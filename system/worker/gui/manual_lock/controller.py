from .view import ManualLockView


class ManualLockController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = ManualLockView(self.root_view)