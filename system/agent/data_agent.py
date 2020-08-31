import os
import numpy as np

from system.database import Database
from system.core import optimize, predict, evaluate
from system.utils import check_pareto


class DataAgent:
    '''
    Agent controlling data communication from & to database
    '''
    def __init__(self, n_var, n_obj, result_dir):
        '''
        Agent initialization
        '''
        self.n_var = n_var
        self.n_obj = n_obj
        self.n_init_sample = 0

        # create & init database
        db_path = os.path.join(result_dir, 'data.db')
        self._create(db_path)

    def _create(self, db_path):
        '''
        Create database table
        '''
        self.db = Database(db_path)

        # keys and associated datatypes of database table
        key_list = [f'x{i + 1} real' for i in range(self.n_var)] + \
            [f'f{i + 1} real' for i in range(self.n_obj)] + \
            [f'f{i + 1}_expected real' for i in range(self.n_obj)] + \
            [f'f{i + 1}_uncertainty real' for i in range(self.n_obj)] + \
            ['is_pareto boolean', 'config_id integer', 'batch_id integer']
        self.db.create('data', key=key_list)
        self.db.commit()

        # high level key mapping (e.g., X -> [x1, x2, ...])
        self.key_map = {
            'X': [f'x{i + 1}' for i in range(self.n_var)],
            'Y': [f'f{i + 1}' for i in range(self.n_obj)],
            'Y_expected': [f'f{i + 1}_expected' for i in range(self.n_obj)],
            'Y_uncertainty': [f'f{i + 1}_uncertainty' for i in range(self.n_obj)],
            'is_pareto': 'is_pareto',
            'config_id': 'config_id',
            'batch_id': 'batch_id',
        }

        # datatype mapping in python
        self.type_map = {
            'X': float,
            'Y': float,
            'Y_expected': float,
            'Y_uncertainty': float,
            'is_pareto': bool,
            'config_id': int,
            'batch_id': int,
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

    def _map_type(self, key):
        '''
        Get mapped types from self.type_map
        '''
        if isinstance(key, str):
            return self.type_map[key]
        elif isinstance(key, list):
            return [self.type_map[k] for k in key]
        else:
            raise NotImplementedError

    def initialize(self, X, Y=None):
        '''
        Initialize database table with initial data X, Y
        '''
        n_init_sample = X.shape[0]
        self.n_init_sample += n_init_sample

        Y_uncertainty = np.zeros((n_init_sample, self.n_obj))
        Y_expected = np.zeros((n_init_sample, self.n_obj))
        config_id = np.zeros(n_init_sample, dtype=int)
        batch_id = np.zeros(n_init_sample, dtype=int)

        if Y is not None:
            is_pareto = check_pareto(Y)

        with self.db.get_lock():
            if Y is None:
                self.db.insert('data', key=self._map_key(['X', 'Y_uncertainty', 'Y_expected', 'config_id', 'batch_id'], flatten=True),
                    data=[X, Y_uncertainty, Y_expected, config_id, batch_id], lock=False)
            else:
                self.db.insert('data', key=None, data=[X, Y, Y_uncertainty, Y_expected, is_pareto, config_id, batch_id], lock=False)
            last_rowid = self.db.get_last_rowid('data', lock=False)
            self.db.commit()

        rowids = np.arange(last_rowid - n_init_sample, last_rowid, dtype=int) + 1
        return rowids.tolist()

    def insert(self, X, Y_expected, Y_uncertainty, config_id):
        '''
        Insert optimization result to database
        Input:
            config_id: current configuration index (user can sequentially reload different config files)
        '''
        sample_len = len(X)
        config_id = np.full(sample_len, config_id)

        with self.db.get_lock():
            batch_id = self.db.select_last('data', key='batch_id', dtype=int, lock=False) + 1
            batch_id = np.full(sample_len, batch_id)
            self.db.insert('data', key=self._map_key(['X', 'Y_expected', 'Y_uncertainty', 'config_id', 'batch_id'], flatten=True), 
                data=[X, Y_expected, Y_uncertainty, config_id, batch_id], lock=False)
            last_rowid = self.db.get_last_rowid('data', lock=False)
            self.db.commit()
            
        rowids = np.arange(last_rowid - sample_len, last_rowid, dtype=int) + 1
        return rowids.tolist()

    def update(self, y, rowid):
        '''
        Update evaluation result to database
        Input:
            rowid: row index to be updated (count from 1)
        '''
        with self.db.get_lock():
            all_Y = self.load('Y', valid_only=False, lock=False)
            all_Y[rowid - 1] = y
            valid_idx = np.where(~np.isnan(all_Y).any(axis=1))
            all_Y_valid = all_Y[valid_idx]

            is_pareto = np.full(len(all_Y), False)
            is_pareto[valid_idx] = check_pareto(all_Y_valid)
            pareto_id = np.where(is_pareto)[0] + 1

            self.db.update('data', key=self._map_key('Y'), data=[y], rowid=rowid, lock=False)
            self.db.update('data', key='is_pareto', data=False, rowid=None, lock=False)
            self.db.update('data', key='is_pareto', data=True, rowid=pareto_id, lock=False)
            self.db.commit()

    def update_batch(self, Y, rowids):
        '''
        Update batch evaluation result to database
        Input:
            rowids: row indices to be updated (count from 1)
        '''
        with self.db.get_lock():
            all_Y = self.load('Y', valid_only=False, lock=False)
            all_Y[np.array(rowids) - 1] = Y
            valid_idx = np.where(~np.isnan(all_Y).any(axis=1))
            all_Y_valid = all_Y[valid_idx]

            is_pareto = np.full(len(all_Y), False)
            is_pareto[valid_idx] = check_pareto(all_Y_valid)
            pareto_id = np.where(is_pareto)[0] + 1

            self.db.update('data', key=self._map_key('Y'), data=[Y], rowid=rowids, lock=False)
            self.db.update('data', key='is_pareto', data=False, rowid=None, lock=False)
            self.db.update('data', key='is_pareto', data=True, rowid=pareto_id, lock=False)
            self.db.commit()

    def load(self, keys, valid_only=True, rowid=None, lock=True):
        '''
        Load array from database table
        Input:
            valid_only: if only keeps valid data (evaluated data)
        '''
        result = self.db.select('data', key=self._map_key(keys), dtype=self._map_type(keys), rowid=rowid, lock=lock)
        if valid_only:
            if isinstance(result, list):
                if 'Y' not in keys:
                    return result
                Y_idx = keys.index('Y')
                isnan = np.isnan(result[Y_idx]).any(axis=1)
                valid_idx = np.where(~isnan)[0]
                return [res[valid_idx] for res in result]
            else:
                if 'Y' != keys:
                    return result
                isnan = np.isnan(result).any(axis=1)
                valid_idx = np.where(~isnan)[0]
                return result[valid_idx]
        else:
            return result

    def get_sample_num(self):
        '''
        Get number of samples (rows)
        '''
        return self.db.get_last_rowid('data')

    def _predict(self, config, X_next):
        '''
        Performance prediction of given design variables X_next
        '''
        # read current data from database
        X, Y = self.load(['X', 'Y'])

        # predict performance of given input X_next
        Y_expected, Y_uncertainty = predict(config, X, Y, X_next)

        return Y_expected, Y_uncertainty

    def evaluate(self, config, rowid):
        '''
        Evaluation of design variables given the associated rowid in database
        '''
        # load design variables
        x_next = self.load('X', valid_only=False, rowid=rowid)[0]

        # run evaluation
        y_next = evaluate(config, x_next)

        # update evaluation result to database
        self.update(y_next, rowid)

    def optimize(self, config, config_id, queue=None):
        '''
        Optimization of next batch of samples to evaluate, stored in 'rowids' rows in database
        '''
        # read current data from database
        X, Y = self.load(['X', 'Y'])

        # optimize for best X_next
        X_next = optimize(config, X, Y)

        # predict performance of X_next
        Y_expected, Y_uncertainty = self._predict(config, X_next)

        # insert optimization and prediction result to database
        rowids = self.insert(X_next, Y_expected, Y_uncertainty, config_id)

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
        rowids = self.insert(X_next, Y_expected, Y_uncertainty, config_id)

        if queue is None:
            return rowids
        else:
            queue.put(rowids)

    def get_status(self):
        '''
        Get the status id of database
        '''
        return self.db.status.value

    def quit(self):
        '''
        Quit database
        '''
        self.db.quit()
