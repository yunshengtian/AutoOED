from .view import MenuEvalView

from .start_local_eval import StartLocalEvalController
from .stop_eval import StopEvalController


class MenuEvalController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = MenuEvalView(self.root_view)

    def get_table(self):
        '''
        Get table of database
        '''
        return self.root_controller.controller['viz_database'].table

    def start_local_eval(self):
        '''
        Manually start local evaluation workers for certain rows (TODO: disable when no eval script linked)
        '''
        StartLocalEvalController(self)

    def start_remove_eval(self):
        '''
        TODO
        '''
        pass

    def stop_eval(self):
        '''
        Manually stop evaluation workers for certain rows (TODO: disable when no eval script linked)
        '''
        StopEvalController(self)