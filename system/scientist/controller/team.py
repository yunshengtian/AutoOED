import os
import shutil
import yaml
from time import time, sleep
import numpy as np
import matplotlib.pyplot as plt

from experiment.config import complete_config
from problem.common import build_problem, get_initial_samples
from problem.problem import Problem

import tkinter as tk
from tkinter import messagebox
from system.params import *
from system.database import TeamDatabase
from system.agent import DataAgent, WorkerAgent

from system.scientist.view.login import ScientistLoginView
from system.scientist.view.main import ScientistView
from system.scientist.menu import MenuConfigController, MenuProblemController, MenuDatabaseController, MenuEvalController
from system.scientist.panel import PanelInfoController, PanelControlController, PanelLogController
from system.scientist.viz import VizSpaceController, VizStatsController, VizDatabaseController


class ScientistController:

    def __init__(self):
        self.root_login = tk.Tk()
        self.root_login.title(f'{TITLE} - Scientist')
        self.root_login.protocol('WM_DELETE_WINDOW', self._quit_login)
        self.root_login.resizable(False, False)
        self.view_login = ScientistLoginView(self.root_login)
        self.bind_command_login()

        self.root = None
        self.view = None
        
        self.database = None
        self.table_name = None
        self.table_checksum = None

    def bind_command_login(self):
        '''
        '''
        self.view_login.widget['login'].configure(command=self.login_database)

    def login_database(self):
        '''
        '''
        try:
            ip = self.view_login.widget['ip'].get()
            user = self.view_login.widget['user'].get()
            passwd = self.view_login.widget['passwd'].get()
            task = self.view_login.widget['task'].get()
        except Exception as e:
            messagebox.showinfo('Error', e, parent=self.root_login)
            return

        try:
            self.database = TeamDatabase(ip, user, passwd)
        except Exception as e:
            messagebox.showinfo('Error', 'Invalid login info: ' + str(e), parent=self.root_login)
            return

        valid_login = self.database.login_verify(name=user, role='Scientist', access=task)
        if not valid_login:
            messagebox.showinfo('Error', f'Invalid access to task {task}', parent=self.root_login)
            return

        self.after_login(table_name=task)

    def _quit_login(self):
        '''
        Quit handling for login window
        '''
        self.root_login.quit()
        self.root_login.destroy()

    def after_login(self, table_name):
        '''
        '''
        self._quit_login()

        self.table_name = table_name

        self.root = tk.Tk()
        self.root.title('OpenMOBO - Scientist')
        self.root.protocol('WM_DELETE_WINDOW', self._quit)

        # TODO: use customized theme
        # from tkinter import ttk
        # from system.utils.path import get_root_dir
        # self.root.tk.call('lappend', 'auto_path', os.path.join(get_root_dir(), 'system', 'gui', 'themes'))
        # self.root.tk.call('package', 'require', 'awdark')
        # s = ttk.Style()
        # s.theme_use('awdark')

        self.refresh_rate = REFRESH_RATE # ms
        self.result_dir = RESULT_DIR # initial result directory
        self.config = None
        self.config_raw = None
        self.config_id = -1
        self.problem_cfg = None
        self.timestamp = None

        self.data_agent = DataAgent(self.database, self.table_name)
        self.worker_agent = WorkerAgent(self.data_agent)

        self.true_pfront = None

        self.n_sample = None
        self.n_valid_sample = None

        self.view = ScientistView(self.root)
        self.controller = {}

        self._init_menu()
        self._init_panel()
        config = self.database.query_config(self.table_name)
        if config is not None:
            self.set_config(config)

        self.root.mainloop()
    
    def _init_menu(self):
        '''
        Menu initialization
        '''
        self.controller['menu_config'] = MenuConfigController(self)
        self.view.menu_config.entryconfig(0, command=self.controller['menu_config'].load_config_from_file)
        self.view.menu_config.entryconfig(1, command=self.controller['menu_config'].create_config)
        self.view.menu_config.entryconfig(2, command=self.controller['menu_config'].change_config, state=tk.DISABLED)

        self.controller['menu_problem'] = MenuProblemController(self)
        self.view.menu_problem.entryconfig(0, command=self.controller['menu_problem'].manage_problem)

        self.controller['menu_database'] = MenuDatabaseController(self)
        self.view.menu_database.entryconfig(0, command=None, state=tk.DISABLED) # TODO
        self.view.menu_database.entryconfig(1, command=self.controller['menu_database'].export_csv, state=tk.DISABLED)
        self.view.menu_database.entryconfig(2, command=self.controller['menu_database'].enter_design, state=tk.DISABLED)
        self.view.menu_database.entryconfig(3, command=self.controller['menu_database'].enter_performance, state=tk.DISABLED)

        self.controller['menu_eval'] = MenuEvalController(self)
        self.view.menu_eval.entryconfig(0, command=self.controller['menu_eval'].start_local_eval, state=tk.DISABLED)
        self.view.menu_eval.entryconfig(1, command=None, state=tk.DISABLED) # TODO
        self.view.menu_eval.entryconfig(2, command=self.controller['menu_eval'].stop_eval, state=tk.DISABLED)

    def _init_panel(self):
        '''
        Panel initialization
        '''
        self.controller['panel_info'] = PanelInfoController(self)
        self.controller['panel_control'] = PanelControlController(self)
        self.controller['panel_log'] = PanelLogController(self)

    def _init_visualization(self):
        '''
        Visualization initialization
        '''
        self.controller['viz_space'] = VizSpaceController(self)
        self.controller['viz_stats'] = VizStatsController(self)
        self.controller['viz_database'] = VizDatabaseController(self)
        self.view.activate_viz()

    def _load_existing_data(self):
        '''
        '''
        # load table data
        self.controller['viz_database'].update_data()

        # load viz status
        self.controller['viz_space'].redraw_performance_space(reset_scaler=True)
        self.controller['viz_stats'].redraw()

    def get_config(self):
        if self.config is None:
            return None
        else:
            return self.config.copy()

    def get_config_id(self):
        return self.config_id

    def get_problem_cfg(self):
        if self.problem_cfg is None:
            return None
        else:
            return self.problem_cfg.copy()

    def set_config(self, config, window=None):
        '''
        Setting configurations
        '''
        # set parent window for displaying potential error messagebox
        if window is None: window = self.root

        try:
            config = complete_config(config, check=True)
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
                problem, self.true_pfront = build_problem(config['problem']['name'], get_pfront=True)
            except Exception as e:
                tk.messagebox.showinfo('Error', 'Invalid values in configuration: ' + str(e), parent=window)
                return False

            # check if config is compatible with history data (problem dimension)
            table_exist = self.database.check_inited_table_exist(self.table_name)
            if table_exist:
                column_names = self.database.get_column_names(self.table_name)
                data_n_var = len([name for name in column_names if name.startswith('x')])
                data_n_obj = len([name for name in column_names if name.startswith('f') and '_' not in name])
                problem_cfg = problem.get_config()
                if problem_cfg['n_var'] != data_n_var or problem_cfg['n_obj'] != data_n_obj:
                    tk.messagebox.showinfo('Error', 'Problem dimension mismatch between configuration and history data', parent=window)
                    return False

            # update config
            self.config = config
            self.problem_cfg = problem.get_config()

            # remove tutorial image
            self.view.image_tutorial.destroy()

            # TODO: give hint of initializing

            # configure agents
            self.data_agent.configure(self.problem_cfg)
            self.worker_agent.configure(mode='manual', config=config, config_id=0, eval=hasattr(problem, 'evaluate_objective'))

            self.data_agent.init_table(create=not table_exist)
            problem_info = self.database.query_problem(self.table_name)
            self.controller['panel_info'].set_info(**problem_info)

            if not table_exist:
                # data initialization
                X_init_evaluated, X_init_unevaluated, Y_init_evaluated = get_initial_samples(problem, config['problem']['n_random_sample'], config['problem']['init_sample_path'])
                if X_init_evaluated is not None:
                    self.data_agent.init_data(X_init_evaluated, Y_init_evaluated)
                if X_init_unevaluated is not None:
                    rowids = self.data_agent.init_data(X_init_unevaluated)
                    for rowid in rowids:
                        self.worker_agent.add_eval_worker(rowid)
                    
                    # wait until initialization is completed
                    while not self.worker_agent.empty():
                        self.worker_agent.refresh()
                        sleep(self.refresh_rate / 1000.0)

            # calculate reference point
            if self.config['problem']['ref_point'] is None:
                Y = self.data_agent.load('Y')
                valid_idx = np.where((~np.isnan(Y)).all(axis=1))[0]
                Y = Y[valid_idx]
                ref_point = np.zeros(problem.n_obj)
                for i, m in enumerate(problem.obj_type):
                    if m == 'max':
                        ref_point[i] = np.max(Y[:, i])
                    elif m == 'min':
                        ref_point[i] = np.min(Y[:, i])
                    else:
                        raise Exception('obj_type must be min/max')
                self.config['problem']['ref_point'] = ref_point

            # initialize visualization widgets
            self._init_visualization()

            # load existing data
            if table_exist:
                self._load_existing_data()

            # change config create/change status
            self.view.menu_config.entryconfig(1, state=tk.DISABLED)
            self.view.menu_config.entryconfig(2, state=tk.NORMAL)

            for i in range(4):
                self.view.menu_database.entryconfig(i, state=tk.NORMAL)
            
            for i in range(3):
                self.view.menu_eval.entryconfig(i, state=tk.NORMAL)

            # activate widgets
            entry_mode = self.controller['panel_control'].view.widget['mode']
            entry_mode.enable(readonly=False)
            entry_mode.set('manual')
            entry_mode.enable(readonly=True)

            entry_batch_size = self.controller['panel_control'].view.widget['batch_size']
            entry_batch_size.enable()
            try:
                entry_batch_size.set(self.config['experiment']['batch_size'])
            except:
                entry_batch_size.set(5)

            entry_n_iter = self.controller['panel_control'].view.widget['n_iter']
            entry_n_iter.enable()
            try:
                entry_n_iter.set(self.config['experiment']['n_iter'])
            except:
                entry_n_iter.set(1)

            self.controller['panel_control'].view.widget['optimize'].enable()
            self.controller['panel_control'].view.widget['set_stop_cri'].enable()

            self.controller['panel_log'].view.widget['clear'].enable()

            # trigger periodic refresh
            self.root.after(self.refresh_rate, self.refresh)

        else: # user changed config in the middle
            try:
                # some keys cannot be changed
                unchanged_keys = ['name', 'n_random_sample', 'init_sample_path']
                if self.config_raw['problem']['ref_point'] is not None:
                    unchanged_keys.append('ref_point')
                for key in unchanged_keys:
                    assert (np.array(self.config_raw['problem'][key]) == np.array(config['problem'][key])).all()
            except:
                tk.messagebox.showinfo('Error', 'Invalid configuration values for reloading', parent=window)
                return False

            self.config = config
            
        self.database.update_config(name=self.table_name, config=self.config)
        
        if self.config != old_config:
            self.worker_agent.set_config(self.config, self.config_id)
            self.controller['viz_space'].set_config(self.config)
            self.controller['viz_stats'].set_config(self.config)

        return True

    def get_timestamp(self):
        return self.timestamp

    def set_timestamp(self):
        self.timestamp = time()

    def set_result_dir(self, result_dir):
        self.result_dir = result_dir

    def create_result_dir(self, window):
        # check if result_dir folder is not empty
        if os.path.exists(self.result_dir) and os.listdir(self.result_dir) != []:
            overwrite = tk.messagebox.askquestion('Error', f'Result folder {self.result_dir} is not empty, do you want to overwrite? If not, please change another folder for saving results by clicking: File -> Save in...', parent=window)
            if overwrite == 'no':
                return False
            else:
                shutil.rmtree(self.result_dir)
        os.makedirs(self.result_dir, exist_ok=True)
        return True

    def refresh(self):
        '''
        Refresh current GUI status and redraw if data has changed
        '''
        self.worker_agent.refresh()
        
        # can optimize and load config when worker agent is empty
        if self.worker_agent.empty():
            self.controller['panel_control'].view.widget['mode'].enable()
            self.controller['panel_control'].view.widget['optimize'].enable()
            self.controller['panel_control'].view.widget['stop'].disable()
            if self.view.menu_config.entrycget(0, 'state') == tk.DISABLED:
                self.view.menu_config.entryconfig(0, state=tk.NORMAL)
            if self.view.menu_config.entrycget(2, 'state') == tk.DISABLED:
                self.view.menu_config.entryconfig(2, state=tk.NORMAL)

        # post-process worker logs
        log_list = []
        for log in self.worker_agent.read_log():
            log = log.split('/') 
            log_text = log[0]
            log_list.append(log_text)

        # log display
        self.controller['panel_log'].log(log_list)

        # check if database has changed
        checksum = self.database.get_checksum(table=self.table_name)
        if checksum != self.table_checksum and checksum != 0:
            self.table_checksum = checksum
            
            # update database visualization
            self.controller['viz_database'].update_data()

            # update space visualization (TODO: only redraw when evaluation is done)
            self.controller['viz_space'].redraw_performance_space(reset_scaler=True)
            self.controller['viz_stats'].redraw()

        # check stopping criterion
        self.check_stop_criterion()
        
        # trigger another refresh
        self.root.after(self.refresh_rate, self.refresh)

    def check_stop_criterion(self):
        '''
        Check if stopping criterion is met
        '''
        stop = False
        stop_criterion = self.controller['panel_control'].stop_criterion
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
                if self.controller['viz_stats'].line_hv.get_ydata()[-1] >= val:
                    stop = True
            elif key == 'hv_conv': # hypervolume convergence
                hv_history = self.controller['viz_stats'].line_hv.get_ydata()
                checkpoint = np.clip(int(n_valid_sample * val / 100.0), 1, n_valid_sample - 1)
                if hv_history[-checkpoint] == hv_history[-1]:
                    stop = True
            else:
                raise NotImplementedError
        
        if stop:
            stop_criterion.clear()
            self.worker_agent.stop_worker()
            self.controller['panel_log'].log('stopping criterion is met')
        
    def _quit(self):
        '''
        Quit handling
        '''
        plt.close('all')
        self.database.quit()
        self.data_agent.quit()
        self.worker_agent.quit()

        self.root.quit()
        self.root.destroy()

    def run(self):
        self.root_login.mainloop()