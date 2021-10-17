import os
import shutil
import yaml
from time import time, sleep
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from autooed.problem import build_problem
from autooed.utils.path import get_root_dir
from autooed.system.experiment.config import complete_config

from autooed.system.params import *
from autooed.system.database import Database
from autooed.system.agent import OptimizeAgent
from autooed.system.scheduler import OptimizeScheduler

from autooed.system.gui.widgets.image import ImageFrame
from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.utils.grid import grid_configure

from autooed.system.gui.init import InitCreateController, InitLoadController, InitRemoveController
from autooed.system.gui.menu import MenuConfigController, MenuProblemController, MenuEvalController, MenuExportController
from autooed.system.gui.panel import PanelInfoController, PanelControlController, PanelLogController
from autooed.system.gui.viz import VizSpaceController, VizStatsController, VizDatabaseController



class GUIInitView:

    def __init__(self, root):
        self.root = root

        frame_init = create_widget('frame', master=self.root, row=0, column=0)
        create_widget('logo', master=frame_init, row=0, column=0, columnspan=3)

        self.widget = {}
        self.widget['create_experiment'] = create_widget('button', master=frame_init, row=1, column=0, text='Create Experiment')
        self.widget['load_experiment'] = create_widget('button', master=frame_init, row=1, column=1, text='Load Experiment')
        self.widget['remove_experiment'] = create_widget('button', master=frame_init, row=1, column=2, text='Remove Experiment')


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
        self.menu_config = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='Config', menu=self.menu_config)
        self.menu_config.add_command(label='Load')
        self.menu_config.add_command(label='Create')
        self.menu_config.add_command(label='Change')

        self.menu_problem = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='Problem', menu=self.menu_problem)
        self.menu_problem.add_command(label='Manage')

        self.menu_eval = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='Evaluation', menu=self.menu_eval)
        self.menu_eval.add_command(label='Start')
        self.menu_eval.add_command(label='Stop')

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

        # temporarily disable tabs until data loaded
        self.nb_viz.tab(0, state=tk.DISABLED)
        self.nb_viz.tab(1, state=tk.DISABLED)
        self.nb_viz.tab(2, state=tk.DISABLED)

        # initialize tutorial image
        img_path = os.path.join(get_root_dir(), 'static', 'tutorial.png')
        self.image_tutorial = ImageFrame(master=self.root, img_path=img_path)
        self.image_tutorial.grid(row=0, column=0, rowspan=3, sticky='NSEW')

    def activate_viz(self):
        '''
        activate visualization tabs
        '''
        self.nb_viz.tab(0, state=tk.NORMAL)
        self.nb_viz.tab(1, state=tk.NORMAL)
        self.nb_viz.tab(2, state=tk.NORMAL)
        self.nb_viz.select(0)


class GUIController:

    def __init__(self):
        self.root_init = tk.Tk()
        self.root_init.title(TITLE)
        self.root_init.protocol('WM_DELETE_WINDOW', self._quit_init)
        self.root_init.resizable(False, False)
        self.view_init = GUIInitView(self.root_init)
        self.bind_command_init()

        self.root = None
        self.view = None
        
        self.database = Database()
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
        InitCreateController(self)
                
    def load_experiment(self):
        '''
        '''
        InitLoadController(self)

    def remove_experiment(self):
        '''
        '''
        InitRemoveController(self)

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

        self.refresh_rate = REFRESH_RATE # ms
        self.config = None
        self.problem_cfg = None
        self.timestamp = None

        self.agent = OptimizeAgent(self.database, self.table_name)
        self.scheduler = OptimizeScheduler(self.agent)

        self.true_pfront = None

        self.n_sample = None
        self.n_valid_sample = None

        self.view = GUIView(self.root)
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
                
            if self.scheduler.agent.ref_point is None:
                self.scheduler.agent._init_ref_point()

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
