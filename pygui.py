import os
import shutil
import omegaconf
from omegaconf import DictConfig
import dearpygui.dearpygui as dpg
from sys import platform

from utils import video2image
from U2Net.u2net_wrapper import U2net

# Names of Folders that will be used in the project
PathEnum = ("video", "input", "temp", "result")


class U2netGui:
    def __init__(self, cfg: DictConfig):
        self.cfg = cfg

        # Load U2Net model for segmentation
        self.u2net = U2net()
        self.u2net.load_model()

        if cfg["headless"]:
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

        else:
            # Write paths saved in GUI to U2Net model class
            self.u2net.change_image_dir(dpg.get_value(cfg["path"]["input"]))
            self.u2net.change_temp_dir(dpg.get_value(cfg["path"]["temp"]))
            self.u2net.change_result_dir(dpg.get_value(cfg["path"]["result"]))

            self.u2net.process()

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
        def set_value_creator(key_):
            path_id = "{}_path".format(key_)
            return lambda _, app_data: dpg.set_value(path_id, app_data['file_path_name'])

        # Register file path dialog
        for key in PathEnum:
            dpg.add_file_dialog(directory_selector=True, show=False, width=600, height=300,
                                callback=set_value_creator(key),
                                tag="{}_path_dialog_id".format(key))

        # Register widgets in window
        with dpg.window(label="Template-Generation", width=600):
            # For button 'Select'
            def dialog_creator(key_):
                """
                Return a dialog callback
                """
                dialog_tag_ = "{}_path_dialog_id".format(key_)
                return lambda: dpg.show_item(dialog_tag_)

            # For button 'Open'
            def open_creator(key_):
                """
                Given dpg context and the prefix of path, it will generate a function according to OS
                as a callback for button to bind with.
                """
                path_id = "{}_path".format(key_)

                def func():
                    path = dpg.get_value(path_id)

                    if platform == "linux" or platform == "linux2":
                        os.system("xdg-open \"{}\"".format(path))
                    elif platform == "darwin":
                        pass
                    elif platform == "win32":
                        os.system("explorer {}".format(path))

                return func

            for key in PathEnum:
                with dpg.group(horizontal=True):
                    dpg.add_input_text(source="{}_path".format(key), width=350, readonly=True)
                    dpg.add_button(label="Select", callback=dialog_creator(key))
                    dpg.add_button(label="Open", callback=open_creator(key))
                    dpg.add_text("{} folder".format(key))
                # Video folder's special option
                if key == "video":
                    # For button 'Separate'
                    def separate_callback():
                        dpg.set_value("separate_success", "Separating")

                        # Start to process images
                        video2image(dpg.get_value("video_path"), dpg.get_value("input_path"),
                                    interval=dpg.get_value("separate_rate"))
                        dpg.set_value("separate_success", "Complete!")

                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Separate", callback=separate_callback, width=60)
                        dpg.add_slider_int(source="separate_rate", min_value=1, max_value=30, width=282)
                        dpg.add_text(tag="separate_success")

            with dpg.group(horizontal=True):
                # For button 'Process'
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

                dpg.add_button(label="Process", callback=process_callback, width=60)
                dpg.add_slider_float(source="processing_rate", width=282)
                dpg.add_text(tag="process_success")

            with dpg.group(horizontal=True):
                # For button 'clean'
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

                dpg.add_button(label="Clean", callback=btn_clean, width=60)

                # Add checkboxes for cleaning
                for key in PathEnum:
                    dpg.add_checkbox(label=key, default_value=True, tag="cb_{}".format(key))

                # dpg.add_text(tag="t_clean",
                #              pos=(dpg.get_item_pos("separate_success")[0], dpg.get_item_pos("cb_input")[1]))
                dpg.add_text(tag="t_clean", pos=(366, 165))

    def __del__(self):
        dpg.destroy_context()



