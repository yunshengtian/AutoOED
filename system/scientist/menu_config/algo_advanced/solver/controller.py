from .view import SolverView


class SolverController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = SolverView(self.root_view)
