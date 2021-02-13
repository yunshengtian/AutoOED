import os
import numpy as np
from multiprocessing import Value

from system.utils.core import optimize, predict, evaluate
from system.utils.performance import check_pareto


class DataAgent:
    '''
    Agent controlling data communication from & to database
    '''
    def __init__(self, database, table_name):
        self.db = database
        self.table_name = table_name

        self.problem_cfg = None
        self.key_map = None
        self.type_map = None

    def configure(self, problem_cfg):
        '''
        '''
        assert problem_cfg is not None
        self.problem_cfg = problem_cfg.copy()

        # mapping from keys to database columns (e.g., X -> [x1, x2, ...])
        self.key_map = {
            'status': 'status',
            'X': [f'x{i + 1}' for i in range(self.problem_cfg['n_var'])],
            'Y': [f'f{i + 1}' for i in range(self.problem_cfg['n_obj'])],
            'Y_expected': [f'f{i + 1}_expected' for i in range(self.problem_cfg['n_obj'])],
            'Y_uncertainty': [f'f{i + 1}_uncertainty' for i in range(self.problem_cfg['n_obj'])],
            'pareto': 'pareto',
            'batch': 'batch',
        }

        var_type_map = {
            'continuous': float,
            'integer': int,
            'binary': int,
            'categorical': str,
            'mixed': object,
        }

        # mapping from keys to data types
        self.type_map = {
            'status': str,
            'X': var_type_map[self.problem_cfg['type']],
            'Y': float,
            'Y_expected': float,
            'Y_uncertainty': float,
            'pareto': bool,
            'batch': int,
        }

    def _map_key(self, key, flatten=False):
        '''
        Get mapped keys from self.key_map
        '''
        if isinstance(key, str):
            return self.key_map[key]
        elif isinstance(key, list):
            if not flatten:
                return [self.key_map[k] for k in key]
            else:
                result = []
                for k in key:
                    mapped_key = self.key_map[k]
                    if isinstance(mapped_key, list):
                        result.extend(mapped_key)
                    else:
                        result.append(mapped_key)
                return result
        else:
            raise NotImplementedError

    def _insert(self, key_list, data_list):
        '''
        '''
        sample_len = len(data_list[0])
        for data in data_list:
            assert len(data) == sample_len

        # compute batch number
        batch_history = self.db.select_data(table=self.table_name, column='batch')
        if len(batch_history) == 0:
            batch = np.zeros(sample_len, dtype=int)
        else:
            batch = batch_history[-1][0] + 1
            batch = np.full(sample_len, batch)

        # insert data
        rowids = self.db.insert_multiple_data(table=self.table_name, column=self._map_key(key_list + ['batch'], flatten=True), 
            data=data_list + [batch], transform=True)
        return rowids

    def insert_design(self, X):
        '''
        '''
        return self._insert(key_list=['X'], data_list=[X])

    def insert_design_and_prediction(self, X, Y_expected, Y_uncertainty):
        '''
        '''
        return self._insert(key_list=['X', 'Y_expected', 'Y_uncertainty'], data_list=[X, Y_expected, Y_uncertainty])

    def insert_design_and_evaluation(self, X, Y):
        '''
        '''
        return self._insert(key_list=['X', 'Y'], data_list=[X, Y])

    def update_prediction(self, Y_expected, Y_uncertainty, rowids):
        '''
        '''
        # update data (Y_expected, Y_uncertainty)
        self.db.update_multiple_data(table=self.table_name, column=self._map_key(['Y_expected', 'Y_uncertainty'], flatten=True), 
            data=[Y_expected, Y_uncertainty], rowid=rowids, transform=True)

    def update_evaluation(self, Y, rowids):
        '''
        '''
        # update data (status, Y)
        status = ['evaluated'] * len(rowids)
        self.db.update_multiple_data(table=self.table_name, column=self._map_key(['Y', 'status'], flatten=True), 
            data=[Y, status], rowid=rowids, transform=True)

        # load data
        Y_prev = self.load('Y')
        if len(Y_prev) == 0:
            Y_all = Y
            rowids_all = rowids
        else:
            rowids_prev = np.where((~np.isnan(Y_prev)).all(axis=1))[0] + 1
            Y_prev = Y_prev[rowids_prev - 1]
            Y_all = np.vstack([Y_prev, Y])
            rowids_all = np.concatenate([rowids_prev, rowids])

        # update data (pareto)
        pareto = check_pareto(Y_all, self.problem_cfg['obj_type']).astype(int)
        self.db.update_multiple_data(table=self.table_name, column=['pareto'], data=[pareto], rowid=rowids_all, transform=True)

    def initialize(self, X, Y=None):
        '''
        Initialize database table with initial data X, Y
        '''
        self.db.init_table(name=self.table_name, problem_cfg=self.problem_cfg)

        if Y is None:
            return self.insert_design(X)
        else:
            return self.insert_design_and_evaluation(X, Y)

    def load(self, keys, rowid=None):
        '''
        Load data from database table
        '''
        data = self.db.select_data(table=self.table_name, column=self._map_key(keys, flatten=True), rowid=rowid)

        if type(keys) == list:
            mapped_keys = self._map_key(keys)
            res_len = [len(k) if type(k) == list else 1 for k in mapped_keys]
            res_cumsum = np.cumsum(res_len)
            result_list = [[] for _ in range(len(keys))]

            for row in range(len(data)):
                res_idx = 0
                for col in range(len(data[row])):
                    if col >= res_cumsum[res_idx]:
                        res_idx += 1
                    if res_len[res_idx] == 1:
                        result_list[res_idx].append(data[row][col])
                    else:
                        if col == 0 or col == res_cumsum[res_idx - 1]:
                            result_list[res_idx].append([])
                        result_list[res_idx][-1].append(data[row][col])

            dtype = [self.type_map[key] for key in keys]
            for i in range(len(dtype)):
                result_list[i] = np.array(result_list[i], dtype=dtype[i])
            return result_list

        else:
            dtype = self.type_map[keys]
            return np.array(data, dtype=dtype)

    def evaluate(self, config, rowid):
        '''
        Evaluation of design variables given the associated rowid in database
        '''
        self.db.connect(force=True)
        
        # load design variables
        x_next = self.load('X', rowid=rowid)[0]
        self.db.update_data(table=self.table_name, column=['status'], data=['evaluating'], rowid=rowid)

        # run evaluation
        y_next = evaluate(config, x_next)

        # update evaluation result to database
        self.update_evaluation(np.atleast_2d(y_next), [rowid])

    def optimize(self, config, queue=None):
        '''
        Optimization of next batch of samples to evaluate, stored in 'rowids' rows in database
        '''
        # read current data from database
        X, Y = self.load(['X', 'Y'])
        valid_idx = np.where((~np.isnan(Y)).all(axis=1))[0]
        X, Y = X[valid_idx], Y[valid_idx]

        # optimize for best X_next
        X_next, (Y_expected, Y_uncertainty) = optimize(config, X, Y)

        # insert optimization and prediction result to database
        rowids = self.insert_design_and_prediction(X_next, Y_expected, Y_uncertainty)

        if queue is None:
            return rowids
        else:
            queue.put(rowids)

    def predict(self, config, rowids):
        '''
        '''
        # read current data from database
        X, Y = self.load(['X', 'Y'])
        valid_idx = np.where((~np.isnan(Y)).all(axis=1))[0]
        X, Y = X[valid_idx], Y[valid_idx]

        X_next = X[np.array(rowids) - 1]

        # predict performance of given input X_next
        Y_expected, Y_uncertainty = predict(config, X, Y, X_next)

        # update prediction result to database
        self.update_prediction(Y_expected, Y_uncertainty, rowids)

    def get_n_init_sample(self):
        batch = self.load('batch')
        return np.sum(batch == 0)

    def get_n_sample(self):
        return self.db.get_n_row(self.table_name)

    def get_n_valid_sample(self):
        status = self.load('status')
        return np.sum(status == 'evaluated')

    def quit(self):
        '''
        Quit database
        '''
        if self.db is not None:
            self.db.quit()
