import dearpygui.dearpygui as dpg
from U2Net.u2net_wrapper import U2net


class U2netGui:
    def __init__(self):
        self.u2net = U2net()
        self.u2net.load_model()

        dpg.create_context()
        self.register_dpg()

        dpg.start_dearpygui()

    def register_dpg(self):
        dpg.add_file_dialog(directory_selector=True, show=False, width=600, height=300,
                            callback=lambda _, app_data: self.u2net.change_image_dir(app_data['file_path_name']),
                            tag="img_path_dialog_id")
        dpg.add_file_dialog(directory_selector=True, show=False, width=600, height=300,
                            callback=lambda _, app_data: self.u2net.change_result_dir(app_data['file_path_name']),
                            tag="result_path_dialog_id")

        with dpg.window(label="U2net-Segmentation"):
            with dpg.group(horizontal=True):
                dpg.add_text("Source path:")
                dpg.add_button(label="Select", callback=lambda: dpg.show_item("img_path_dialog_id"))
            with dpg.group(horizontal=True):
                dpg.add_text("Result path:")
                dpg.add_button(label="Select", callback=lambda: dpg.show_item("result_path_dialog_id"))
            dpg.add_button(label="Process", callback=lambda: self.u2net.process())

        dpg.create_viewport()
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def __del__(self):
        dpg.destroy_context()


if __name__ == '__main__':
    gui = U2netGui()
