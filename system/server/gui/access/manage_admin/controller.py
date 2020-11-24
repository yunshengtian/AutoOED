from .view import ManageAdminView


class ManageAdminController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = ManageAdminView(self.root_view)