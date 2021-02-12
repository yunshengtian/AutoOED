import numpy as np
from .view import VizDatabaseView


class VizDatabaseController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        # set values from root
        self.database = self.root_controller.database
        self.table_name = self.root_controller.table_name

        # initialize database table
        problem_cfg = self.root_controller.problem_cfg
        n_var, n_obj = problem_cfg['n_var'], problem_cfg['n_obj']
        self.columns = ['status'] + [f'x{i + 1}' for i in range(n_var)] + \
            [f'f{i + 1}' for i in range(n_obj)] + \
            [f'f{i + 1}_expected' for i in range(n_obj)] + \
            [f'f{i + 1}_uncertainty' for i in range(n_obj)] + \
            ['pareto', 'batch']

        self.view = VizDatabaseView(self.root_view, columns=self.columns)
        self.table = self.view.widget['table']

        data = self.database.load_table(name=self.table_name, column=self.columns)
        self.table.load(data)

    def update_data(self):
        '''
        Update table data
        '''
        data = self.database.load_table(name=self.table_name)
        self.table.load(data)
