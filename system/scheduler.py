from multiprocessing import Process, Queue
from problem.common import build_problem, get_initial_samples, get_problem_config


class Scheduler:

    def __init__(self, agent):
        self.agent = agent

        self.opt_worker = None
        self.opt_queue = Queue()
        self.pred_workers = []
        self.eval_workers_manual = []
        self.eval_workers_auto = []
        self.logs = []

        self.initialized = False
        self.agent_initializing = False

        self.config = None
        self.stop_criterion = []
        self.auto_scheduling = False

    def set_config(self, config):
        '''
        '''
        self.config = config.copy()

        if not self.initialized: # check if initialized
            self.initialized = self.agent.check_initialized()

        if not self.initialized and not self.agent_initializing: # check if initializing
            self.agent_initializing = True

            problem = build_problem(self.config['problem']['name'])
            X_init_evaluated, X_init_unevaluated, Y_init_evaluated = get_initial_samples(problem, self.config['problem']['n_random_sample'], self.config['problem']['init_sample_path'])
            rowids_unevaluated = self.agent.initialize(X_init_evaluated, X_init_unevaluated, Y_init_evaluated)
            if rowids_unevaluated is not None:
                self.evaluate_manual(rowids_unevaluated)

    def _optimize(self):
        '''
        '''
        if not self.initialized:
            raise Exception('initialization has not finished')
        assert self.opt_worker is None, 'optimization worker is running'
        self._add_log(f'optimization worker started')
        self.opt_worker = Process(target=self.agent.optimize, args=(self.config, self.opt_queue))
        self.opt_worker.start()

    def optimize_manual(self):
        '''
        '''
        self._optimize()

    def optimize_auto(self, stop_criterion=[]):
        '''
        '''
        assert self.agent.can_eval
        self.auto_scheduling = True
        self.stop_criterion = stop_criterion
        for criterion in self.stop_criterion:
            criterion.start()
        self._optimize()

    def predict(self, rowids):
        '''
        '''
        self._add_log(f'prediction worker for row {",".join([str(r) for r in rowids])} started')
        worker = Process(target=self.agent.predict, args=(self.config, rowids))
        worker.start()
        self.pred_workers.append([worker, rowids])

    def evaluate_manual(self, rowids):
        '''
        '''
        if not self.agent.can_eval: return
        self._add_log(f'evaluation worker for row {",".join([str(r) for r in rowids])} started')
        for rowid in rowids:
            worker = Process(target=self.agent.evaluate, args=(self.config, rowid))
            worker.start()
            self.eval_workers_manual.append([worker, rowid])

    def evaluate_auto(self, rowids):
        '''
        '''
        if not self.agent.can_eval: return
        self._add_log(f'evaluation worker for row {",".join([str(r) for r in rowids])} started')
        for rowid in rowids:
            worker = Process(target=self.agent.evaluate, args=(self.config, rowid))
            worker.start()
            self.eval_workers_auto.append([worker, rowid])

    def is_optimizing(self):
        '''
        '''
        return self.opt_worker is not None

    def is_predicting(self):
        '''
        '''
        return self.pred_workers != []

    def is_evaluating_manual(self):
        '''
        '''
        return self.eval_workers_manual != []

    def is_evaluating_auto(self):
        '''
        '''
        return self.eval_workers_auto != []

    def is_evaluating(self):
        '''
        '''
        return self.is_evaluating_manual() or self.is_evaluating_auto()

    def is_working(self):
        '''
        '''
        return self.is_optimizing() or self.is_predicting() and self.is_evaluating()

    def _refresh_optimize(self):
        '''
        '''
        if self.opt_worker is None: return

        rowids = None
        try:
            rowids = self.opt_queue.get(block=False)
        except:
            pass

        if rowids is not None:
            self._add_log(f'optimization worker for row {",".join([str(r) for r in rowids])} finished')
            if self.opt_worker.is_alive():
                self.opt_worker.terminate()
            self.opt_worker = None

        return rowids

    def _refresh_predict(self):
        '''
        '''
        completed_workers = []

        for worker_info in self.pred_workers:
            pred_worker, rowids = worker_info
            if not pred_worker.is_alive():
                self._add_log(f'prediction worker for row {",".join([str(r) for r in rowids])} finished')
                completed_workers.append(worker_info)

        for worker_info in completed_workers:
            self.pred_workers.remove(worker_info)

        return len(completed_workers) > 0

    def _refresh_evaluate(self):
        '''
        '''
        completed_workers_manual, completed_workers_auto = [], []

        for worker_info in self.eval_workers_manual:
            eval_worker, rowid = worker_info
            if not eval_worker.is_alive():
                self._add_log(f'evaluation worker for row {rowid} finished')
                completed_workers_manual.append(worker_info)
        
        for worker_info in self.eval_workers_auto:
            eval_worker, rowid = worker_info
            if not eval_worker.is_alive():
                self._add_log(f'evaluation worker for row {rowid} finished')
                completed_workers_auto.append(worker_info)

        for worker_info in completed_workers_manual:
            self.eval_workers_manual.remove(worker_info)
        
        for worker_info in completed_workers_auto:
            self.eval_workers_auto.remove(worker_info)

        return len(completed_workers_manual) > 0, len(completed_workers_auto) > 0

    def refresh(self):
        '''
        '''
        opt_rowids = self._refresh_optimize()
        opt_finished = opt_rowids is not None
        pred_finished = self._refresh_predict()
        eval_manual_finished, eval_auto_finished = self._refresh_evaluate()
        assert not (opt_finished and eval_auto_finished)

        if not self.initialized:
            self.initialized = self.agent.check_initialized()
            if self.initialized and self.agent.ref_point is None:
                self.agent.set_ref_point()

        if opt_finished:
            if self.auto_scheduling:
                self.evaluate_auto(opt_rowids)
            else:
                self.evaluate_manual(opt_rowids)

        if self.auto_scheduling and eval_auto_finished:
            for criterion in self.stop_criterion:
                stop = criterion.check()
                self.auto_scheduling = self.auto_scheduling and (not stop)

            if self.auto_scheduling:
                self._optimize()
            else:
                self._add_log('stopping criterion met')
        
    def _add_log(self, log):
        '''
        Add log
        '''
        self.logs.append(log)

    def read_log(self):
        '''
        Read and clear logs
        '''
        logs = self.logs.copy()
        self.logs = []
        return logs

    def stop_optimize(self):
        '''
        Stop the running optimization worker
        '''
        self.auto_scheduling = False

        if self.opt_worker is None: return

        if self.opt_worker.is_alive():
            self.opt_worker.terminate()

        self._add_log(f'optimization worker stopped')
        self.opt_worker = None

    def stop_predict(self):
        '''
        Stop the running prediction worker(s)
        '''
        for worker_info in self.pred_workers:
            worker, rowids = worker_info
            if worker.is_alive():
                worker.terminate()
                self._add_log(f'prediction worker for row {",".join(rowids)} stopped')

        self.pred_workers = []

    def stop_evaluate_manual(self, rowid=None):
        '''
        Stop the running evaluation worker(s)
        Input:
            rowid: the id of row to be stopped (if None then stop all workers)
        '''
        stop_all = rowid is None
        worker_stopped = None

        for worker_info in self.eval_workers_manual:
            worker, rowid_ = worker_info
            if (stop_all or rowid_ == rowid) and worker.is_alive():
                worker.terminate()
                self._add_log(f'evaluation worker for row {rowid_} stopped')
                if not stop_all:
                    worker_stopped = worker_info
                    break
        
        if stop_all:
            self.eval_workers_manual = []
        elif worker_stopped is not None:
            self.eval_workers_manual.remove(worker_stopped)

    def stop_evaluate_auto(self, rowid=None):
        '''
        Stop the running evaluation worker(s)
        Input:
            rowid: the id of row to be stopped (if None then stop all workers)
        '''
        self.auto_scheduling = False

        stop_all = rowid is None
        worker_stopped = None

        for worker_info in self.eval_workers_auto:
            worker, rowid_ = worker_info
            if (stop_all or rowid_ == rowid) and worker.is_alive():
                worker.terminate()
                self._add_log(f'evaluation worker for row {rowid_} stopped')
                if not stop_all:
                    worker_stopped = worker_info
                    break
        
        if stop_all:
            self.eval_workers_auto = []
        elif worker_stopped is not None:
            self.eval_workers_auto.remove(worker_stopped)

    def stop_evaluate(self, rowid=None):
        self.stop_evaluate_manual(rowid=rowid)
        self.stop_evaluate_auto(rowid=rowid)

    def stop_all(self):
        '''
        Stop all workers
        '''
        self.stop_optimize()
        self.stop_predict()
        self.stop_evaluate()

    def quit(self):
        self.stop_all()
