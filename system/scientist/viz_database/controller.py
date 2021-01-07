import numpy as np
from system.gui.widgets.newtable import Table
from .view import VizDatabaseView


class VizDatabaseController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        # set values from root
        self.database = self.root_controller.database
        self.table_name = self.root_controller.table_name

        self.view = VizDatabaseView(self.root_view)

        # initialize database table
        problem_cfg = self.root_controller.problem_cfg
        n_var, n_obj = problem_cfg['n_var'], problem_cfg['n_obj']
        self.columns = ['status'] + [f'x{i + 1}' for i in range(n_var)] + \
            [f'f{i + 1}' for i in range(n_obj)] + \
            [f'f{i + 1}_expected' for i in range(n_obj)] + \
            [f'f{i + 1}_uncertainty' for i in range(n_obj)] + \
            ['pareto', 'config_id', 'batch_id']
        self.n_var = n_var
        self.n_obj = n_obj

        self.table = Table(master=self.view.frame, columns=self.columns)
        data = self.database.load_table(name=self.table_name)
        data = np.array(data, dtype=str)[:, 1:]
        self.table.insert(columns=None, data=data)

    def update_data(self):
        '''
        Update table data
        '''
        data = self.database.load_table(name=self.table_name)
        data = np.array(data, dtype=str)[:, 1:]
        self.table.update(columns=None, data=data)