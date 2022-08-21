import os
import glob
import cv2
import shutil
from sys import platform
from skimage.io import imsave
import omegaconf
from omegaconf import DictConfig
from typing import Optional
import dearpygui.dearpygui as dpg
from U2Net.u2net_wrapper import U2net

# Names of Folders that will be used in the project
PathEnum = ("video", "input", "temp", "result")


class U2netGui:
    def __init__(self, cfg: DictConfig):
        self.cfg = cfg

        # Load U2Net model for segmentation
        self.u2net = U2net()
        self.u2net.load_model()

        dpg.create_context()

        # Pre value setting
        self.value_register()

        # Register widgets
        self.register_dpg()

        # Gui pre-init
        dpg.create_viewport()
        dpg.setup_dearpygui()
        dpg.show_viewport()

        # Gui start
        dpg.start_dearpygui()

    def value_register(self):
        with dpg.value_registry():
            # Value that represents processing rate
            dpg.add_float_value(default_value=0, tag="processing_rate")
            dpg.add_int_value(default_value=15, tag="separate_rate")

            # Value that saves path
            for key in PathEnum:
                dpg.add_string_value(default_value="", tag="{}_path".format(key))

        # Load parameters into the gui binding values
        print("Loading config file...")
        for key in PathEnum:
            try:
                dpg.set_value("{}_path".format(key), self.cfg["path"][key])
            except omegaconf.errors.ConfigKeyError:
                print("Not load {} path from config file.".format(key))
        print("Finish!")

    def register_dpg(self):
        # Register file dialog
        for key in PathEnum:
            dpg.add_file_dialog(directory_selector=True, show=False, width=600, height=300,
                                callback=lambda _, app_data: dpg.set_value("{}_path".format(key),
                                                                           app_data['file_path_name']),
                                tag="{}_path_dialog_id".format(key), default_path=dpg.get_value("{}_path".format(key)))

        # Register widgets in window
        with dpg.window(label="Template-Generation", width=600):
            def separate_callback():
                dpg.set_value("separate_success", "Separating")

                # Start to process images
                video2image(dpg.get_value("video_path"), dpg.get_value("input_path"),
                            interval=dpg.get_value("separate_rate"))
                dpg.set_value("separate_success", "Complete!")

            def open_creator(path):
                def creator_win():
                    os.system("explorer {}".format(path))

                def creator_linux():
                    os.system("xdg-open {}".format(path))

                if platform == "linux" or platform == "linux2":
                    return creator_linux
                elif platform == "darwin":
                    pass
                elif platform == "win32":
                    return creator_win

            for key in PathEnum:
                with dpg.group(horizontal=True):
                    dpg.add_input_text(source="{}_path".format(key), width=350)
                    dpg.add_button(label="Select", callback=lambda: dpg.show_item("{}_path_dialog_id".format(key)))
                    open_temp = open_creator(dpg.get_value("{}_path".format(key)))
                    dpg.add_button(label="Open", callback=open_temp)
                    dpg.add_text("{} folder".format(key))
                if key == "video":
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Separate", callback=separate_callback, width=60)
                        dpg.add_slider_int(source="separate_rate", min_value=1, max_value=30, width=282)
                        dpg.add_text(tag="separate_success")

            def process_callback():
                dpg.set_value("process_success", "")

                # Write paths saved in GUI to U2Net model class
                self.u2net.change_image_dir(dpg.get_value("input_path"))
                self.u2net.change_temp_dir(dpg.get_value("temp_path"))
                self.u2net.change_result_dir(dpg.get_value("result_path"))

                # Start to process images
                self.u2net.process(callback=lambda:
                dpg.set_value("processing_rate",
                              self.u2net.current_idx / self.u2net.total_images * 100)
                                   )
                dpg.set_value("process_success", "Complete!")

            with dpg.group(horizontal=True):
                dpg.add_button(label="Process", callback=process_callback, width=60)
                dpg.add_slider_float(source="processing_rate", width=282)
                dpg.add_text(tag="process_success")

            def btn_clean():
                # Only clean folders that keep checkbox
                for _key in PathEnum:
                    if dpg.get_value("cb_{}".format(_key)):
                        path_temp = dpg.get_value("{}_path".format(_key))
                        if os.path.exists(path_temp):
                            shutil.rmtree(path_temp)
                            os.mkdir(path_temp)
                        else:
                            print("{} path does not exist!")
                dpg.set_value("t_clean", "Clean finish!")

            with dpg.group(horizontal=True):
                dpg.add_button(label="Clean", callback=btn_clean, width=60)

                # Add checkboxes for cleaning
                for key in PathEnum:
                    dpg.add_checkbox(label=key, default_value=True, tag="cb_{}".format(key))

                # dpg.add_text(tag="t_clean",
                #              pos=(dpg.get_item_pos("separate_success")[0], dpg.get_item_pos("cb_input")[1]))
                dpg.add_text(tag="t_clean", pos=(366, 165))

    def __del__(self):
        dpg.destroy_context()


def video2image(input_dir, output_dir, interval=30, image_size: Optional[int] = None, transpose=False):
    video_name_list = glob.glob(input_dir + os.sep + '*.mp4')
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
