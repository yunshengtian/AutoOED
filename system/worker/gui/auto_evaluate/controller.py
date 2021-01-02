from .view import AutoEvaluateView


class AutoEvaluateController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = AutoEvaluateView(self.root_view)