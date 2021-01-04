from .view import SelectionView


class SelectionController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = SelectionView(self.root_view)
