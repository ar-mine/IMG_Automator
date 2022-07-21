import glob
import os
import sys

import numpy as np
import torch
from PIL import Image
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


def save_output(image_name, pred, d_dir):
    predict = pred
    predict = predict.squeeze()
    predict_np = predict.cpu().data.numpy()

    im = Image.fromarray(predict_np * 255).convert('RGB')
    img_name = image_name.split(os.sep)[-1]
    image = io.imread(image_name)
    imo = im.resize((image.shape[1], image.shape[0]), resample=Image.BILINEAR)

    pb_np = np.array(imo)

    aaa = img_name.split(".")
    bbb = aaa[0:-1]
    imidx = bbb[0]
    for i in range(1, len(bbb)):
        imidx = imidx + "." + bbb[i]

    imo.save(os.path.join(d_dir, imidx+'.png'))


class U2net:
    def __init__(self, default_model: str = 'u2netp'):
        self.model_name = default_model

        self.image_dir = ''
        self.result_dir = ''
        self.model_dir = os.path.join(current_path, 'saved_models', self.model_name, self.model_name + '.pth')

        self.dataloader = None
        self.net = None
        self.img_name_list = []

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

    def change_result_dir(self, result_dir: str):
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
        self.result_dir = result_dir

    def process(self):
        self.load_images()
        for i_test, data_test in enumerate(self.dataloader):

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

                # save results to test_results folder
                if not os.path.exists(self.result_dir):
                    os.makedirs(self.result_dir, exist_ok=True)
                save_output(self.img_name_list[i_test], pred, self.result_dir)

            del d1, d2, d3, d4, d5, d6, d7


if __name__ == '__main__':
    u2net = U2net()
    u2net.load_model()
    u2net.change_image_dir(os.path.join(current_path, 'test_data', 'test_images'))
    u2net.change_result_dir(os.path.join(current_path, 'test_data', 'u2netp_results'))
    u2net.process()
