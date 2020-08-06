import os
import numpy as np
import yaml
from multiprocessing import Process, Lock
from pymoo.performance_indicator.hv import Hypervolume

from problems.common import build_problem
from system.database import Database
from system.core import optimize, predict, evaluate
from system.utils import check_pareto, calc_pred_error


class DataAgent:
    '''
    Agent controlling data communication from & to database
    '''
    def __init__(self, config, result_dir):
        '''
        Agent initialization
        '''
        # build problem and initial data
        problem, X_init, Y_init = build_problem(config['problem'], get_init_samples=True)

        self.n_var = problem.n_var
        self.n_obj = problem.n_obj
        self.hv = Hypervolume(ref_point=problem.ref_point) # hypervolume calculator
        self.n_init_sample = None

        # create & init database
        db_path = os.path.join(result_dir, 'data.db')
        self._create(db_path)
        self._init(X_init, Y_init)

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
            ['hv real', 'pred_error real', 'is_pareto boolean', 'config_id integer', 'batch_id integer']
        self.db.create('data', key=key_list)
        self.db.commit()

        # high level key mapping (e.g., X -> [x1, x2, ...])
        self.key_map = {
            'X': [f'x{i + 1}' for i in range(self.n_var)],
            'Y': [f'f{i + 1}' for i in range(self.n_obj)],
            'Y_expected': [f'f{i + 1}_expected' for i in range(self.n_obj)],
            'Y_uncertainty': [f'f{i + 1}_uncertainty' for i in range(self.n_obj)],
            'hv': 'hv',
            'pred_error': 'pred_error',
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
            'hv': float,
            'pred_error': float,
            'is_pareto': bool,
            'config_id': int,
            'batch_id': int,
        }

    def _mapped_keys(self, keys, flatten=False):
        '''
        Get mapped keys from self.key_map
        '''
        if not flatten:
            return [self.key_map[key] for key in keys]
        else:
            result = []
            for key in keys:
                mapped_key = self.key_map[key]
                if isinstance(mapped_key, list):
                    result.extend(mapped_key)
                else:
                    result.append(mapped_key)
            return result

    def _mapped_types(self, keys, flatten=False):
        '''
        Get mapped types from self.type_map
        '''
        if not flatten:
            return [self.type_map[key] for key in keys]
        else:
            result = []
            for key in keys:
                mapped_key = self.type_map[key]
                if isinstance(mapped_key, list):
                    result.extend(mapped_key)
                else:
                    result.append(mapped_key)
            return result

    def _init(self, X, Y):
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
        batch_id = np.zeros(self.n_init_sample, dtype=int)

        with self.db.get_lock():
            self.db.insert('data', key=None, data=[X, Y, Y_expected, Y_uncertainty, hv_value, pred_error, is_pareto, config_id, batch_id])
            self.db.commit()

    def _insert(self, X, Y_expected, Y_uncertainty, config_id):
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
            self.db.insert('data', key=self._mapped_keys(['X', 'Y_expected', 'Y_uncertainty', 'config_id', 'batch_id'], flatten=True), 
                data=[X, Y_expected, Y_uncertainty, config_id, batch_id])
            last_rowid = self.db.get_last_rowid('data')
            self.db.commit()
            
        rowids = np.arange(last_rowid - sample_len, last_rowid, dtype=int) + 1
        return rowids

    def _update(self, Y, rowids):
        '''
        Update evaluation result to database
        Input:
            rowids: row indices to be updated
        '''
        with self.db.get_lock():
            all_Y, all_Y_expected = self.load(['Y', 'Y_expected'], valid_only=False, lock=False)
            all_Y[rowids - 1] = Y
            valid_idx = np.where(~np.isnan(all_Y).any(axis=1))
            all_Y_valid, all_Y_expected_valid = all_Y[valid_idx], all_Y_expected[valid_idx]

            # compute associated values based on evaluation data (hv, pred_error, is_pareto)
            sample_len, all_len = len(rowids), len(all_Y)
            hv_value = np.full(sample_len, self.hv.calc(all_Y_valid))
            pred_error = calc_pred_error(all_Y_valid[self.n_init_sample:], all_Y_expected_valid[self.n_init_sample:])
            pred_error = np.full(sample_len, pred_error)
            is_pareto = np.full(all_len, False)
            is_pareto[valid_idx] = check_pareto(all_Y_valid)
            pareto_id = np.where(is_pareto)[0] + 1

            for i, rowid in enumerate(rowids.tolist()):
                self.db.update('data', key=self._mapped_keys(['Y', 'hv', 'pred_error'], flatten=True), 
                    data=[Y[i], hv_value[i], pred_error[i]], rowid=rowid)
            self.db.update('data', key='is_pareto', data=False, rowid=None)
            self.db.update('data', key='is_pareto', data=True, rowid=pareto_id)
            self.db.commit()

    def load(self, keys, valid_only=True, lock=True):
        '''
        Load array from database table
        Input:
            valid_only: if only keeps valid data, i.e., filled data, without nan
        '''
        result = self.db.select('data', key=self._mapped_keys(keys), dtype=self._mapped_types(keys), lock=lock)
        if valid_only:
            if isinstance(result, list):
                isnan = None
                for res in result:
                    assert len(res.shape) in [1, 2]
                    curr_isnan = np.isnan(res) if len(res.shape) == 1 else np.isnan(res).any(axis=1)
                    if isnan is None:
                        isnan = curr_isnan
                    else:
                        isnan = np.logical_or(isnan, curr_isnan)
                valid_idx = np.where(~isnan)[0]
                return [res[valid_idx] for res in result]
            else:
                assert len(result.shape) in [1, 2]
                isnan = np.isnan(result) if len(result.shape) == 1 else np.isnan(result).any(axis=1)
                valid_idx = np.where(~isnan)[0]
                return result[valid_idx]
        else:
            return result

    def get_sample_num(self):
        '''
        Get number of samples (rows)
        '''
        return self.db.get_last_rowid('data')

    def predict(self, config, X_next):
        '''
        Performance prediction of given design variables X_next
        '''
        # read current data from database
        X, Y = self.load(['X', 'Y'])

        # predict performance of given input X_next
        Y_expected, Y_uncertainty = predict(config, X, Y, X_next)

        return Y_expected, Y_uncertainty

    def update(self, config, X_next, Y_expected, Y_uncertainty, config_id):
        '''
        Update given data to database
        '''
        # insert optimization and prediction result to database
        rowids = self._insert(X_next, Y_expected, Y_uncertainty, config_id)
        
        # run evaluation
        Y_next = evaluate(config, X_next)
        
        # update evaluation result to database
        self._update(Y_next, rowids)

    def optimize(self, config, config_id):
        '''
        Automatic execution of optimization workflow
        '''
        # run several iterations
        for _ in range(config['general']['n_iter']):

            # read current data from database
            X, Y = self.load(['X', 'Y'])

            # optimize for best X_next
            X_next = optimize(config, X, Y)

            # predict performance of X_next
            Y_expected, Y_uncertainty = self.predict(config, X_next)

            # update X_next related data to database
            self.update(config, X_next, Y_expected, Y_uncertainty, config_id)

    def quit(self):
        '''
        Quit database
        '''
        self.db.quit()


