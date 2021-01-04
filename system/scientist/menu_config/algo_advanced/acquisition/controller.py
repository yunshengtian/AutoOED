from .view import AcquisitionView


class AcquisitionController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = AcquisitionView(self.root_view)