import os
import numpy as np
from multiprocessing import Lock

from problem.common import build_problem
from system.utils.core import optimize, predict, evaluate
from system.utils.performance import check_pareto, calc_hypervolume, calc_pred_error


class Agent:
    '''
    Agent controlling data communication from & to database
    '''
    def __init__(self, database, table_name):
        self.db = database
        self.table_name = table_name

        self.problem_cfg = None
        self.can_eval = False
        self.key_map = None
        self.type_map = None
        self.ref_point = None

        self.initialized = False

        self.lock = Lock()

    def get_config(self):
        '''
        '''
        return self.db.query_config(self.table_name)

    def set_config(self, config):
        '''
        '''
        self.db.update_config(self.table_name, config)

        if self.problem_cfg is None: # first time

            problem_cfg = config['problem']
            problem = build_problem(problem_cfg['name']) 
            self.problem_cfg = problem.get_config()
            self.problem_cfg.update(problem_cfg)

            self.ref_point = self.problem_cfg['ref_point']
            self.can_eval = hasattr(problem, 'evaluate_objective') or self.problem_cfg['obj_func'] is not None

            # mapping from keys to database columns (e.g., X -> [x1, x2, ...])
            self.key_map = {
                'status': 'status',
                'X': [f'x{i + 1}' for i in range(self.problem_cfg['n_var'])],
                'Y': [f'f{i + 1}' for i in range(self.problem_cfg['n_obj'])],
                'Y_expected': [f'f{i + 1}_expected' for i in range(self.problem_cfg['n_obj'])],
                'Y_uncertainty': [f'f{i + 1}_uncertainty' for i in range(self.problem_cfg['n_obj'])],
                'pareto': 'pareto', 'batch': 'batch', 
                '_order': '_order', '_hypervolume': '_hypervolume',
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
                '_order': int,
                '_hypervolume': float,
            }

        elif config != self.problem_cfg: # update in the middle
            self.problem_cfg.update(config['problem'])
            self._set_ref_point(self.problem_cfg['ref_point'])

        if not self.initialized:
            self.initialized = self.check_initialized()

    '''
    Utilities
    '''

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

    def _get_valid_idx(self, data):
        if len(data.shape) == 1:
            return np.where((~np.isnan(data)))[0]
        elif len(data.shape) == 2:
            return np.where((~np.isnan(data)).all(axis=1))[0]
        else:
            raise NotImplementedError

    '''
    Design and performance
    '''

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
        rowids = self.insert_design(X)
        self.update_evaluation(Y, rowids)
        return rowids

    def update_prediction(self, Y_expected, Y_uncertainty, rowids):
        '''
        '''
        # update data (Y_expected, Y_uncertainty)
        self.db.update_multiple_data(table=self.table_name, column=self._map_key(['Y_expected', 'Y_uncertainty'], flatten=True), 
            data=[Y_expected, Y_uncertainty], rowid=rowids, transform=True)
        
    def update_evaluation(self, Y, rowids):
        '''
        '''
        # update data (Y, status, _order)
        status = ['evaluated'] * len(rowids)
        with self.lock:
            prev_order = self.load('_order')
            valid_idx = prev_order >= 0
            max_order = np.max(prev_order[valid_idx]) + 1 if valid_idx.any() else 0
            order = np.arange(max_order, max_order + len(rowids))
            self.db.update_multiple_data(table=self.table_name, column=self._map_key(['Y', 'status', '_order'], flatten=True), 
                data=[Y, status, order], rowid=rowids, transform=True)

            # update data (hypervolume)
            self._update_hypervolume(rowids)

        # update data (pareto)
        Y_all = self.load('Y')
        valid_idx = self._get_valid_idx(Y_all)
        Y_all = Y_all[valid_idx]
        rowids_all = valid_idx + 1
        pareto = check_pareto(Y_all, self.problem_cfg['obj_type']).astype(int)
        self.db.update_multiple_data(table=self.table_name, column=['pareto'], data=[pareto], rowid=rowids_all, transform=True)

        if not self.initialized:
            self.initialized = self.check_initialized()
            if self.initialized:
                self._init_ref_point()

    '''
    Hypervolume and model error
    '''

    def _update_hypervolume(self, rowids):
        '''
        '''
        if self.ref_point is None: return

        # load and check order (assume only called after some evaluations)
        all_order = self.load('_order')
        assert (all_order >= 0).any()
        curr_order = all_order[np.array(rowids) - 1]
        assert (curr_order >= 0).all()

        # find previously evaluated Y
        min_curr_order = np.min(curr_order)
        prev_order_idx = np.logical_and(all_order < min_curr_order, all_order >= 0)
        Y_all = self.load('Y')
        Y = Y_all[prev_order_idx]
        
        # compute hypervolume according to evaluation order
        hv_list = []
        for rowid in rowids:
            if len(Y) > 0:
                Y = np.vstack([Y, np.atleast_2d(Y_all[rowid - 1])])
            else:
                Y = np.atleast_2d(Y_all[rowid - 1])
            hv = calc_hypervolume(Y, self.ref_point, self.problem_cfg['obj_type'])
            hv_list.append(hv)

        self.db.update_multiple_data(table=self.table_name, column=['_hypervolume'], data=[hv_list], rowid=rowids, transform=True)

    def _reload_hypervolume(self):
        '''
        '''
        if self.ref_point is None: return

        # load and check order
        all_order, Y = self.load(['_order', 'Y'])
        if len(all_order) == 0: return
        valid_idx = all_order >= 0
        if not valid_idx.any(): return
        valid_order = all_order[valid_idx]

        # compute hypervolume according to evaluation order
        rowids = []
        hv_list = []
        Y_curr = np.zeros((0, Y.shape[1]))
        for i in np.sort(valid_order):
            idx = int(np.where(all_order == i)[0][0])
            rowids.append(idx + 1)
            Y_curr = np.vstack([Y_curr, np.atleast_2d(Y[idx])])
            hv = calc_hypervolume(Y_curr, self.ref_point, self.problem_cfg['obj_type'])
            hv_list.append(hv)

        self.db.update_multiple_data(table=self.table_name, column=['_hypervolume'], data=[hv_list], rowid=rowids, transform=True)

    def _init_ref_point(self):
        '''
        '''
        if self.ref_point is not None and None not in self.ref_point: return

        # compute reference point based on current data
        Y = self.load('Y')
        valid_idx = self._get_valid_idx(Y)
        assert len(valid_idx) > 0, 'no evaluated data so far, cannot set default reference point'
        Y = Y[valid_idx]

        ref_point = np.zeros(Y.shape[1])
        for i, m in enumerate(self.problem_cfg['obj_type']):
            if m == 'min':
                ref_point[i] = np.max(Y[:, i])
            elif m == 'max':
                ref_point[i] = np.min(Y[:, i])
            else:
                raise Exception('obj_type must be min/max')

        # set reference point where values are not provided
        if self.ref_point is not None:
            keep_idx = np.array(self.ref_point) != None
            ref_point[keep_idx] = np.array(self.ref_point)[keep_idx]
        self._set_ref_point(ref_point.tolist())

        # update config
        config = self.get_config()
        config['problem']['ref_point'] = self.ref_point
        self.db.update_config(self.table_name, config)

    def _set_ref_point(self, ref_point):
        '''
        '''
        # only called when ref_point is inited from data or user changed ref_point in the middle
        assert len(ref_point) == self.problem_cfg['n_obj']
        assert type(ref_point) == list
        if ref_point != self.ref_point:
            self.ref_point = ref_point
            self._reload_hypervolume()

    def load_hypervolume(self):
        '''
        '''
        with self.lock:
            order, hypervolume = self.load(['_order', '_hypervolume'])

        if len(order) == 0: return np.array([])
        valid_idx = order >= 0
        if valid_idx.sum() == 0: return np.array([])
        order, hypervolume = np.argsort(order[valid_idx]), hypervolume[valid_idx]

        ordered_hypervolume = np.zeros_like(hypervolume)
        ordered_hypervolume[order] = hypervolume
        return ordered_hypervolume

    def load_model_error(self):
        '''
        '''
        order, Y, Y_expected = self.load(['_order', 'Y', 'Y_expected'])
        if len(order) == 0: return np.array([])
        valid_idx = order >= 0
        if valid_idx.sum() == 0: return np.array([])
        order, Y, Y_expected = np.argsort(order[valid_idx]), Y[valid_idx], Y_expected[valid_idx]

        ordered_Y, ordered_Y_expected = np.zeros_like(Y), np.zeros_like(Y_expected)
        ordered_Y[order] = Y
        ordered_Y_expected[order] = Y_expected
        valid_idx = np.intersect1d(self._get_valid_idx(ordered_Y), self._get_valid_idx(ordered_Y_expected))
        ordered_Y, ordered_Y_expected = ordered_Y[valid_idx], ordered_Y_expected[valid_idx]
        return calc_pred_error(ordered_Y, ordered_Y_expected, average=False)

    '''
    High-level commands
    '''

    def initialize(self, X_evaluated, X_unevaluated, Y_evaluated):
        '''
        Initialize database table with initial data X, Y
        '''
        self.db.init_table(name=self.table_name, problem_cfg=self.problem_cfg)

        # check validity of input
        assert (X_unevaluated is not None) or (X_evaluated is not None)
        if X_evaluated is not None:
            assert Y_evaluated is not None
            assert len(X_evaluated) == len(Y_evaluated)

        if X_evaluated is not None and X_unevaluated is not None:
            rowids = self.insert_design([X_evaluated, X_unevaluated])
            rowids_evaluated, rowids_unevaluated = rowids[:len(X_evaluated)], rowids[len(X_evaluated):]
        elif X_evaluated is not None:
            rowids = self.insert_design(X_evaluated)
            rowids_evaluated, rowids_unevaluated = rowids, None
        elif X_unevaluated is not None:
            rowids = self.insert_design(X_unevaluated)
            rowids_evaluated, rowids_unevaluated = None, rowids
        else:
            raise Exception()

        if Y_evaluated is not None:
            self.update_evaluation(Y_evaluated, rowids_evaluated)

        return rowids_unevaluated

    def check_initialized(self):
        '''
        '''
        if self.check_table_exist():
            batch, order = self.load(['batch', '_order'])
            if len(batch) == 0: return False
            init_idx = np.where(batch == 0)[0]
            return (order[init_idx] >= 0).all()
        else:
            return False

    def check_table_exist(self):
        '''
        '''
        return self.db.check_inited_table_exist(name=self.table_name)

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
            result = np.array(data, dtype=dtype)
            if type(self._map_key(keys)) == str:
                return result.squeeze()
            else:
                return result

    def evaluate(self, config, rowid):
        '''
        Evaluation of design variables given the associated rowid in database
        '''
        if not self.can_eval: return
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
        valid_idx = self._get_valid_idx(Y)
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
        X_next = X[np.array(rowids) - 1]
        valid_idx = self._get_valid_idx(Y)
        X, Y = X[valid_idx], Y[valid_idx]

        # predict performance of given input X_next
        Y_expected, Y_uncertainty = predict(config, X, Y, X_next)

        # update prediction result to database
        self.update_prediction(Y_expected, Y_uncertainty, rowids)

    def quit(self):
        '''
        Quit database
        '''
        if self.db is not None:
            self.db.quit()

    '''
    Status
    '''

    def get_n_init_sample(self):
        batch = self.load('batch')
        return np.sum(batch == 0)

    def get_n_sample(self):
        return self.db.get_n_row(self.table_name)

    def get_n_valid_sample(self):
        status = self.load('status')
        return np.sum(status == 'evaluated')

    def get_max_hv(self):
        hypervolume = self.load('_hypervolume')
        if len(hypervolume) == 0: return None
        valid_idx = self._get_valid_idx(hypervolume)
        if len(valid_idx) == 0: return None
        return hypervolume[valid_idx].max()
