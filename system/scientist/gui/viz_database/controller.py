import numpy as np
from system.gui.widgets.newtable import Table
from .view import VizDatabaseView


class VizDatabaseController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        # set values from root
        self.data_agent = self.root_controller.data_agent
        self.worker_agent = self.root_controller.worker_agent

        self.view = VizDatabaseView(self.root_view)

        # initialize database table
        n_var, n_obj = self.data_agent.n_var, self.data_agent.n_obj
        self.columns = ['status'] + [f'x{i + 1}' for i in range(n_var)] + \
            [f'f{i + 1}' for i in range(n_obj)] + \
            [f'f{i + 1}_expected' for i in range(n_obj)] + \
            [f'f{i + 1}_uncertainty' for i in range(n_obj)] + \
            ['pareto', 'config_id', 'batch_id']
        self.n_var = n_var
        self.n_obj = n_obj

        self.table = Table(master=self.view.frame, columns=self.columns)
        data_str = self.data_agent.load_str(keys=['status', 'X', 'Y', 'Y_expected', 'Y_uncertainty', 'is_pareto', 'config_id', 'batch_id'])
        self.table.insert(columns=None, data=data_str)

    def update_data(self, opt_done, eval_done):
        '''
        Update table data when 1) status changes, 2) optimization is None, 3) evaluation is done
        '''
        # only status changes
        if not opt_done and not eval_done:
            status_str = self.data_agent.load_str(keys='status')
            self.table.update(columns=['status'], data=status_str)
            return

        data_str = self.data_agent.load_str(keys=['status', 'X', 'Y', 'Y_expected', 'Y_uncertainty', 'is_pareto', 'config_id', 'batch_id'])

        # update optimization results
        if opt_done:
            n_prev_sample = self.table.n_rows
            self.table.insert(columns=self.columns, data=data_str[n_prev_sample:])

        # update evaluation results and status
        if eval_done:
            Y_str = data_str[:, 1 + self.n_var:1 + self.n_var + self.n_obj]
            pareto_str = data_str[:, -3]
            status_str = data_str[:, 0]
            self.table.update(columns=self.data_agent._map_key('Y') + ['pareto', 'status'], data=[Y_str, pareto_str, status_str], transform=True)
