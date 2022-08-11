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
        self.register_dpg()

        dpg.create_viewport()
        dpg.setup_dearpygui()
        dpg.show_viewport()

        parser = config_parser()
        args = parser.parse_args()

        if args.inputdir is not None and \
           args.tempdir is not None and \
           args.resultdir is not None:
            print("Load config file successfully!")
            dpg.set_value("it_input_path", args.inputdir)
            dpg.set_value("it_temp_path", args.tempdir)
            dpg.set_value("it_result_path", args.resultdir)

        dpg.start_dearpygui()

    def update_path(self):
        self.u2net.change_image_dir(dpg.get_value("it_input_path"))
        self.u2net.change_temp_dir(dpg.get_value("it_temp_path"))
        self.u2net.change_result_dir(dpg.get_value("it_result_path"))

    def register_dpg(self):
        with dpg.value_registry():
            dpg.add_float_value(default_value=0, tag="sf_processing")
            dpg.add_string_value(default_value="/", tag="it_input_path")
            dpg.add_string_value(default_value="/", tag="it_temp_path")
            dpg.add_string_value(default_value="/", tag="it_result_path")

        dpg.add_file_dialog(directory_selector=True, show=False, width=600, height=300,
                            callback=lambda _, app_data: dpg.set_value("it_input_path", app_data['file_path_name']),
                            tag="img_path_dialog_id")
        dpg.add_file_dialog(directory_selector=True, show=False, width=600, height=300,
                            callback=lambda _, app_data: dpg.set_value("it_temp_path", app_data['file_path_name']),
                            tag="temp_path_dialog_id")
        dpg.add_file_dialog(directory_selector=True, show=False, width=600, height=300,
                            callback=lambda _, app_data: dpg.set_value("it_result_path", app_data['file_path_name']),
                            tag="result_path_dialog_id")

        with dpg.window(label="U2net-Segmentation", width=600):
            with dpg.group(horizontal=True):
                dpg.add_input_text(label="input images path", source="it_input_path")
                dpg.add_button(label="Select", callback=lambda: dpg.show_item("img_path_dialog_id"))

            with dpg.group(horizontal=True):
                dpg.add_input_text(label="temp images path", source="it_temp_path")
                dpg.add_button(label="Select", callback=lambda: dpg.show_item("temp_path_dialog_id"))

            with dpg.group(horizontal=True):
                dpg.add_input_text(label="result images path", source="it_result_path")
                dpg.add_button(label="Select", callback=lambda: dpg.show_item("result_path_dialog_id"))

            def btn_callback():
                self.update_path()
                self.u2net.process(callback=lambda:
                                   dpg.set_value("sf_processing", self.u2net.current_idx/self.u2net.total_images*100))

            with dpg.group(horizontal=True):
                dpg.add_button(label="Process", callback=btn_callback)
                dpg.add_slider_float(source="sf_processing")

    def __del__(self):
        dpg.destroy_context()


if __name__ == '__main__':
    gui = U2netGui()
