import numpy as np
from .view import VizDatabaseView
from .enter_design import EnterDesignController
from .enter_performance import EnterPerformanceController


class VizDatabaseController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        # set values from root
        self.database = self.root_controller.database
        self.table_name = self.root_controller.table_name
        self.agent, self.scheduler = self.root_controller.agent, self.root_controller.scheduler

        columns = self.database.get_column_names(self.table_name)
        columns = [col for col in columns if not col.startswith('_')]
        self.view = VizDatabaseView(self.root_view, columns=columns)
        self.table = self.view.widget['table']

        self.view.widget['enter_design'].configure(command=self.enter_design)
        self.view.widget['enter_performance'].configure(command=self.enter_performance)

        self.update_data()

    def update_data(self):
        '''
        Update table data
        '''
        data = self.database.load_table(name=self.table_name, column=self.view.get_table_columns())
        self.table.load(data)

    def get_config(self):
        return self.root_controller.get_config()

    def get_problem_cfg(self):
        return self.root_controller.get_problem_cfg()

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