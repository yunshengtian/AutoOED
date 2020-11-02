from .view import SurrogateView


class SurrogateController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = SurrogateView(self.root_view)

        self.view.widget['name'].widget.bind('<<ComboboxSelected>>', self.select_surrogate)

    def select_surrogate(self, event):
        '''
        Select surrogate model type
        '''
        name = event.widget.get()
        self.view.select(name)