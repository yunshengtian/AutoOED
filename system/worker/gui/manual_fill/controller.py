from .view import ManualFillView


class ManualFillController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = ManualFillView(self.root_view)