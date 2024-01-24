import os
import glob
from typing import Optional
import cv2
from skimage.io import imsave


def video2image(input_dir, output_dir, interval=30, image_size: Optional[int] = None, transpose=False):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    video_name_list = glob.glob(input_dir + os.sep + '*')
    # video_name_list = glob.glob(input_dir + os.sep + '*.mp4')
    count = 0
    for input_video in video_name_list:
        print(f'split video {input_video} into images ...')
        video_cap = cv2.VideoCapture(input_video)
        success, image = video_cap.read()
        while success:
            if count % interval == 0:
                # If images need to be scaled
                if image_size is not None:
                    h, w = image.shape[:2]
                    ratio = image_size / max(h, w)
                    ht, wt = int(ratio * h), int(ratio * w)
                    image = cv2.resize(image, (wt, ht), interpolation=cv2.INTER_LINEAR)

                # If images need to be transposed
                if transpose:
                    v0 = cv2.getVersionMajor()
                    v1 = cv2.getVersionMinor()
                    if v0 >= 4 and v1 >= 5:
                        image = cv2.flip(image, 0)
                        image = cv2.flip(image, 1)
                    else:
                        image = cv2.transpose(image)
                        image = cv2.flip(image, 1)

                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                imsave(f"{output_dir}/frame%d.jpg" % count, image)  # save frame as JPEG file
            success, image = video_cap.read()
            count += 1
    return count