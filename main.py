import shutil
import dearpygui.dearpygui as dpg
from U2Net.u2net_wrapper import U2net


def config_parser():
    import configargparse
    parser = configargparse.ArgumentParser()

    parser.add_argument('--config', is_config_file=True,
                        help='config file path')

    parser.add_argument('--inputdir', type=str)
    parser.add_argument("--tempdir", type=str)
    parser.add_argument("--resultdir", type=str)

    return parser


class U2netGui:
    def __init__(self):
        self.u2net = U2net()
        self.u2net.load_model()

        dpg.create_context()

        self.value_register()

        # Load pre-config file
        parser = config_parser()
        args = parser.parse_args()

        if args.inputdir is not None and \
                args.tempdir is not None and \
                args.resultdir is not None:
            print("Load config file successfully!")
            dpg.set_value("it_input_path", args.inputdir)
            dpg.set_value("it_temp_path", args.tempdir)
            dpg.set_value("it_result_path", args.resultdir)
            self.update_path()

        # Register widgets
        self.register_dpg()

        dpg.create_viewport()
        dpg.setup_dearpygui()
        dpg.show_viewport()

        dpg.start_dearpygui()

    def value_register(self):
        with dpg.value_registry():
            dpg.add_float_value(default_value=0, tag="sf_processing")
            dpg.add_string_value(default_value="/", tag="it_input_path")
            dpg.add_string_value(default_value="/", tag="it_temp_path")
            dpg.add_string_value(default_value="/", tag="it_result_path")

    def update_path(self):
        self.u2net.change_image_dir(dpg.get_value("it_input_path"))
        self.u2net.change_temp_dir(dpg.get_value("it_temp_path"))
        self.u2net.change_result_dir(dpg.get_value("it_result_path"))

    def register_dpg(self):
        dpg.add_file_dialog(directory_selector=True, show=False, width=600, height=300,
                            callback=lambda _, app_data: dpg.set_value("it_input_path", app_data['file_path_name']),
                            tag="img_path_dialog_id", default_path=dpg.get_value("it_input_path"))
        dpg.add_file_dialog(directory_selector=True, show=False, width=600, height=300,
                            callback=lambda _, app_data: dpg.set_value("it_temp_path", app_data['file_path_name']),
                            tag="temp_path_dialog_id", default_path=dpg.get_value("it_temp_path"))
        dpg.add_file_dialog(directory_selector=True, show=False, width=600, height=300,
                            callback=lambda _, app_data: dpg.set_value("it_result_path", app_data['file_path_name']),
                            tag="result_path_dialog_id", default_path=dpg.get_value("it_result_path"))

        with dpg.window(label="Template-Generation", width=600):
            with dpg.group(horizontal=True):
                dpg.add_input_text(source="it_input_path", width=350)
                dpg.add_button(label="Select", callback=lambda: dpg.show_item("img_path_dialog_id"))
                dpg.add_text("input images path")

            with dpg.group(horizontal=True):
                dpg.add_input_text(source="it_temp_path", width=350)
                dpg.add_button(label="Select", callback=lambda: dpg.show_item("temp_path_dialog_id"))
                dpg.add_text("temp images path")

            with dpg.group(horizontal=True):
                dpg.add_input_text(source="it_result_path", width=350)
                dpg.add_button(label="Select", callback=lambda: dpg.show_item("result_path_dialog_id"))
                dpg.add_text("result images path")

            def btn_callback():
                self.update_path()
                dpg.set_value("t_success", "")
                self.u2net.process(callback=lambda:
                                   dpg.set_value("sf_processing", self.u2net.current_idx/self.u2net.total_images*100)
                                   )
                dpg.set_value("t_success", "Complete!")
                dpg.set_value("t_clean", "")

            with dpg.group(horizontal=True):
                dpg.add_button(label="Process", callback=btn_callback, width=60)
                dpg.add_slider_float(source="sf_processing", width=282)
                dpg.add_text(tag="t_success")

            def btn_clean():
                if dpg.get_value("cb_input"):
                    shutil.rmtree(dpg.get_value("it_input_path"))
                if dpg.get_value("cb_temp"):
                    shutil.rmtree(dpg.get_value("it_temp_path"))
                if dpg.get_value("cb_result"):
                    shutil.rmtree(dpg.get_value("it_result_path"))
                dpg.set_value("t_clean", "Clean finish!")

            with dpg.group(horizontal=True):
                dpg.add_button(label="Clean", callback=btn_clean, width=60)

                dpg.add_checkbox(label="input", default_value=True, tag="cb_input")
                dpg.add_checkbox(label="temp", default_value=True, tag="cb_temp")
                dpg.add_checkbox(label="result", default_value=True, tag="cb_result")

                dpg.add_text(tag="t_clean", pos=(354, 120))

    def __del__(self):
        dpg.destroy_context()


if __name__ == '__main__':
    gui = U2netGui()