class ProblemAgent:
    '''
    Agent controlling problem communication from & to file system
    '''
    def __init__(self):
        '''
        Agent initialization
        '''
        # create folder
        self.problem_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'problems', 'custom', 'yaml')
        os.makedirs(self.problem_dir, exist_ok=True)

    def save_problem(self, config):
        '''
        Save problem config as yaml file
        '''
        name = config['name']
        config_path = os.path.join(self.problem_dir, f'{name}.yml')
        try:
            with open(config_path, 'w') as fp:
                yaml.dump(config, fp, default_flow_style=False, sort_keys=False)
        except:
            raise Exception('not a valid problem config')
        
    def load_problem(self, name):
        '''
        Load problem config from yaml file
        '''
        config_path = os.path.join(self.problem_dir, f'{name}.yml')
        try:
            with open(config_path, 'r') as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
        except:
            raise Exception('not a valid config file')
        return config

    def list_problem(self):
        '''
        List all the problems saved
        '''
        return [name[:-4] for name in os.listdir(self.problem_dir) if name.endswith('.yml')]

    def remove_problem(self, name):
        '''
        Remove a problem from saved problems
        '''
        config_path = os.path.join(self.problem_dir, f'{name}.yml')
        try:
            os.remove(config_path)
        except:
            raise Exception("problem doesn't exist")


