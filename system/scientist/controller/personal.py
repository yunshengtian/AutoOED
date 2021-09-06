import os
import shutil
import yaml
from time import time, sleep
import numpy as np
import matplotlib.pyplot as plt

from experiment.config import complete_config
from problem.common import build_problem
from problem.problem import Problem

import tkinter as tk
from tkinter import messagebox
from system.params import *
from system.database.personal import PersonalDatabase
from system.agent import OptimizeAgent
from system.scheduler import OptimizeScheduler

from system.scientist.view.init import ScientistInitView
from system.scientist.view.main import ScientistView
from system.scientist.experiment import CreateExperimentController, LoadExperimentController, RemoveExperimentController
from system.scientist.menu import MenuConfigController, MenuProblemController, MenuEvalController, MenuExportController
from system.scientist.panel import PanelInfoController, PanelControlController, PanelLogController
from system.scientist.viz import VizSpaceController, VizStatsController, VizDatabaseController


class ScientistController:

    def __init__(self):
        self.root_init = tk.Tk()
        self.root_init.title(TITLE)
        self.root_init.protocol('WM_DELETE_WINDOW', self._quit_init)
        self.root_init.resizable(False, False)
        self.view_init = ScientistInitView(self.root_init)
        self.bind_command_init()

        self.root = None
        self.view = None
        
        self.database = PersonalDatabase()
        self.table_name = None
        self.table_checksum = None

    def bind_command_init(self):
        '''
        '''
        self.view_init.widget['create_experiment'].configure(command=self.create_experiment)
        self.view_init.widget['load_experiment'].configure(command=self.load_experiment)
        self.view_init.widget['remove_experiment'].configure(command=self.remove_experiment)

    def create_experiment(self):
        '''
        '''
        CreateExperimentController(self)
                
    def load_experiment(self):
        '''
        '''
        LoadExperimentController(self)

    def remove_experiment(self):
        '''
        '''
        RemoveExperimentController(self)

    def _quit_init(self, force=True):
        '''
        Quit handling for init window
        '''
        self.root_init.quit()
        self.root_init.destroy()
        if force:
            self.database.quit()

    def after_init(self, table_name):
        '''
        '''
        self._quit_init(force=False)

        self.table_name = table_name

        self.root = tk.Tk()
        self.root.title(f'{TITLE}')
        self.root.protocol('WM_DELETE_WINDOW', self._quit)

        # TODO: use customized theme
        # from tkinter import ttk
        # from system.utils.path import get_root_dir
        # self.root.tk.call('lappend', 'auto_path', os.path.join(get_root_dir(), 'system', 'gui', 'themes'))
        # self.root.tk.call('package', 'require', 'awdark')
        # s = ttk.Style()
        # s.theme_use('awdark')

        self.refresh_rate = REFRESH_RATE # ms
        self.config = None
        self.problem_cfg = None
        self.timestamp = None

        self.agent = OptimizeAgent(self.database, self.table_name)
        self.scheduler = OptimizeScheduler(self.agent)

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

        self.controller['menu_eval'] = MenuEvalController(self)
        self.view.menu_eval.entryconfig(0, command=self.controller['menu_eval'].start_eval, state=tk.DISABLED)
        self.view.menu_eval.entryconfig(1, command=self.controller['menu_eval'].stop_eval, state=tk.DISABLED)

        self.controller['menu_export'] = MenuExportController(self)
        self.view.menu_export.entryconfig(0, command=self.controller['menu_export'].export_db, state=tk.DISABLED)
        self.view.menu_export.entryconfig(1, command=self.controller['menu_export'].export_stats, state=tk.DISABLED)
        self.view.menu_export.entryconfig(2, command=self.controller['menu_export'].export_figures, state=tk.DISABLED)

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
        return self.agent.get_config()

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
        
        old_config = None if self.config is None else self.config.copy()

        if self.config is None: # first time setting config
            # initialize problem
            try:
                problem, self.true_pfront = build_problem(config['problem']['name'], get_pfront=True)
            except Exception as e:
                tk.messagebox.showinfo('Error', 'Invalid values in configuration: ' + str(e), parent=window)
                return False

            problem_cfg = problem.get_config()

            # check if config is compatible with history data (problem dimension)
            table_exist = self.agent.check_table_exist()

            if table_exist:
                column_names = self.agent.get_column_names()
                data_n_var = len([name for name in column_names if name.startswith('x')])
                data_n_obj = len([name for name in column_names if name.startswith('f') and '_' not in name])
                if problem_cfg['n_var'] != data_n_var or problem_cfg['n_obj'] != data_n_obj:
                    tk.messagebox.showinfo('Error', 'Problem dimension mismatch between configuration and history data', parent=window)
                    return False

            # configure scheduler
            try:
                self.scheduler.set_config(config)
            except Exception as e:
                tk.messagebox.showinfo('Error', 'Invalid values in configuration: ' + str(e), parent=window)
                return False

            # update config
            self.config = config
            self.problem_cfg = problem.get_config()
            self.problem_cfg.update(self.config['problem'])

            # remove tutorial image
            self.view.image_tutorial.destroy()

            # set problem info
            self.controller['panel_info'].set_info(self.problem_cfg)

            # initialize visualization widgets
            self._init_visualization()

            # load existing data
            if table_exist:
                self._load_existing_data()
            
            # change menu button status
            self.view.menu_config.entryconfig(0, state=tk.DISABLED)
            self.view.menu_config.entryconfig(1, state=tk.DISABLED)
            self.view.menu_config.entryconfig(2, state=tk.NORMAL)
            for i in range(3):
                self.view.menu_export.entryconfig(i, state=tk.NORMAL)
            for i in range(2):
                self.view.menu_eval.entryconfig(i, state=tk.NORMAL)

            # activate widgets
            entry_mode = self.controller['panel_control'].view.widget['mode']
            entry_mode.enable()
            if not self.agent.can_eval:
                entry_mode.widget['Auto'].config(state=tk.DISABLED)

            entry_batch_size = self.controller['panel_control'].view.widget['batch_size']
            entry_batch_size.enable()
            try:
                entry_batch_size.set(self.config['experiment']['batch_size'])
            except:
                entry_batch_size.set(5)

            self.controller['panel_log'].view.widget['clear'].enable()

            # trigger periodic refresh
            self.root.after(self.refresh_rate, self.refresh)

        else: # user changed config in the middle
            try:
                assert self.config['problem']['name'] == config['problem']['name']
            except:
                tk.messagebox.showinfo('Error', 'Cannot change problem', parent=window)
                return False

            self.config = config
            self.scheduler.set_config(self.config)
        
        if self.config != old_config:
            self.controller['viz_space'].set_config(self.config)

        return True

    def get_timestamp(self):
        return self.timestamp

    def set_timestamp(self):
        self.timestamp = time()

    def refresh(self):
        '''
        Refresh current GUI status and redraw if data has changed
        '''
        self.scheduler.refresh()
        
        # change button status when scheduler is free
        if not self.scheduler.is_optimizing() and self.agent.check_initialized():
            if not self.scheduler.is_evaluating_manual():
                self.controller['panel_control'].enable_manual()
            if self.agent.can_eval and not self.scheduler.is_evaluating_auto():
                self.controller['panel_control'].enable_auto()

        # log display
        log_list = self.scheduler.logger.read()
        self.controller['panel_log'].log(log_list)

        # check if database has changed
        checksum = self.database.get_checksum()
        if checksum != self.table_checksum and checksum != 0:
            self.table_checksum = checksum
            
            # update database visualization
            self.controller['viz_database'].update_data()

            # update space visualization (TODO: only redraw when evaluation is done)
            self.controller['viz_space'].redraw_performance_space(reset_scaler=True)
            self.controller['viz_stats'].redraw()
        
        # trigger another refresh
        self.root.after(self.refresh_rate, self.refresh)
        
    def _quit(self):
        '''
        Quit handling
        '''
        plt.close('all')
        self.database.quit()
        self.agent.quit()
        self.scheduler.quit()

        self.root.quit()
        self.root.destroy()

    def run(self):
        self.root_init.mainloop()