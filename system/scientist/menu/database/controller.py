from .view import MenuVizDatabaseView

from .enter_design import EnterDesignController
from .enter_performance import EnterPerformanceController


class MenuDatabaseController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.data_agent, self.worker_agent = self.root_controller.data_agent, self.root_controller.worker_agent

        self.view = MenuVizDatabaseView(self.root_view)

    def get_table(self):
        '''
        Get table of database
        '''
        return self.root_controller.controller['viz_database'].table

    def get_config(self):
        return self.root_controller.get_config()

    def get_problem_cfg(self):
        return self.root_controller.get_problem_cfg()

    def export_csv(self):
        '''
        Export database to csv file
        '''
        table = self.get_table()
        table.export_csv()

    def enter_design(self):
        '''
        Enter design variables
        '''
        EnterDesignController(self)

    def enter_performance(self):
        '''
        Enter performance values at certain rows
        '''
        EnterPerformanceController(self)