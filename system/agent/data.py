import os
import numpy as np
from multiprocessing import Value

from system.utils.process_safe import ProcessSafeExit
from system.utils.core import optimize, predict, evaluate
from system.utils.performance import check_pareto


class DataAgent:
    '''
    Agent controlling data communication from & to database
    '''
    def __init__(self, database, table_name):
        self.db = database
        self.table_name = table_name

        self.n_init_sample = Value('i', 0)
        self.n_valid_sample = Value('i', 0)
        self.n_sample = Value('i', 0)

        self.problem_cfg = None

    def configure(self, problem_cfg):
        '''
        '''
        assert problem_cfg is not None
        self.problem_cfg = problem_cfg.copy()

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

    def init_table(self, create=False):
        '''
        Initialize database table
        '''
        if create:
            self.db.init_table(name=self.table_name, problem_cfg=self.problem_cfg)

        # high level key mapping (e.g., X -> [x1, x2, ...])
        self.key_map = {
            'status': 'status',
            'X': [f'x{i + 1}' for i in range(self.problem_cfg['n_var'])],
            'Y': [f'f{i + 1}' for i in range(self.problem_cfg['n_obj'])],
            'Y_expected': [f'f{i + 1}_expected' for i in range(self.problem_cfg['n_obj'])],
            'Y_uncertainty': [f'f{i + 1}_uncertainty' for i in range(self.problem_cfg['n_obj'])],
            'is_pareto': 'is_pareto',
            'config_id': 'config_id',
            'batch_id': 'batch_id',
        }

        var_type_map = {
            'continuous': float,
            'integer': int,
            'binary': int,
            'categorical': str,
            'mixed': object,
        }

        self.type_map = {
            'status': str,
            'X': var_type_map[self.problem_cfg['type']],
            'Y': float,
            'Y_expected': float,
            'Y_uncertainty': float,
            'is_pareto': bool,
            'config_id': int,
            'batch_id': int,
        }

    def init_data(self, X, Y=None):
        '''
        Initialize database table with initial data X, Y
        '''
        n_init_sample = X.shape[0]

        config_id = np.zeros(n_init_sample, dtype=int)
        batch_id = np.zeros(n_init_sample, dtype=int)

        if Y is not None:
            is_pareto = check_pareto(Y, self.problem_cfg['obj_type']).astype(int)

        # update data
        if Y is None:
            self.db.insert_multiple_data(table=self.table_name, column=self._map_key(['X', 'config_id', 'batch_id'], flatten=True),
                data=[X, config_id, batch_id], transform=True)
        else:
            status = ['evaluated'] * n_init_sample
            self.db.insert_multiple_data(table=self.table_name, column=self._map_key(['status', 'X', 'Y', 'is_pareto', 'config_id', 'batch_id'], flatten=True),
                data=[status, X, Y, is_pareto, config_id, batch_id], transform=True)

        # update stats
        with self.n_init_sample.get_lock():
            self.n_init_sample.value += n_init_sample
        
        with self.n_sample.get_lock():
            self.n_sample.value += n_init_sample
        
        with self.n_valid_sample.get_lock():
            if Y is not None:
                self.n_valid_sample.value += n_init_sample

        rowids = np.arange(n_init_sample, dtype=int) + 1
        return rowids.tolist()

    def insert(self, X, Y_expected, Y_uncertainty, config_id):
        '''
        Insert optimization result to database
        Input:
            config_id: current configuration index (user can sequentially reload different config files)
        '''
        sample_len = len(X)
        config_id = np.full(sample_len, config_id)

        # update data
        batch_id = self.db.select_data(table=self.table_name, column='batch_id')[-1][0] + 1
        batch_id = np.full(sample_len, batch_id)
        self.db.insert_multiple_data(table=self.table_name, column=self._map_key(['X', 'Y_expected', 'Y_uncertainty', 'config_id', 'batch_id'], flatten=True), 
            data=[X, Y_expected, Y_uncertainty, config_id, batch_id], transform=True)
        n_row = self.db.get_n_row(self.table_name)

        # update stats
        with self.n_sample.get_lock():
            self.n_sample.value += sample_len
            
        rowids = np.arange(n_row - sample_len, n_row, dtype=int) + 1
        return rowids.tolist()

    def update(self, y, rowid):
        '''
        Update evaluation result to database
        Input:
            rowid: row index to be updated (count from 1)
        '''
        # update data
        Y_prev = self.load('Y')
        rowids_prev = np.where((~np.isnan(Y_prev)).all(axis=1))[0] + 1
        Y_prev = Y_prev[rowids_prev - 1]

        self.db.update_data(table=self.table_name, column=['status'] + self._map_key('Y'), data=['evaluated', y], rowid=rowid, transform=True)

        if len(Y_prev) == 0:
            self.db.update_data(table=self.table_name, column=['is_pareto'], data=[1], rowid=rowid, transform=True)
        else:
            Y_all = np.vstack([Y_prev, y])
            rowids_all = np.concatenate([rowids_prev, [rowid]])
            is_pareto = check_pareto(Y_all, self.problem_cfg['obj_type']).astype(int)
            self.db.update_multiple_data(table=self.table_name, column=['is_pareto'], data=[is_pareto], rowid=rowids_all, transform=True)

        # update stats
        with self.n_valid_sample.get_lock():
            self.n_valid_sample.value += 1

    def update_batch(self, Y, rowids):
        '''
        Update batch evaluation result to database
        Input:
            rowids: row indices to be updated (count from 1)
        '''
        # update data
        Y_prev = self.load('Y')
        rowids_prev = np.where((~np.isnan(Y_prev)).all(axis=1))[0] + 1
        Y_prev = Y_prev[rowids_prev - 1]

        Y_all = np.vstack([Y_prev, Y])
        rowids_all = np.concatenate([rowids_prev, rowids])
        is_pareto = check_pareto(Y_all, self.problem_cfg['obj_type']).astype(int)

        self.db.update_multiple_data(table=self.table_name, column=self._map_key('Y'), data=[Y], rowid=rowids, transform=True)
        self.db.update_multiple_data(table=self.table_name, column=['is_pareto'], data=[is_pareto], rowid=rowids_all, transform=True)

        # update stats
        with self.n_valid_sample.get_lock():
            self.n_valid_sample.value += len(Y)

    def _load(self, keys, rowid=None):
        '''
        '''
        data = self.db.select_data(table=self.table_name, column=self._map_key(keys, flatten=True), rowid=rowid)
        return data

    def load_str(self, keys, rowid=None):
        '''
        Load data represented as string from database table
        '''
        data = self._load(keys, rowid)
        data_str = np.array(data, dtype=str)
        return data_str

    def load(self, keys, rowid=None):
        '''
        Load data from database table
        '''
        data = self._load(keys, rowid)

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

    def _predict(self, config, X_next):
        '''
        Performance prediction of given design variables X_next
        '''
        # read current data from database
        X, Y = self.load(['X', 'Y'])
        valid_idx = np.where((~np.isnan(Y)).all(axis=1))[0]
        X, Y = X[valid_idx], Y[valid_idx]

        # predict performance of given input X_next
        Y_expected, Y_uncertainty = predict(config, X, Y, X_next)

        return Y_expected, Y_uncertainty

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
        try:
            self.update(y_next, rowid)
        except ProcessSafeExit:
            self.correct_stats()
            raise ProcessSafeExit()

    def optimize(self, config, config_id, queue=None):
        '''
        Optimization of next batch of samples to evaluate, stored in 'rowids' rows in database
        '''
        # read current data from database
        X, Y = self.load(['X', 'Y'])
        valid_idx = np.where((~np.isnan(Y)).all(axis=1))[0]
        X, Y = X[valid_idx], Y[valid_idx]

        # optimize for best X_next
        X_next = optimize(config, X, Y)

        # predict performance of X_next
        Y_expected, Y_uncertainty = self._predict(config, X_next)

        # insert optimization and prediction result to database
        try:
            rowids = self.insert(X_next, Y_expected, Y_uncertainty, config_id)
        except ProcessSafeExit:
            self.correct_stats()
            raise ProcessSafeExit()

        if queue is None:
            return rowids
        else:
            queue.put(rowids)

    def predict(self, config, config_id, X_next, queue=None):
        '''
        Performance prediction of given design variables X_next, stored in 'rowids' rows in database
        '''
        # predict performance of given input X_next
        Y_expected, Y_uncertainty = self._predict(config, X_next)

        # insert design variables and prediction result to database
        try:
            rowids = self.insert(X_next, Y_expected, Y_uncertainty, config_id)
        except ProcessSafeExit:
            self.correct_stats()
            raise ProcessSafeExit()

        if queue is None:
            return rowids
        else:
            queue.put(rowids)

    def get_n_init_sample(self):
        with self.n_init_sample.get_lock():
            num = self.n_init_sample.value
        return num

    def get_n_sample(self):
        with self.n_sample.get_lock():
            num = self.n_sample.value
        return num

    def get_n_valid_sample(self):
        with self.n_valid_sample.get_lock():
            num = self.n_valid_sample.value
        return num

    def correct_stats(self):
        '''
        Correct stats variables due to process termination
        '''
        status = self.load_str('status')
        n_sample = len(status)
        n_valid_sample = np.sum(status == 'evaluated')
        with self.n_sample.get_lock():
            self.n_sample.value = n_sample
        with self.n_valid_sample.get_lock():
            self.n_valid_sample.value = n_valid_sample

    def quit(self):
        '''
        Quit database
        '''
        if self.db is not None:
            self.db.quit()
