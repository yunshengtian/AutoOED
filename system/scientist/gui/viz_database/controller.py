import numpy as np
from system.gui.widgets.table import Table
from .view import VizDatabaseView


class VizDatabaseController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        # set values from root
        self.data_agent = self.root_controller.data_agent
        self.worker_agent = self.root_controller.worker_agent

        self.view = VizDatabaseView(self.root_view)

        # load data
        X, Y, is_pareto = self.data_agent.load(['X', 'Y', 'is_pareto'])
        n_init_sample = len(X)

        # initialize database table
        n_var, n_obj = X.shape[1], Y.shape[1]
        titles = ['status'] + [f'x{i + 1}' for i in range(n_var)] + \
            [f'f{i + 1}' for i in range(n_obj)] + \
            [f'f{i + 1}_expected' for i in range(n_obj)] + \
            [f'f{i + 1}_uncertainty' for i in range(n_obj)] + \
            ['pareto', 'config_id', 'batch_id']
        key_map = {
            'X': [f'x{i + 1}' for i in range(n_var)],
            'Y': [f'f{i + 1}' for i in range(n_obj)],
            'Y_expected': [f'f{i + 1}_expected' for i in range(n_obj)],
            'Y_uncertainty': [f'f{i + 1}_uncertainty' for i in range(n_obj)],
        }

        self.table = Table(master=self.view.frame, titles=titles)
        self.table.register_key_map(key_map)
        self.table.insert({
            'status': ['evaluated'] * n_init_sample,
            'X': X, 
            'Y': Y, 
            'Y_expected': np.full_like(Y, 'N/A', dtype=object),
            'Y_uncertainty': np.full_like(Y, 'N/A', dtype=object),
            'pareto': is_pareto, 
            'config_id': np.zeros(n_init_sample, dtype=int), 
            'batch_id': np.zeros(n_init_sample, dtype=int)
        })

    def update_data(self, opt_done, eval_done):
        '''
        Update table data when optimization or evaluation is done
        '''
        if not opt_done and not eval_done:
            return

        # load data
        X, Y, Y_expected, Y_uncertainty, is_pareto, config_id, batch_id = \
            self.data_agent.load(['X', 'Y', 'Y_expected', 'Y_uncertainty', 'is_pareto', 'config_id', 'batch_id'], valid_only=False)

        # update optimization results
        if opt_done:
            n_prev_sample = self.table.n_rows
            insert_len = len(Y_expected[n_prev_sample:])
            self.table.insert({
                # confirmed value
                'X': X[n_prev_sample:], 
                'Y_expected': Y_expected[n_prev_sample:],
                'Y_uncertainty': Y_uncertainty[n_prev_sample:],
                'config_id': config_id[n_prev_sample:], 
                'batch_id': batch_id[n_prev_sample:],
                # unconfirmed value
                'status': ['unevaluated'] * insert_len,
                'Y': np.ones_like(Y_expected[n_prev_sample:]) * np.nan,
                'pareto': [False] * insert_len,
            })

        # update evaluation results
        if eval_done:
            valid_idx = np.where(~np.isnan(Y).any(axis=1))
            self.table.update({
                'Y': Y[valid_idx], 
                'pareto': is_pareto[valid_idx],
            })

    def update_status(self, status, rowids):
        '''
        Update status of evaluation
        '''
        self.table.update({'status': status}, rowids)
