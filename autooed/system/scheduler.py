'''
Schedulers for scheduling evaluation and optimization in a parallel scenario.
'''

import numpy as np
from multiprocessing import Process, Queue

from autooed.problem import build_problem, get_problem_config
from autooed.utils.initialization import get_initial_samples


class Logger:
    '''
    Logger that records the status change of evaluation and optimization.
    '''
    def __init__(self):
        self.logs = []

    def add(self, log):
        '''
        Add log.

        Parameters
        ----------
        log: str
            Text to log.
        '''
        self.logs.append(log)

    def read(self, clear=True):
        '''
        Read and clear logs

        Parameters
        ----------
        clear: bool
            Whether to clear existing logs.

        Returns
        -------
        logs: list
            List of logs since last read.
        '''
        logs = self.logs.copy()
        if clear:
            self.logs = []
        return logs


class EvaluateScheduler:
    '''
    Scheduler for evaluation.
    '''
    def __init__(self, agent):
        '''
        Parameters
        ----------
        agent: autooed.system.agent.LoadAgent
            Agent that talks to algorithms and database.
        '''
        self.agent = agent
        self.logger = Logger()

        self.eval_workers_run = []
        self.eval_workers_wait = []

        self.n_worker = 0

    def evaluate(self, eval_func, rowids, n_worker):
        '''
        Evaluate certain rows of data.

        Parameters
        ----------
        eval_func: function
            Provided evaluation function.
        rowids: list
            Row numbers of data to evaluate.
        n_worker: int
            Number of evaluation workers that can evaluatein parallel.
        '''
        if not (self.agent.can_eval or eval_func is not None): return
        self.n_worker = n_worker
        for rowid in rowids:
            worker = Process(target=self.agent.evaluate, args=(rowid, eval_func))
            self.eval_workers_wait.append([worker, rowid])

    def is_evaluating(self):
        '''
        Check if any evaluation worker is running.
        '''
        return self.eval_workers_run != [] or self.eval_workers_wait != []

    def _refresh_evaluate(self):
        '''
        Refresh evaluation status.

        Returns
        -------
        bool
            Whether ongoing evaluations have finished.
        '''
        completed_workers = []

        # check if eval workers finished
        for worker_info in self.eval_workers_run:
            eval_worker, rowid = worker_info
            if not eval_worker.is_alive():
                self.logger.add(f'evaluation for row {rowid} finished')
                completed_workers.append(worker_info)

        for worker_info in completed_workers:
            self.eval_workers_run.remove(worker_info)
        
        # launch waiting eval workers
        while len(self.eval_workers_run) < self.n_worker and self.eval_workers_wait != []:
            worker, rowid = self.eval_workers_wait.pop(0)
            worker.start()
            self.logger.add(f'evaluation for row {rowid} started')
            self.eval_workers_run.append([worker, rowid])

        eval_finished = len(completed_workers) > 0 and self.eval_workers_run == []
        return eval_finished

    def refresh(self):
        '''
        Refresh evaluation status.
        '''
        eval_finished = self._refresh_evaluate()

    def stop_evaluate(self, rowid=None):
        '''
        Stop the running evaluation worker(s).
        
        Parameters
        ----------
        rowid: int
            Row number of the evaluation to stop (if None then stop all evaluations)
        '''
        stop_all = rowid is None
        worker_run_stopped = None
        worker_wait_stopped = None

        # stop running workers
        for worker_info in self.eval_workers_run:
            worker, rowid_ = worker_info
            if (stop_all or rowid_ == rowid) and worker.is_alive():
                worker.terminate()
                self.logger.add(f'evaluation for row {rowid_} stopped')
                if not stop_all:
                    worker_run_stopped = worker_info
                    break
        
        # stop waiting workers
        for worker_info in self.eval_workers_wait:
            worker, rowid_ = worker_info
            if not stop_all and rowid_ == rowid:
                worker_wait_stopped = worker_info
                break
        
        if stop_all:
            self.eval_workers_run = []
            self.eval_workers_wait = []
        else:
            if worker_run_stopped is not None:
                self.eval_workers_run.remove(worker_run_stopped)
            if worker_wait_stopped is not None:
                self.eval_workers_wait.remove(worker_wait_stopped)

    def quit(self):
        '''
        Quit the scheduler.
        '''
        self.stop_evaluate()


