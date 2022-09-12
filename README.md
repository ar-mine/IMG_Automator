# IMG_Automator
A GUI wrapper created by [DearPyGui](https://github.com/hoffstadt/DearPyGui) 
for pre-processing images to generate templates that are used as dataset.

## Functions
+ Use [FFmpeg](https://github.com/FFmpeg/FFmpeg) to separate videos to images for further processing.
+ Use [U^2-Net](https://github.com/xuebinqin/U-2-Net) to make YCB like dataset. 

## Installation
The source codes have been tested with `python3.8`, 
and the packages needed are written into the `requirements.txt`.

You can just use `git clone https://github.com/ar-mine/IMG_Automator.git` to download the whole repo.

## Usage
+ Modify the `main.py` to specify use `config-win.yaml` or `config.yaml` and then run `main.py`. 
  + It will load pre-trained `U^2-Net` model and then load config file if it exists.
  + Put your video that contains target objects in the path of `video folder` and then click `separate` button,
    then the video will be separated into sequence images according to the rate of slider. 
  + Or you can just put all images in `input folder` and click `process` button, 
    then it will generate images only contain target and save them in `temp folder`.
  + Finally, YCB-like images dataset will be saved in `result folder` with resolution of 120*120.
  + You can use `open` to see the images in the folder and use `clean` and related checkbox to clean redundant images or videos
    (the action will eraser the whole folder specified except the folder itself).
+ The `config-win.yaml` and `config.yaml` store the default processing paths based on different formats of Windows and Linux. 
  You can change it according to your project or modify the path while running the program.

## Resource
Test video link: https://drive.google.com/file/d/17pofu-ii4KtUTX7YxbwOes9vlHXXils3/view?usp=sharing.
By default, you can put the video in the `IMG_Automator\dataset\video` folder.