class WorkerAgent:
    '''
    Agent scheduling worker processes
    '''
    def __init__(self, n_worker, mode):
        '''
        Input:
            n_worker: max number of workers running in parallel
            mode: 'manual' will only launch worker once when required, 'auto' will launch worker automatically if previously launched worker ends
        '''
        assert n_worker > 0
        self.n_worker = n_worker

        assert mode in ['manual', 'auto']
        self.mode = mode

        self.workers_run = [] # active workers
        self.workers_wait = [] # pending workers
        self.worker_id = -1
        self.worker_cmd = None # command (function) that generates a worker
        self.stopped = False
        
        self.lock_worker = Lock()
        self.lock_log = Lock()
        
        self.logs = [] # for recording scheduling history

    def _start_worker(self, worker):
        worker.start()
        self.worker_id += 1
        self.workers_run.append([self.worker_id, worker])
        self._add_log(f'worker {self.worker_id} started')

    def add_worker(self, target, args):
        '''
        Add worker process
        Input:
            target: function that worker needs to execute
            args: arguments to the target function
        '''
        self.worker_cmd = lambda: Process(target=target, args=args)
        worker = self.worker_cmd()
        with self.lock_worker:
            if len(self.workers_run) < self.n_worker:
                self._start_worker(worker)
            else:
                self.workers_wait.append(worker)
        self.stopped = False

    def stop_worker(self, worker_id=None):
        '''
        Stop the running worker(s)
        Input:
            worker_id: the id of worker to be stopped, if None then stop all the workers
        '''
        with self.lock_worker:
            stopped = []

            # check for workers to stop
            for w in self.workers_run:
                wid, worker = w
                if (worker_id is None or wid == worker_id) and worker.is_alive():
                    worker.terminate()
                    stopped.append(w)
                    self._add_log(f'worker {wid} stopped')
                    if worker_id is not None:
                        break
            
            # remove stopped workers
            for w in stopped:
                self.workers_run.remove(w)
            
            # stop waiting workers
            if worker_id is None:
                self.workers_wait = []
                self.stopped = True

    def refresh(self):
        '''
        Refresh the status of running/waiting workers, launch workers if in auto mode, need to be called periodically
        '''
        with self.lock_worker:
            completed = []

            # check for completed workers
            for w in self.workers_run:
                wid, worker = w
                if not worker.is_alive():
                    completed.append(w)
                    self._add_log(f'worker {wid} completed')
            
            # remove completed workers
            for w in completed:
                self.workers_run.remove(w)

            # launch waiting workers
            while len(self.workers_run) < self.n_worker and len(self.workers_wait) > 0:
                self._start_worker(self.workers_wait.pop(0))

            # automatically launch new workers
            if self.mode == 'auto' and not self.stopped:
                while len(self.workers_run) < self.n_worker:
                    self._start_worker(self.worker_cmd())

    def empty(self):
        '''
        Check if there are running workers
        '''
        return len(self.workers_run) == 0

    def full(self):
        '''
        Check if number of running workers reaches maximum
        '''
        return len(self.workers_run) == self.n_worker

    def set_n_worker(self, n_worker):
        assert n_worker > 0
        self.n_worker = n_worker

    def set_mode(self, mode):
        assert mode in ['manual', 'auto']
        self.mode = mode

    def _add_log(self, log):
        with self.lock_log:
            self.logs.append(log)

    def read_log(self):
        '''
        Read and clear logs
        '''
        with self.lock_log:
            logs = self.logs.copy()
            self.logs = []
        return logs

    def quit(self):
        self.stop_worker()