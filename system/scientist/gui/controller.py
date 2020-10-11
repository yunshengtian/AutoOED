import os
import yaml
from time import time, sleep
from datetime import datetime
import numpy as np

from config.utils import load_config, process_config
from problem.common import build_problem, get_initial_samples
from problem.problem import Problem

import tkinter as tk
from system.scientist.gui.view import View
from system.server.agent import DataAgent, WorkerAgent
from system.scientist.gui.params import *

from system.scientist.gui.menu_file import FileController
from system.scientist.gui.menu_config import ConfigController
from system.scientist.gui.menu_problem import ProblemController
from system.scientist.gui.panel_control import ControlController
from system.scientist.gui.panel_log import LogController
from system.scientist.gui.viz_space import SpaceController
from system.scientist.gui.viz_stats import StatsController
from system.scientist.gui.viz_database import DatabaseController


class ScientistController:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('OpenMOBO - Scientist')
        self.root.protocol('WM_DELETE_WINDOW', self._quit)

        self.refresh_rate = REFRESH_RATE # ms
        self.result_dir = RESULT_DIR # initial result directory
        self.config = None
        self.config_raw = None
        self.config_id = -1
        self.problem_cfg = None
        self.timestamp = None

        self.data_agent = DataAgent()
        self.worker_agent = WorkerAgent(self.data_agent)

        self.true_pfront = None

        self.n_sample = None
        self.n_valid_sample = None

        self.view = View(self.root)
        self.controller = {}

        self._init_menu()
        self._init_panel()
    
    def _init_menu(self):
        '''
        Menu initialization
        '''
        self.controller['file'] = FileController(self)
        self.view.menu_file.entryconfig(0, command=self.controller['file'].set_result_dir)

        self.controller['config'] = ConfigController(self)
        self.view.menu_config.entryconfig(0, command=self.controller['config'].load_config_from_file)
        self.view.menu_config.entryconfig(1, command=self.controller['config'].create_config)
        self.view.menu_config.entryconfig(2, command=self.controller['config'].change_config, state=tk.DISABLED)

        self.controller['problem'] = ProblemController(self)
        self.view.menu_problem.entryconfig(0, command=self.controller['problem'].manage_problem)

    def _init_panel(self):
        '''
        Panel initialization
        '''
        self.controller['control'] = ControlController(self)
        self.controller['log'] = LogController(self)

    def _init_visualization(self):
        '''
        Visualization initialization
        '''
        self.controller['space'] = SpaceController(self)
        self.controller['stats'] = StatsController(self)
        self.controller['database'] = DatabaseController(self)
        self.view.activate_viz()

    def get_config(self):
        return self.config

    def get_config_id(self):
        return self.config_id

    def get_problem_cfg(self):
        return self.problem_cfg

    def set_config(self, config, window=None):
        '''
        Setting configurations
        '''
        # set parent window for displaying potential error messagebox
        if window is None: window = self.root

        try:
            config = process_config(config)
        except Exception as e:
            tk.messagebox.showinfo('Error', 'Invalid configurations: ' + str(e), parent=window)
            return False

        # update raw config (config will be processed and changed later)
        self.config_raw = config.copy()
        
        old_config = None if self.config is None else self.config.copy()

        if self.config is None: # first time setting config
            # create directory for saving results
            if not self.create_result_dir(window):
                return False

            # initialize problem
            try:
                problem, self.true_pfront = build_problem(config['problem'], get_pfront=True)
            except Exception as e:
                tk.messagebox.showinfo('Error', 'Invalid values in configuration: ' + str(e), parent=window)
                return False

            # update config
            self.config = config
            self.problem_cfg = problem.get_config(
                var_lb=config['problem']['var_lb'],
                var_ub=config['problem']['var_ub'],
                obj_lb=config['problem']['obj_lb'],
                obj_ub=config['problem']['obj_ub'],
            )

            # remove tutorial image
            self.view.image_tutorial.destroy()

            # TODO: give hint of initializing

            # configure agents
            self.data_agent.configure(db_dir=self.result_dir, n_var=problem.n_var, n_obj=problem.n_obj, minimize=problem.minimize)
            self.data_agent.initialize_db()
            self.worker_agent.configure(mode='manual', config=config, config_id=0, eval=hasattr(problem, 'evaluate_performance'))

            # data initialization
            X_init_evaluated, X_init_unevaluated, Y_init_evaluated = get_initial_samples(config['problem'], problem)
            if X_init_evaluated is not None:
                self.data_agent.initialize_data(X_init_evaluated, Y_init_evaluated)
            if X_init_unevaluated is not None:
                rowids = self.data_agent.initialize_data(X_init_unevaluated)
                for rowid in rowids:
                    self.worker_agent.add_eval_worker(rowid)
                
                # wait until initialization is completed
                while not self.worker_agent.empty():
                    self.worker_agent.refresh()
                    sleep(self.refresh_rate / 1000.0)

            # calculate reference point
            if self.config['problem']['ref_point'] is None:
                Y = self.data_agent.load('Y')
                ref_point = np.zeros(problem.n_obj)
                for i, m in enumerate(problem.minimize):
                    if m == True:
                        ref_point[i] = np.max(Y[:, i])
                    else:
                        ref_point[i] = np.min(Y[:, i])
                self.config['problem']['ref_point'] = ref_point

            # initialize visualization widgets
            self._init_visualization()

            # disable changing saving location
            self.view.menu_file.entryconfig(0, state=tk.DISABLED)

            # change config create/change status
            self.view.menu_config.entryconfig(1, state=tk.DISABLED)
            self.view.menu_config.entryconfig(2, state=tk.NORMAL)

            # activate widgets
            entry_mode = self.controller['control'].view.widget['mode']
            entry_mode.enable(readonly=False)
            entry_mode.set('manual')
            entry_mode.enable(readonly=True)

            entry_batch_size = self.controller['control'].view.widget['batch_size']
            entry_batch_size.enable()
            try:
                entry_batch_size.set(self.config['general']['batch_size'])
            except:
                entry_batch_size.set(5)

            entry_n_iter = self.controller['control'].view.widget['n_iter']
            entry_n_iter.enable()
            try:
                entry_n_iter.set(self.config['general']['n_iter'])
            except:
                entry_n_iter.set(1)

            self.controller['control'].view.widget['optimize'].enable()
            self.controller['control'].view.widget['set_stop_cri'].enable()

            self.controller['log'].view.widget['clear'].enable()

            # trigger periodic refresh
            self.root.after(self.refresh_rate, self.refresh)

        else: # user changed config in the middle
            try:
                # some keys cannot be changed
                unchanged_keys = ['name', 'n_init_sample', 'init_sample_path']
                if self.config_raw['problem']['ref_point'] is not None:
                    unchanged_keys.append('ref_point')
                for key in unchanged_keys:
                    assert (np.array(self.config_raw['problem'][key]) == np.array(config['problem'][key])).all()
            except:
                tk.messagebox.showinfo('Error', 'Invalid configuration values for reloading', parent=window)
                return False

            self.config = config
            self.problem_cfg = Problem.process_config(
                self.problem_cfg,
                var_lb=config['problem']['var_lb'],
                var_ub=config['problem']['var_ub'],
                obj_lb=config['problem']['obj_lb'],
                obj_ub=config['problem']['obj_ub'],
            )
        
        if self.config != old_config:
            self.save_config(self.config)
            self.worker_agent.set_config(self.config, self.config_id)
            self.controller['space'].set_config(self.config, self.problem_cfg)
            self.controller['stats'].set_config(self.config, self.problem_cfg)

        return True

    def save_config(self, config):
        '''
        Save configurations to file
        '''
        self.config_id += 1
        with open(os.path.join(self.result_dir, 'config', f'config_{self.config_id}.yml'), 'w') as fp:
            yaml.dump(config, fp, default_flow_style=False, sort_keys=False)

    def get_timestamp(self):
        return self.timestamp

    def set_timestamp(self):
        self.timestamp = time()

    def set_result_dir(self, result_dir):
        self.result_dir = result_dir

    def create_result_dir(self, window):
        # check if result_dir folder is not empty
        if os.path.exists(self.result_dir) and os.listdir(self.result_dir) != []:
            tk.messagebox.showinfo('Error', f'Result folder {self.result_dir} is not empty, please change another folder for saving results by clicking: File -> Save in...', parent=window)
            return False
        os.makedirs(self.result_dir, exist_ok=True)
        config_dir = os.path.join(self.result_dir, 'config')
        os.makedirs(config_dir)
        return True

    def refresh(self):
        '''
        Refresh current GUI status and redraw if data has changed
        '''
        self.worker_agent.refresh()
        
        # can optimize and load config when worker agent is empty
        if self.worker_agent.empty():
            self.controller['control'].view.widget['mode'].enable()
            self.controller['control'].view.widget['optimize'].enable()
            self.controller['control'].view.widget['stop'].disable()
            if self.view.menu_config.entrycget(0, 'state') == tk.DISABLED:
                self.view.menu_config.entryconfig(0, state=tk.NORMAL)
            if self.view.menu_config.entrycget(2, 'state') == tk.DISABLED:
                self.view.menu_config.entryconfig(2, state=tk.NORMAL)

        # post-process worker logs
        log_list = []
        status, rowids = [], []
        evaluated = False
        for log in self.worker_agent.read_log():
            log = log.split('/') 
            log_text = datetime.now().strftime('%Y-%m-%d %H:%M:%S\n') + log[0] + '\n'
            log_list.append(log_text)

            if 'evaluation' not in log_text: continue

            # evaluation worker log, update database table status
            if len(log) > 1:
                rowid = int(log[1])
                if 'started' in log_text:
                    status.append('evaluating')
                elif 'stopped' in log_text:
                    status.append('unevaluated')
                elif 'completed' in log_text:
                    status.append('evaluated')
                    evaluated = True
                else:
                    raise NotImplementedError
                rowids.append(rowid)

        # log display
        self.controller['log'].log(log_list)

        # update visualization
        opt_done, eval_done = self.data_agent.check_opt_done(), self.data_agent.check_eval_done()

        if eval_done:
            self.controller['space'].redraw_performance_space(reset_scaler=True)
            self.controller['stats'].redraw()
        
        self.controller['database'].update_data(opt_done, eval_done)
        self.controller['database'].update_status(status, rowids)

        # check stopping criterion
        self.check_stop_criterion()
        
        # trigger another refresh
        self.root.after(self.refresh_rate, self.refresh)

    def check_stop_criterion(self):
        '''
        Check if stopping criterion is met
        '''
        stop = False
        stop_criterion = self.controller['control'].stop_criterion
        n_valid_sample = self.data_agent.get_n_valid_sample()

        for key, val in stop_criterion.items():
            if key == 'time': # optimization & evaluation time
                if time() - self.timestamp >= val:
                    stop = True
                    self.timestamp = None
            elif key == 'n_sample': # number of samples
                if n_valid_sample >= val:
                    stop = True
            elif key == 'hv_value': # hypervolume value
                if self.controller['viz'].view.line_hv.get_ydata()[-1] >= val:
                    stop = True
            elif key == 'hv_conv': # hypervolume convergence
                hv_history = self.controller['viz'].view.line_hv.get_ydata()
                checkpoint = np.clip(int(n_valid_sample * val / 100.0), 1, n_valid_sample - 1)
                if hv_history[-checkpoint] == hv_history[-1]:
                    stop = True
            else:
                raise NotImplementedError
        
        if stop:
            stop_criterion.clear()
            self.worker_agent.stop_worker()
            self.controller['log'].log('stopping criterion is met')
        
    def _quit(self):
        '''
        Quit handling
        '''
        self.data_agent.quit()
        self.worker_agent.quit()

        self.root.quit()
        self.root.destroy()

    def run(self):
        tk.mainloop()