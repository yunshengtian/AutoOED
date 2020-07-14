import os
import numpy as np
import yaml
from pymoo.performance_indicator.hv import Hypervolume
from system.utils import check_pareto, calc_pred_error


class Agent:
    '''
    Agent controlling data preprocessing before making changes to database
    '''
    def __init__(self, database, problem):
        self.db = database
        self.n_var = problem.n_var
        self.n_obj = problem.n_obj
        self.hv = Hypervolume(ref_point=problem.ref_point) # hypervolume calculator
        self.n_init_sample = None

        # keys and associated datatypes of database table
        key_list = [f'x{i + 1} real' for i in range(self.n_var)] + \
            [f'f{i + 1} real' for i in range(self.n_obj)] + \
            [f'expected_f{i + 1} real' for i in range(self.n_obj)] + \
            [f'uncertainty_f{i + 1} real' for i in range(self.n_obj)] + \
            ['hv real', 'pred_error real', 'is_pareto boolean', 'config_id integer']
        self.db.create('data', key=key_list)

        # high level key mapping (e.g., X -> [x1, x2, ...])
        self.key_map = {
            'X': [f'x{i + 1}' for i in range(self.n_var)],
            'Y': [f'f{i + 1}' for i in range(self.n_obj)],
            'Y_expected': [f'expected_f{i + 1}' for i in range(self.n_obj)],
            'Y_uncertainty': [f'uncertainty_f{i + 1}' for i in range(self.n_obj)],
            'hv': 'hv',
            'pred_error': 'pred_error',
            'is_pareto': 'is_pareto',
            'config_id': 'config_id'
        }

        # datatype mapping in python
        self.type_map = {
            'X': float,
            'Y': float,
            'Y_expected': float,
            'Y_uncertainty': float,
            'hv': float,
            'pred_error': float,
            'is_pareto': bool,
            'config_id': int,
        }

    def init(self, X, Y):
        '''
        Initialize database table with initial data X, Y
        '''
        self.n_init_sample = X.shape[0]
        Y_expected = np.zeros((self.n_init_sample, self.n_obj))
        Y_uncertainty = np.zeros((self.n_init_sample, self.n_obj))

        hv_value = np.full(self.n_init_sample, self.hv.calc(Y))
        pred_error = np.ones(self.n_init_sample) * 100
        is_pareto = check_pareto(Y)
        config_id = np.zeros(self.n_init_sample, dtype=int)

        self.db.insert('data', key=None, data=[X, Y, Y_expected, Y_uncertainty, hv_value, pred_error, is_pareto, config_id])

    def select(self, keys):
        '''
        Select array from database table
        '''
        return self.db.select('data', key=[self.key_map[key] for key in keys], dtype=[self.type_map[key] for key in keys])

    def insert(self, dataframe, config_id):
        '''
        Insert array to database table
        Input:
            dataframe: result dataframe from optimization and evaluation, keys: X, Y, Y_expected, Y_uncertainty
            config_id: current configuration index (user can sequentially reload different config files)
        '''
        X = dataframe[self.key_map['X']].to_numpy()
        Y = dataframe[self.key_map['Y']].to_numpy()
        Y_expected = dataframe[self.key_map['Y_expected']].to_numpy()
        Y_uncertainty = dataframe[self.key_map['Y_uncertainty']].to_numpy()

        with self.db.get_lock():
            old_Y, old_Y_expected = self.select(['Y', 'Y_expected'])
            all_Y, all_Y_expected = np.vstack([old_Y, Y]), np.vstack([old_Y_expected, Y_expected])

            # compute associated values from dataframe (hv, pred_error, is_pareto)
            sample_len = X.shape[0]
            hv_value = np.full(sample_len, self.hv.calc(all_Y))
            pred_error = calc_pred_error(all_Y[self.n_init_sample:], all_Y_expected[self.n_init_sample:])
            pred_error = np.full(sample_len, pred_error)
            is_pareto = check_pareto(all_Y)
            pareto_id = np.where(is_pareto)[0] + 1
            config_id = np.full(sample_len, config_id)
            
            self.db.insert('data', key=None, data=[X, Y, Y_expected, Y_uncertainty, hv_value, pred_error, np.zeros(sample_len, dtype=bool), config_id])
            self.db.update('data', key='is_pareto', data=False, rowid=None)
            self.db.update('data', key='is_pareto', data=True, rowid=pareto_id)

    def quit(self):
        '''
        Quit database
        '''
        self.db.quit()