class OptimizeScheduler:
    '''
    Scheduler for evaluation and optimization.
    '''
    def __init__(self, agent):
        '''
        Parameters
        ----------
        agent: autooed.system.agent.LoadAgent
            Agent that talks to algorithms and database.
        '''
        self.agent = agent
        self.logger = Logger()

        self.opt_workers = []
        self.opt_queue = Queue()
        self.n_optimizing_sample = 0
        self.pred_workers = []
        self.eval_workers_manual_run = []
        self.eval_workers_manual_wait = []
        self.eval_workers_auto_run = []
        self.eval_workers_auto_wait = []

        self.initializing = False

        self.config = None
        self.stop_criterion = []
        self.auto_scheduling = False

    def set_config(self, config):
        '''
        Set config, update agent's config and start initialization if available.
        '''
        if not self.agent.check_table_exist() and not self.initializing: # check if initializing

            problem = build_problem(config['problem']['name'])
            n_random_sample, init_sample_path = config['experiment']['n_random_sample'], config['experiment']['init_sample_path']
            X_init_evaluated, X_init_unevaluated, Y_init_evaluated = get_initial_samples(problem, n_random_sample, init_sample_path)

            self.initializing = True

            self.config = config.copy()
            self.agent.set_config(self.config)

            rowids_unevaluated = self.agent.initialize(X_init_evaluated, X_init_unevaluated, Y_init_evaluated)
            if rowids_unevaluated is not None:
                self.evaluate_manual(rowids_unevaluated)
        else:
            self.config = config.copy()
            self.agent.set_config(self.config)

    def _optimize(self, batch_size=None):
        '''
        Launch an optimization worker.
        '''
        if not self.agent.check_initialized():
            raise Exception('initialization has not finished')
        self.logger.add(f'optimization started')
        worker = Process(target=self.agent.optimize, args=(self.opt_queue, batch_size))
        worker.start()
        self.opt_workers.append(worker)
        
        if batch_size is None:
            self.n_optimizing_sample += self.config['experiment']['batch_size']
        else:
            self.n_optimizing_sample += batch_size

    def optimize_manual(self):
        '''
        Optimize in manual mode.
        '''
        self._optimize()

    def optimize_auto(self, stop_criterion=[]):
        '''
        Optimize in auto mode.
        
        Parameters
        ----------
        stop_criterion: list
            List of stop criteria for optimization.
        '''
        assert self.agent.can_eval, 'evaluation function is not provided, cannot use auto mode'
        self.auto_scheduling = True
        self.stop_criterion = stop_criterion
        for criterion in self.stop_criterion:
            criterion.start()
        self._optimize()

    def predict(self, rowids):
        '''
        Predict the performance of given row numbers.

        Parameters
        ----------
        rowids: list
            Row numbers of the data to predict.
        '''
        self.logger.add(f'prediction for row {",".join([str(r) for r in rowids])} started')
        worker = Process(target=self.agent.predict, args=(rowids,))
        worker.start()
        self.pred_workers.append([worker, rowids])

    def evaluate_manual(self, rowids):
        '''
        Evaluate the performance of given row numbers in manual mode.

        Parameters
        ----------
        rowids: list
            Row numbers of the data to evaluate.
        '''
        if not self.agent.can_eval: return
        for rowid in rowids:
            worker = Process(target=self.agent.evaluate, args=(rowid,))
            self.eval_workers_manual_wait.append([worker, rowid])

    def evaluate_auto(self, rowids):
        '''
        Evaluate the performance of given row numbers in auto mode.

        Parameters
        ----------
        rowids: list
            Row numbers of the data to evaluate.
        '''
        if not self.agent.can_eval: return
        for rowid in rowids:
            worker = Process(target=self.agent.evaluate, args=(rowid,))
            self.eval_workers_auto_wait.append([worker, rowid])

    def is_optimizing(self):
        '''
        Check if any optimization worker is running.
        '''
        return self.opt_workers != []

    def is_predicting(self):
        '''
        Check if any prediction worker is running.
        '''
        return self.pred_workers != []

    def is_evaluating_manual(self):
        '''
        Check if any manual evaluation worker is running.
        '''
        return self.eval_workers_manual_run != [] or self.eval_workers_manual_wait != []

    def is_evaluating_auto(self):
        '''
        Check if any auto evaluation worker is running.
        '''
        return self.eval_workers_auto_run != [] or self.eval_workers_auto_wait != []

    def is_evaluating(self):
        '''
        Check if any evaluation worker is running.
        '''
        return self.is_evaluating_manual() or self.is_evaluating_auto()

    def is_working(self):
        '''
        Check if any worker is running.
        '''
        return self.is_optimizing() or self.is_predicting() and self.is_evaluating()

    def _refresh_optimize(self):
        '''
        Refresh optimization status.

        Returns
        -------
        rowids: list
            Row numbers of the data where ongoing optimizations have finished.
        '''
        completed_workers = []
        rowids_list = []

        for worker in self.opt_workers:
            if not worker.is_alive():
                try:
                    rowids = self.opt_queue.get(block=False)
                except:
                    raise Exception('optimization worker finished without returning rowids of the design to evaluate')
                rowids_list.append(rowids)
                self.logger.add(f'optimization for row {",".join([str(r) for r in rowids])} finished')
                completed_workers.append(worker)
                self.n_optimizing_sample -= len(rowids)
                assert self.n_optimizing_sample >= 0, 'error in counting designs being optimized'

        for worker in completed_workers:
            self.opt_workers.remove(worker)

        if rowids_list != []:
            rowids_list = np.concatenate(rowids_list).tolist()

        return rowids_list

    def _refresh_predict(self):
        '''
        Refresh prediction status.

        Returns
        -------
        bool
            Whether ongoing predictions have finished.
        '''
        completed_workers = []

        for worker_info in self.pred_workers:
            pred_worker, rowids = worker_info
            if not pred_worker.is_alive():
                self.logger.add(f'prediction for row {",".join([str(r) for r in rowids])} finished')
                completed_workers.append(worker_info)

        for worker_info in completed_workers:
            self.pred_workers.remove(worker_info)

        pred_finished = len(completed_workers) > 0
        return pred_finished

    def _refresh_evaluate(self):
        '''
        Refresh evaluation status.

        Returns
        -------
        bool
            Whether ongoing manual evaluations have finished.
        bool
            Whether ongoing auto evaluations have finished.
        '''
        completed_workers_manual, completed_workers_auto = [], []

        # check if manual eval workers finished
        for worker_info in self.eval_workers_manual_run:
            eval_worker, rowid = worker_info
            if not eval_worker.is_alive():
                self.logger.add(f'evaluation for row {rowid} finished')
                completed_workers_manual.append(worker_info)

        for worker_info in completed_workers_manual:
            self.eval_workers_manual_run.remove(worker_info)
        
        # check if auto eval workers finished
        for worker_info in self.eval_workers_auto_run:
            eval_worker, rowid = worker_info
            if not eval_worker.is_alive():
                self.logger.add(f'evaluation for row {rowid} finished')
                completed_workers_auto.append(worker_info)

        for worker_info in completed_workers_auto:
            self.eval_workers_auto_run.remove(worker_info)

        # launch waiting manual eval workers
        while len(self.eval_workers_manual_run) + len(self.eval_workers_auto_run) < self.config['experiment']['n_worker'] and self.eval_workers_manual_wait != []:
            worker, rowid = self.eval_workers_manual_wait.pop(0)
            worker.start()
            self.logger.add(f'evaluation for row {rowid} started')
            self.eval_workers_manual_run.append([worker, rowid])

        # launch waiting auto eval workers
        while len(self.eval_workers_manual_run) + len(self.eval_workers_auto_run) < self.config['experiment']['n_worker'] and self.eval_workers_auto_wait != []:
            worker, rowid = self.eval_workers_auto_wait.pop(0)
            worker.start()
            self.logger.add(f'evaluation for row {rowid} started')
            self.eval_workers_auto_run.append([worker, rowid])

        eval_manual_finished = len(completed_workers_manual) > 0
        eval_auto_finished = len(completed_workers_auto) > 0
        return eval_manual_finished, eval_auto_finished

    def refresh(self):
        '''
        Refresh optimization, prediction and evaluation status.
        '''
        opt_rowids = self._refresh_optimize()
        opt_finished = opt_rowids != []
        pred_finished = self._refresh_predict()
        eval_manual_finished, eval_auto_finished = self._refresh_evaluate()

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
                n_running_eval_workers = len(self.eval_workers_manual_run) + len(self.eval_workers_auto_run)
                batch_size = self.config['experiment']['batch_size'] - n_running_eval_workers - self.n_optimizing_sample
                if batch_size > 0:
                    self._optimize(batch_size=batch_size)
                elif batch_size == 0:
                    pass
                else:
                    raise Exception('number of running evaluation workers exceeds the maximum set')
            else:
                self.logger.add('stopping criterion met')

    def stop_optimize(self):
        '''
        Stop the running optimization worker.
        '''
        self.auto_scheduling = False

        for worker in self.opt_workers:
            if worker.is_alive():
                worker.terminate()
                self.logger.add(f'optimization stopped')

        self.opt_workers = []
        self.n_optimizing_sample = 0

    def stop_predict(self):
        '''
        Stop the running prediction worker(s).
        '''
        for worker_info in self.pred_workers:
            worker, rowids = worker_info
            if worker.is_alive():
                worker.terminate()
                self.logger.add(f'prediction for row {",".join(rowids)} stopped')

        self.pred_workers = []

    def stop_evaluate_manual(self, rowid=None):
        '''
        Stop the running manual evaluation worker(s).
        
        Parameters
        ----------
        rowid: list
            Row numbers of the manual evaluations to be stopped (if None then stop all manual workers).
        '''
        stop_all = rowid is None
        worker_run_stopped = None
        worker_wait_stopped = None

        # stop running workers
        for worker_info in self.eval_workers_manual_run:
            worker, rowid_ = worker_info
            if (stop_all or rowid_ == rowid) and worker.is_alive():
                worker.terminate()
                self.logger.add(f'evaluation for row {rowid_} stopped')
                if not stop_all:
                    worker_run_stopped = worker_info
                    break
        
        # stop waiting workers
        for worker_info in self.eval_workers_manual_wait:
            worker, rowid_ = worker_info
            if not stop_all and rowid_ == rowid:
                worker_wait_stopped = worker_info
                break
        
        if stop_all:
            self.eval_workers_manual_run = []
            self.eval_workers_manual_wait = []
        else:
            if worker_run_stopped is not None:
                self.eval_workers_manual_run.remove(worker_run_stopped)
            if worker_wait_stopped is not None:
                self.eval_workers_manual_wait.remove(worker_wait_stopped)

    def stop_evaluate_auto(self, rowid=None):
        '''
        Stop the running auto evaluation worker(s).
        
        Parameters
        ----------
        rowid: list
            Row numbers of the auto evaluations to be stopped (if None then stop all auto workers).
        '''
        self.auto_scheduling = False

        stop_all = rowid is None
        worker_run_stopped = None
        worker_wait_stopped = None

        # stop running workers
        for worker_info in self.eval_workers_auto_run:
            worker, rowid_ = worker_info
            if (stop_all or rowid_ == rowid) and worker.is_alive():
                worker.terminate()
                self.logger.add(f'evaluation for row {rowid_} stopped')
                if not stop_all:
                    worker_run_stopped = worker_info
                    break
        
        # stop waiting workers
        for worker_info in self.eval_workers_auto_wait:
            worker, rowid_ = worker_info
            if not stop_all and rowid_ == rowid:
                worker_wait_stopped = worker_info
                break
        
        if stop_all:
            self.eval_workers_auto_run = []
            self.eval_workers_auto_wait = []
        else:
            if worker_run_stopped is not None:
                self.eval_workers_auto_run.remove(worker_run_stopped)
            if worker_wait_stopped is not None:
                self.eval_workers_auto_wait.remove(worker_wait_stopped)

    def stop_evaluate(self, rowid=None):
        '''
        Stop the running evaluation worker(s).
        
        Parameters
        ----------
        rowid: list
            Row numbers of the evaluations to be stopped (if None then stop all workers).
        '''
        self.stop_evaluate_manual(rowid=rowid)
        self.stop_evaluate_auto(rowid=rowid)

    def stop_all(self):
        '''
        Stop all workers.
        '''
        self.stop_optimize()
        self.stop_predict()
        self.stop_evaluate()

    def quit(self):
        '''
        Quit the scheduler.
        '''
        self.stop_all()
