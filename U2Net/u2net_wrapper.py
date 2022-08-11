import glob
import os
import sys

import numpy as np
import torch
from PIL import Image, ImageFilter
from skimage import io
from torch.autograd import Variable
from torch.utils.data import DataLoader
from torchvision import transforms  # , utils

current_path = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(current_path)

from data_loader import RescaleT
from data_loader import ToTensorLab
from data_loader import SalObjDataset

from model import U2NET  # full size version 173.6 MB
from model import U2NETP  # small version u2net 4.7 MB


# normalize the predicted SOD probability map
def normPRED(d):
    ma = torch.max(d)
    mi = torch.min(d)

    dn = (d - mi) / (ma - mi)

    return dn


def save_output_overlay(image_name, mask, d_dir, o_dir):
    # Convert predicted segmentation mask to numpy array
    mask_ = mask
    mask_ = mask_.squeeze()
    mask_np = mask_.cpu().data.numpy()

    # Segment the image with mask while using black bg(0, 0, 0)
    image_np = io.imread(image_name)
    image_ = Image.fromarray(image_np).convert('RGB')
    background = Image.fromarray(np.zeros((image_np.shape[0], image_np.shape[1]))).convert('RGB')
    img = Image.fromarray(mask_np * 255).convert('L')
    img_mask = img.resize((image_np.shape[1], image_np.shape[0]), resample=Image.Resampling.BILINEAR).\
        convert('1').filter(ImageFilter.MedianFilter(5))
    img_composite = Image.composite(image_, background, img_mask)

    # Remove path prefix
    image_name = image_name.split(os.sep)[-1]
    # left, top, right, bottom
    box = img_mask.getbbox()
    box_center = [(box[0]+box[2])//2, (box[1]+box[3])//2]
    gap = max(image_np.shape)*0.02
    edge_size = (max(box[2]-box[0], box[3]-box[1])+gap)//2
    box_tuned = [box_center[0]-edge_size, box_center[1]-edge_size, box_center[0]+edge_size, box_center[1]+edge_size]
    img_cropped = img_composite.transform((128, 128), Image.Transform.EXTENT, box_tuned, Image.Resampling.BILINEAR)
    mask_cropped = img_mask.transform((128, 128), Image.Transform.EXTENT, box_tuned, Image.Resampling.BILINEAR)

    aaa = image_name.split(".")
    bbb = aaa[0:-1]
    imidx = bbb[0]
    for i in range(1, len(bbb)):
        imidx = imidx + "." + bbb[i]

    img_composite.save(os.path.join(d_dir, imidx + '.png'))
    img_cropped.save(os.path.join(o_dir, imidx + '_a.png'))
    mask_cropped.save(os.path.join(o_dir, imidx + '_m.png'))


def save_output(image_name, pred, d_dir, threshold=128):
    predict = pred
    predict = predict.squeeze()
    predict_np = predict.cpu().data.numpy()

    im = Image.fromarray(predict_np * 255).convert('RGB')
    img_name = image_name.split(os.sep)[-1]
    image = io.imread(image_name)
    imo = im.resize((image.shape[1], image.shape[0]), resample=Image.BILINEAR)

    mask = np.array(imo)
    img_rgb = np.zeros(mask.shape, dtype=np.uint8)
    img_rgb[mask > threshold] = image[mask > threshold]
    img_rgb = Image.fromarray(img_rgb, mode='RGB')

    aaa = img_name.split(".")
    bbb = aaa[0:-1]
    imidx = bbb[0]
    for i in range(1, len(bbb)):
        imidx = imidx + "." + bbb[i]

    if not os.path.exists(os.path.join(d_dir, 'mask')):
        os.mkdir(os.path.join(d_dir, 'mask'))
    if not os.path.exists(os.path.join(d_dir, 'rgb')):
        os.mkdir(os.path.join(d_dir, 'rgb'))
    imo.save(os.path.join(d_dir, 'mask', imidx+'.png'))
    img_rgb.save(os.path.join(d_dir, 'rgb', imidx+'.png'))


class U2net:
    def __init__(self, default_model: str = 'u2netp'):
        self.model_name = default_model

        self.image_dir = ''
        self.temp_dir = ''
        self.result_dir = ''
        self.model_dir = os.path.join(current_path, 'saved_models', self.model_name, self.model_name + '.pth')

        self.dataloader = None
        self.net = None
        self.img_name_list = []

        self.total_images = -1
        self.current_idx = -1

    def load_model(self):
        if self.model_name == 'u2net':
            print("...load U2NET---173.6 MB")
            self.net = U2NET(3, 1)
        elif self.model_name == 'u2netp':
            print("...load U2NEP---4.7 MB")
            self.net = U2NETP(3, 1)
        if torch.cuda.is_available():
            self.net.load_state_dict(torch.load(self.model_dir))
            self.net.cuda()
        else:
            self.net.load_state_dict(torch.load(self.model_dir, map_location='cpu'))
        self.net.eval()

    def load_images(self):
        self.img_name_list = glob.glob(self.image_dir + os.sep + '*')
        print(self.img_name_list)
        self.total_images = len(self.img_name_list)
        self.current_idx = 0

        dataset = SalObjDataset(img_name_list=self.img_name_list,
                                lbl_name_list=[],
                                transform=transforms.Compose([RescaleT(320),
                                                              ToTensorLab(flag=0)])
                                )
        self.dataloader = DataLoader(dataset,
                                     batch_size=1,
                                     shuffle=False,
                                     num_workers=1)

    def change_image_dir(self, image_dir: str):
        self.image_dir = image_dir

    def change_temp_dir(self, temp_dir: str):
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        self.temp_dir = temp_dir

    def change_result_dir(self, result_dir: str):
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
        self.result_dir = result_dir

    def process(self, callback=None):
        self.load_images()
        for i_test, data_test in enumerate(self.dataloader):
            self.current_idx = i_test
            print("inferencing:", self.img_name_list[i_test].split(os.sep)[-1])

            inputs_test = data_test['image']
            inputs_test = inputs_test.type(torch.FloatTensor)

            if torch.cuda.is_available():
                inputs_test = Variable(inputs_test.cuda())
            else:
                inputs_test = Variable(inputs_test)

            with torch.no_grad():
                d1, d2, d3, d4, d5, d6, d7 = self.net(inputs_test)

                # normalization
                pred = d1[:, 0, :, :]
                pred = normPRED(pred)

                # save_output(self.img_name_list[i_test], pred, self.result_dir)
                save_output_overlay(self.img_name_list[i_test], pred, self.temp_dir, self.result_dir)

            del d1, d2, d3, d4, d5, d6, d7

            if callback is not None:
                callback()

        self.current_idx = self.total_images

        if callback is not None:
            callback()


if __name__ == '__main__':
    u2net = U2net()
    u2net.load_model()
    u2net.change_image_dir(os.path.join(current_path, 'test_data', 'test_images'))
    u2net.change_temp_dir(os.path.join(current_path, 'test_data', 'temp_images'))
    u2net.change_result_dir(os.path.join(current_path, 'test_data', 'u2netp_results'))
    u2net.process()
