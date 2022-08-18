import os
import shutil
import omegaconf
from omegaconf import DictConfig

import dearpygui.dearpygui as dpg
from U2Net.u2net_wrapper import U2net

PathEnum = ("input", "temp", "result", "video")


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

    def register_dpg(self):
        # Register file dialog
        for key in PathEnum:
            dpg.add_file_dialog(directory_selector=True, show=False, width=600, height=300,
                                callback=lambda _, app_data: dpg.set_value("{}_path".format(key),
                                                                           app_data['file_path_name']),
                                tag="{}_path_dialog_id".format(key), default_path=dpg.get_value("{}_path".format(key)))

        with dpg.window(label="Template-Generation", width=600):
            for key in PathEnum:
                with dpg.group(horizontal=True):
                    dpg.add_input_text(source="{}_path".format(key), width=350)
                    dpg.add_button(label="Select", callback=lambda: dpg.show_item("{}_path_dialog_id".format(key)))
                    dpg.add_text("{} folder".format(key))

            def btn_callback():
                dpg.set_value("t_success", "")

                # Write paths saved in GUI to U2Net model class
                self.u2net.change_image_dir(dpg.get_value("input_path"))
                self.u2net.change_temp_dir(dpg.get_value("temp_path"))
                self.u2net.change_result_dir(dpg.get_value("result_path"))

                # Start to process images
                self.u2net.process(callback=lambda:
                dpg.set_value("sf_processing",
                              self.u2net.current_idx / self.u2net.total_images * 100)
                                   )
                dpg.set_value("t_success", "Complete!")

            with dpg.group(horizontal=True):
                dpg.add_button(label="Process", callback=btn_callback, width=60)
                dpg.add_slider_float(source="sf_processing", width=282)
                dpg.add_text(tag="t_success")

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

                dpg.add_text(tag="t_clean", pos=(354, 120))

    def __del__(self):
        dpg.destroy_context()
