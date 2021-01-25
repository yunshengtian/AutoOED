from multiprocessing import Process, Queue, Lock

from system.utils.process_safe import process_safe_func


class WorkerAgent:
    '''
    Agent scheduling optimization & evaluation worker processes
    '''
    def __init__(self, data_agent):
        self.data_agent = data_agent
        self.mode = 'manual'
        self.config = None
        self.config_id = -1
        self.eval = True

        self.opt_workers_run = [] # active optimization workers
        self.opt_workers_wait = [] # pending optimization workers
        self.opt_worker_id = 0
        self.opt_worker_cmd = None # command (function) that generates an optimization worker

        self.eval_workers_run = [] # active optimization workers
        self.eval_workers_wait = [] # pending optimization workers
        self.eval_worker_id = 0
        self.eval_worker_cmd = None # command (function) that generates an evaluation worker

        self.stopped = False # whether is stopped by user

        self.queue = Queue()
        
        self.lock_opt_worker = Lock()
        self.lock_eval_worker = Lock()
        self.lock_log = Lock()
        
        self.logs = [] # for recording scheduling history

    def configure(self, mode=None, config=None, config_id=None, eval=None):
        '''
        Set configurations, a required step before starting any worker
        Input:
            mode: 'manual' will only launch worker once when required, 'auto' will launch worker automatically if previously launched worker ends
            eval: whether the problem's evaluation function is defined
        '''
        if mode is not None:
            self.set_mode(mode)
        if config is not None and config_id is not None:
            self.set_config(config, config_id)
        if eval is not None:
            self.eval = eval

    def set_mode(self, mode):
        assert mode in ['manual', 'auto'], 'invalid mode'
        assert self.eval or mode == 'auto', 'auto mode is invalid when evaluation function is not defined'
        self.mode = mode

    def set_config(self, config, config_id):
        '''
        Required to set correct configurations before optimization / evaluation
        '''
        self.config = config.copy()
        self.config_id = config_id

    def _start_opt_worker(self):
        '''
        Start an optimization worker
        '''
        if len(self.opt_workers_wait) == 0: return False
        worker, n_iter, curr_iter = self.opt_workers_wait.pop(0)
        curr_iter += 1
        if curr_iter > n_iter: return False
        worker.start()
        self.opt_worker_id += 1
        self.opt_workers_run.append([self.opt_worker_id, worker, n_iter, curr_iter])
        self._add_log(f'optimization worker {self.opt_worker_id} started')
        if self.eval:
            self._queue_opt_worker(n_iter, curr_iter) # NOTE: only queue next iteration's optimization worker if evaluation function is defined
        return True

    def _start_eval_worker(self):
        '''
        Start an evaluation worker
        '''
        if len(self.eval_workers_run) >= self.config['experiment']['n_worker'] or len(self.eval_workers_wait) == 0: return False
        worker, rowid = self.eval_workers_wait.pop(0)
        worker.start()
        self.eval_worker_id += 1
        self.eval_workers_run.append([self.eval_worker_id, worker, rowid])
        self._add_log(f'evaluation worker {self.eval_worker_id} started' + f'/{rowid}') # NOTE: for passing rowid to gui for updating status
        return True
        
    def _queue_opt_worker(self, n_iter, curr_iter):
        '''
        Queue an optimization worker
        '''
        worker = self.opt_worker_cmd()
        self.opt_workers_wait.append([worker, n_iter, curr_iter])

    def add_opt_worker(self):
        '''
        Add an optimization worker process
        '''
        n_iter = self.config['experiment']['n_iter']
        self.opt_worker_cmd = lambda: Process(target=process_safe_func, args=(self.data_agent.optimize, self.config, self.config_id, self.queue))
        with self.lock_opt_worker:
            self._queue_opt_worker(n_iter, 0)
            self._start_opt_worker()
        self.stopped = False

    def add_eval_worker(self, rowid):
        '''
        Add an evaluation worker process
        '''
        if not self.eval: return # TODO: check
        worker = Process(target=process_safe_func, args=(self.data_agent.evaluate, self.config, rowid))
        with self.lock_eval_worker:
            self.eval_workers_wait.append([worker, rowid])
            self._start_eval_worker()
        self.stopped = False

    def stop_opt_worker(self, worker_id=None):
        '''
        Stop the running optimization worker(s)
        Input:
            worker_id: the id of worker to be stopped, if None then stop all the workers
        '''
        with self.lock_opt_worker:
            for w in self.opt_workers_run:
                wid, worker, _, _ = w
                if (worker_id is None or wid == worker_id) and worker.is_alive():
                    worker.terminate()
                    self._add_log(f'optimization worker {wid} stopped')
                    if worker_id is not None:
                        self.opt_workers_run.remove(w)
                        break
            if worker_id is None:
                self.opt_workers_run = []
                self.opt_workers_wait = []

    def stop_eval_worker(self, worker_id=None, row_id=None):
        '''
        Stop the running evaluation worker(s)
        Input:
            worker_id: the id of worker to be stopped
            row_id: the id of row to be stopped
            (if both are None then stop all workers)
        '''
        stop_all = worker_id is None and row_id is None
        with self.lock_eval_worker:
            for w in self.eval_workers_run:
                wid, worker, rowid = w
                if (stop_all or wid == worker_id or rowid == row_id) and worker.is_alive():
                    worker.terminate()
                    self._add_log(f'evaluation worker {wid} stopped' + f'/{rowid}')
                    if worker_id is not None:
                        self.eval_workers_run.remove(w)
                        break
            if stop_all:
                self.eval_workers_run = []
                self.eval_workers_wait = []

    def stop_worker(self):
        '''
        Stop all the optimization and evaluation workers
        '''
        self.stop_opt_worker()
        self.stop_eval_worker()
        self.stopped = True

    def refresh(self):
        '''
        Refresh the status of running/waiting workers, launch workers if in auto mode, need to be called periodically
        '''
        if self.eval:
            with self.lock_eval_worker:
                completed_eval = []

                # check for completed evaluation workers
                for w in self.eval_workers_run:
                    wid, worker, rowid = w
                    if not worker.is_alive():
                        completed_eval.append(w)
                        self._add_log(f'evaluation worker {wid} completed' + f'/{rowid}')
                
                # remove completed evaluation workers
                for w in completed_eval:
                    self.eval_workers_run.remove(w)

                # launch waiting evaluation workers
                while self._start_eval_worker():
                    pass

        with self.lock_opt_worker:
            completed_opt = []

            # check for completed optimization workers
            for w in self.opt_workers_run:
                wid, worker, _, _ = w
                if not worker.is_alive():
                    completed_opt.append(w)
                    self._add_log(f'optimization worker {wid} completed')
            
            # remove completed optimization workers
            for w in completed_opt:
                self.opt_workers_run.remove(w)

            # launch evaluation workers for completed optimization workers
            for _ in completed_opt:
                rowids = self.queue.get()
                for rowid in rowids:
                    self.add_eval_worker(rowid)

            # launch optimization workers if all iterations are not finished
            for _ in completed_opt:
                self._start_opt_worker()

            # launch new optimization workers in auto mode
            if self.mode == 'auto' and not self.stopped and self.eval:
                while len(self.opt_workers_run) * self.config['experiment']['batch_size'] < self.config['experiment']['n_worker'] - len(self.eval_workers_run):
                    self._queue_opt_worker(1, 0)
                    self._start_opt_worker()

    def empty(self):
        '''
        Check if there are running optimization or evaluation workers
        '''
        return len(self.opt_workers_run) == 0 and len(self.eval_workers_run) == 0

    def full(self):
        '''
        Check if number of running evaluation workers reaches maximum
        '''
        return len(self.eval_workers_run) == self.config['experiment']['n_worker']

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
