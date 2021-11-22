import os
import shutil
import yaml
from time import time, sleep
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from autooed.problem import build_problem, get_problem_config
from autooed.utils.path import get_root_dir, get_icon_path
from autooed.utils.initialization import load_provided_initial_samples, verify_provided_initial_samples
from autooed.system.config import complete_config

from autooed.system.params import *
from autooed.system.database import Database
from autooed.system.agent import OptimizeAgent
from autooed.system.scheduler import OptimizeScheduler

from autooed.system.gui.widgets.image import ImageFrame
from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.utils.layout import grid_configure, center

from autooed.system.gui.experiment import ExpConfigController, ExpLoadController, ExpRemoveController
from autooed.system.gui.problem import ProblemController
from autooed.system.gui.menu import MenuExportController
from autooed.system.gui.panel import PanelInfoController, PanelControlController, PanelLogController
from autooed.system.gui.visualization import VizSpaceController, VizStatsController, VizDatabaseController


class GUIInitView:

    def __init__(self, root):
        self.root = root

        frame_init = create_widget('frame', master=self.root, row=0, column=0)
        create_widget('logo', master=frame_init, row=0, column=0, rowspan=4)

        self.widget = {}
        self.widget['manage_problem'] = create_widget('button', master=frame_init, row=0, column=1, text='Manage Problem')
        self.widget['create_experiment'] = create_widget('button', master=frame_init, row=1, column=1, text='Create Experiment')
        self.widget['load_experiment'] = create_widget('button', master=frame_init, row=2, column=1, text='Load Experiment')
        self.widget['remove_experiment'] = create_widget('button', master=frame_init, row=3, column=1, text='Remove Experiment')


class GUIView:

    def __init__(self, root):
        '''         
        GUI initialization
        '''
        # GUI root initialization
        self.root = root
        self.root.geometry(f'{WIDTH}x{HEIGHT}')
        grid_configure(self.root, 2, 0, row_weights=[1, 1, 20]) # configure for resolution change

        self._init_menu()
        self._init_viz()

    def _init_menu(self):
        '''
        Menu initialization
        '''
        # top-level menu
        self.menu = tk.Menu(master=self.root, relief='raised')
        self.root.config(menu=self.menu)

        # sub-level menu
        self.menu_export = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='Export', menu=self.menu_export)
        self.menu_export.add_command(label='Database')
        self.menu_export.add_command(label='Statistics')
        self.menu_export.add_command(label='Figures')
        
    def _init_viz(self):
        '''
        Visualization initialization
        '''
        frame_viz = tk.Frame(master=self.root)
        frame_viz.grid(row=0, column=0, rowspan=3, sticky='NSEW')
        grid_configure(frame_viz, 0, 0)

        # configure tab widgets
        self.nb_viz = ttk.Notebook(master=frame_viz)
        self.nb_viz.grid(row=0, column=0, sticky='NSEW')
        self.frame_plot = tk.Frame(master=self.nb_viz)
        self.frame_stat = tk.Frame(master=self.nb_viz)
        self.frame_db = tk.Frame(master=self.nb_viz)
        self.nb_viz.add(child=self.frame_plot, text='Visualization')
        self.nb_viz.add(child=self.frame_stat, text='Statistics')
        self.nb_viz.add(child=self.frame_db, text='Database')
        grid_configure(self.frame_plot, [0], [0])
        grid_configure(self.frame_stat, [0], [0])
        grid_configure(self.frame_db, [0], [0])


