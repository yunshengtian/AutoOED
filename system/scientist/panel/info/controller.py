from .view import PanelInfoView


class PanelInfoController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = PanelInfoView(self.root_view)

    def set_info(self, problem_cfg):
        self.view.widget['problem_info'].set_info(problem_cfg)

    def update_info(self, problem_cfg):
        self.view.widget['problem_info'].update_info(problem_cfg)

    def clear_info(self):
        self.view.widget['problem_info'].clear_info()