class GUIController:

    def __init__(self):
        self.database = Database()
        self.table_name = None
        self.table_checksum = None
        self.refresh_rate = REFRESH_RATE
        self.timestamp = None
        self.config = None
        self.problem_cfg = None
        self.agent = None
        self.scheduler = None

        self.root = tk.Tk()
        self.root.title('AutoOED')
        self.root.protocol('WM_DELETE_WINDOW', self._quit_init)
        self.root.resizable(False, False)
        self.root.iconphoto(True, tk.Image('photo', file=get_icon_path()))

        self.view = GUIInitView(self.root)
        self.view.widget['manage_problem'].configure(command=self.manage_problem)
        self.view.widget['create_experiment'].configure(command=self.create_experiment)
        self.view.widget['load_experiment'].configure(command=self.load_experiment)
        self.view.widget['remove_experiment'].configure(command=self.remove_experiment)

        center(self.root)
        self.root.mainloop()

    def manage_problem(self):
        '''
        '''
        ProblemController(self)

    def create_experiment(self):
        '''
        '''
        ExpConfigController(self).create_config()

    def update_experiment(self):
        '''
        '''
        ExpConfigController(self).update_config()
                
    def load_experiment(self):
        '''
        '''
        ExpLoadController(self)

    def remove_experiment(self):
        '''
        '''
        ExpRemoveController(self)

    def verify_config(self, table_name, config, window=None):
        '''
        Verify experiment configuration for the first time. 
        Return processed config if successful, otherwise, return None.
        '''
        assert self.table_name is None
        if window is None: window = self.root

        # check if experiment exists
        if self.database.check_table_exist(name=table_name):
            tk.messagebox.showinfo('Error', f'Experiment {table_name} already exists', parent=window)
            return

        # check if config is valid
        try:
            config = complete_config(config, check=True)
        except Exception as e:
            tk.messagebox.showinfo('Error', 'Invalid configurations: ' + str(e), parent=window)
            return

        # check if problem can be built
        try:
            problem = build_problem(config['problem']['name'])
        except Exception as e:
            tk.messagebox.showinfo('Error', 'Failed to build problem: ' + str(e), parent=window)
            return

        # check if initial samples to be loaded are valid
        if 'init_sample_path' in config['experiment'] and config['experiment']['init_sample_path'] is not None:
            try:
                X_init, Y_init = load_provided_initial_samples(config['experiment']['init_sample_path'])
                problem_cfg = problem.get_config()
                n_var, n_obj = problem_cfg['n_var'], problem_cfg['n_obj']
                verify_provided_initial_samples(X_init, Y_init, n_var, n_obj)
            except Exception as e:
                tk.messagebox.showinfo('Error', 'Failed to load initial samples from file: ' + str(e), parent=window)
                return

        # success
        return config

    def init_config(self, table_name, config=None, window=None):
        '''
        '''
        if window is None: window = self.root

        # check if table exists
        if config is None: # load experiment
            config = self.database.query_config(table_name)
            if config is None:
                tk.messagebox.showinfo('Error', f'Database cannot find config of {table_name}, please recreate this experiment', parent=window)
                return
            table_exist = True
        else: # create experiment
            table_exist = False

        # create database table
        if not table_exist:
            try:
                self.database.create_table(table_name)
            except Exception as e:
                tk.messagebox.showinfo('Error', 'Failed to create database table: ' + str(e), parent=window)
                return

        # create agent and scheduler
        agent = OptimizeAgent(self.database, table_name)
        scheduler = OptimizeScheduler(agent)
        try:
            scheduler.set_config(config)
        except Exception as e:
            scheduler.stop_all()
            self.database.remove_table(table_name)
            tk.messagebox.showinfo('Error', 'Invalid values in configuration: ' + str(e), parent=window)
            return

        # set properties
        self.table_name = table_name
        self.config = config
        problem, self.true_pfront = build_problem(self.config['problem']['name'], get_pfront=True)
        self.problem_cfg = problem.get_config()
        self.problem_cfg.update(self.config['problem'])
        self.agent = agent
        self.scheduler = scheduler

        # initialize window
        self._quit_init(quit_db=False)
        self.root = tk.Tk()
        self.root.title('AutoOED')
        self.root.protocol('WM_DELETE_WINDOW', self._quit)
        self.root.iconphoto(True, tk.Image('photo', file=get_icon_path()))

        # initialize main GUI
        self.view = GUIView(self.root)
        self.controller = {
            'menu_export': MenuExportController(self),
            'panel_info': PanelInfoController(self),
            'panel_control': PanelControlController(self),
            'panel_log': PanelLogController(self),
            'viz_space': VizSpaceController(self),
            'viz_stats': VizStatsController(self),
            'viz_database': VizDatabaseController(self),
        }
        self.view.menu_export.entryconfig(0, command=self.controller['menu_export'].export_db)
        self.view.menu_export.entryconfig(1, command=self.controller['menu_export'].export_stats)
        self.view.menu_export.entryconfig(2, command=self.controller['menu_export'].export_figures)

        # initialize GUI params
        if not self.agent.can_eval:
            entry_mode = self.controller['panel_control'].view.widget['mode']
            entry_mode.widget['Auto'].config(state=tk.DISABLED)
        entry_batch_size = self.controller['panel_control'].view.widget['batch_size']
        entry_batch_size.set(self.config['experiment']['batch_size'])

        # trigger periodic refresh
        self.root.after(self.refresh_rate, self.refresh)
        # center(self.root)
        self.root.mainloop()

    def set_config(self, config):
        '''
        '''
        try:
            self.scheduler.set_config(config)
        except Exception as e:
            self.scheduler.stop_all()
            tk.messagebox.showinfo('Error', 'Invalid values in configuration: ' + str(e), parent=self.root)
            return
        self.config = config

    def get_config(self):
        if self.config is None:
            return None
        else:
            return self.config.copy()

    def get_problem_cfg(self):
        if self.problem_cfg is None:
            return None
        else:
            return self.problem_cfg.copy()

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

    def _quit_init(self, quit_db=True):
        '''
        Quit handling for init window
        '''
        self.root.quit()
        self.root.destroy()
        if quit_db:
            self.database.quit()
        
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
