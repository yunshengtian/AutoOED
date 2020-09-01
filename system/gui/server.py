import tkinter as tk
from tkinter import ttk, scrolledtext
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MaxNLocator
from matplotlib.backend_bases import MouseButton


import os
import yaml
import numpy as np
from time import time, sleep
from problems.common import build_problem, get_initial_samples, get_problem_list, get_yaml_problem_list, get_problem_config
from problems.utils import import_module_from_path
from system.agent import DataAgent, WorkerAgent
from system.manager import ProblemManager, WorkerManager
from system.utils import process_config, load_config, get_available_algorithms, calc_hypervolume, calc_pred_error, find_closest_point, check_pareto
from system.gui.utils.button import Button
from system.gui.utils.entry import get_entry
from system.gui.utils.excel import Excel
from system.gui.utils.listbox import Listbox
from system.gui.utils.table import Table
from system.gui.utils.grid import grid_configure, embed_figure
from system.gui.utils.radar import radar_factory
from system.gui.utils.widget_creation import create_widget, show_widget_error
from system.gui.utils.image import ImageFrame


class ServerGUI:
    '''
    Interactive local tkinter-based GUI
    '''
    def __init__(self):
        '''
        GUI initialization
        '''
        # GUI root initialization
        self.root = tk.Tk()
        self.root.title('OpenMOBO - Server')
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        grid_configure(self.root, [0, 1], [0], row_weights=[1, 20]) # configure for resolution change
        screen_width = self.root.winfo_screenwidth()
        max_width = 1280
        width = 0.8 * screen_width
        if width > max_width: width = max_width
        height = 0.5 * width
        self.root.geometry(f'{int(width)}x{int(height)}')

        # predefined GUI parameters
        self.refresh_rate = 100 # ms
        self.result_dir = os.path.abspath('result') # initial result directory

        # agent
        self.agent_data = None
        self.agent_worker = None

        # manager
        self.manager_problem = ProblemManager()
        self.manager_worker = WorkerManager()

        # config related
        self.config = None
        self.config_raw = None
        self.config_id = -1

        # event widgets
        self.button_optimize = None
        self.button_stop = None
        self.button_stopcri = None
        self.scrtext_log = None
        self.entry_mode = None
        self.entry_batch_size = None
        self.entry_n_iter = None
        self.nb_viz = None
        self.frame_plot = None
        self.frame_stat = None
        self.frame_db = None
        self.table_db = None
        self.image_tutorial = None

        # data to be plotted
        self.scatter_x = None
        self.scatter_y = None
        self.scatter_y_pareto = None
        self.line_y_pred_list = []
        self.scatter_selected = None
        self.line_x = None
        self.fill_x = None
        self.bar_x = None
        self.text_x = []
        self.line_hv = None
        self.line_error = None

        # status variables
        self.n_init_sample = None
        self.n_sample = None
        self.n_valid_sample = None
        self.curr_iter = tk.IntVar()
        self.max_iter = 0
        self.in_creating_problem = False
        self.in_creating_worker = False
        self.db_status = 0
        self.stop_criterion = {}
        self.timestamp = None
        self.true_pfront = None
        self.pfront_limit = None

        # GUI modules initialization
        self._init_mapping()
        self._init_menu()
        self._init_widgets()

    def _init_mapping(self):
        '''
        Mapping initialization
        '''
        self.name_map = {
            'general': {
                'n_worker': 'Max number of evaluation workers',
                'batch_size': 'Batch size',
                'n_iter': 'Number of iterations',
            },
            'problem': {
                'name': 'Name of problem',
                'n_var': 'Number of design variables',
                'n_obj': 'Number of objectives',
                'n_constr': 'Number of constraints',
                'performance_eval': 'Performance evaluation script',
                'constraint_eval': 'Constraint evaluation script',
                'var_lb': 'Lower bound',
                'var_ub': 'Upper bound',
                'obj_lb': 'Lower bound',
                'obj_ub': 'Upper bound',
                'var_name': 'Names',
                'obj_name': 'Names',
                'ref_point': 'Reference point',
                'n_init_sample': 'Number of random initial samples',
                'init_sample_path': 'Path of provided initial samples',
            },
            'algorithm': {
                'name': 'Name of algorithm',
                'n_process': 'Number of parallel processes to use',
            },
        }

        self.name_map_algo = {
            'surrogate': {
                'name': 'Name',
                'nu': 'Type of Matern kernel',
                'n_spectral_pts': 'Number of points for spectral sampling',
                'mean_sample': 'Use mean sample for Thompson sampling',
            },
            'acquisition': {
                'name': 'Name',
            },
            'solver': {
                'name': 'Name',
                'n_gen': 'Number of generations',
                'pop_size': 'Population size',
                'pop_init_method': 'Population initialization method',
            },
            'selection': {
                'name': 'Name',
            },
        }

        self.value_map_algo = {
            'surrogate': {
                'name': {
                    'gp': 'Gaussian Process',
                    'ts': 'Thompson Sampling',
                    'nn': 'Neural Network',
                },
            },
            'acquisition': {
                'name': {
                    'identity': 'Identity',
                    'pi': 'Probability of Improvement',
                    'ei': 'Expected Improvement',
                    'ucb': 'Upper Confidence Bound',
                    'lcb': 'Lower Confidence Bound',
                },
            },
            'solver': {
                'name': {
                    'nsga2': 'NSGA-II',
                    'moead': 'MOEA/D',
                    'parego': 'ParEGO Solver',
                },
                'pop_init_method': {
                    'random': 'Random',
                    'nds': 'Non-Dominated Sort',
                    'lhs': 'Latin-Hypercube Sampling',
                },
            },
            'selection': {
                'name': {
                    'hvi': 'Hypervolume Improvement',
                    'uncertainty': 'Uncertainty',
                    'random': 'Random',
                    'moead': 'MOEA/D Selection',
                },
            },
        }

        self.value_inv_map_algo = {}
        for cfg_type, val_map in self.value_map_algo.items():
            self.value_inv_map_algo[cfg_type] = {}
            for key, value_map in val_map.items():
                self.value_inv_map_algo[cfg_type][key] = {v: k for k, v in value_map.items()}

        self.name_map_worker = {
            'id': 'ID',
            'name': 'Name',
            'timeout': 'Default timeout (s)',
        }

    def _init_menu(self):
        '''
        Menu initialization
        '''
        # top-level menu
        self.menu = tk.Menu(master=self.root, relief='raised')
        self.root.config(menu=self.menu)

        # sub-level menu
        self.menu_file = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='File', menu=self.menu_file)
        self.menu_config = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='Config', menu=self.menu_config)
        self.menu_problem = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='Problem', menu=self.menu_problem)
        self.menu_worker = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='Worker', menu=self.menu_worker)
        self.menu_log = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='Log', menu=self.menu_log)

        # init sub-level menu
        self._init_file_menu()
        self._init_config_menu()
        self._init_problem_menu()
        self._init_worker_menu()
        self._init_log_menu()

    def _init_file_menu(self):
        '''
        File menu initialization
        '''
        self.menu_file.add_command(label='Save in...')

        def gui_change_saving_path():
            '''
            Change data saving path
            '''
            dirname = tk.filedialog.askdirectory(parent=self.root)
            if not isinstance(dirname, str) or dirname == '': return
            self.result_dir = dirname

        # link menu command
        self.menu_file.entryconfig(0, command=gui_change_saving_path)

    def _init_config_menu(self):
        '''
        Config menu initialization
        '''
        self.menu_config.add_command(label='Load')
        self.menu_config.add_command(label='Create')
        self.menu_config.add_command(label='Change')

        def gui_load_config():
            '''
            Load config from file
            '''
            filename = tk.filedialog.askopenfilename(parent=self.root)
            if not isinstance(filename, str) or filename == '': return

            try:
                config = load_config(filename)
            except:
                tk.messagebox.showinfo('Error', 'Invalid yaml file', parent=self.root)
                return
                
            self._set_config(config)

        def gui_build_config_window(change=False):
            '''
            Build config GUI
            '''
            # arrange widgets as a dict with same structure as config
            widget_map = {
                'general': {}, 
                'problem': {}, 
                'algorithm': {},
            }

            problem_cfg = {} # store other problem configs that cannot be obtained by widget.get()
            algo_cfg = {} # store advanced config of algorithm

            window = tk.Toplevel(master=self.root)
            if change:
                window.title('Change Configurations')
            else:
                window.title('Create Configurations')
            window.resizable(False, False)

            # parameter section
            frame_param = tk.Frame(master=window)
            frame_param.grid(row=0, column=0)
            grid_configure(frame_param, [0, 1, 2], [0])

            # TODO: set default values visible

            # problem subsection
            frame_problem = create_widget('labeled_frame', master=frame_param, row=0, column=0, text='Problem')
            grid_configure(frame_problem, [0, 1, 2, 3, 4, 5, 6, 7], [0])
            widget_map['problem']['name'] = create_widget('labeled_combobox', 
                master=frame_problem, row=0, column=0, text=self.name_map['problem']['name'], values=get_problem_list(), width=15, required=True, changeable=False)
            widget_map['problem']['n_var'] = create_widget('labeled_entry', 
                master=frame_problem, row=1, column=0, text=self.name_map['problem']['n_var'], class_type='int', required=True,
                valid_check=lambda x: x > 0, error_msg='number of design variables must be positive', changeable=False)
            widget_map['problem']['n_obj'] = create_widget('labeled_entry', 
                master=frame_problem, row=2, column=0, text=self.name_map['problem']['n_obj'], class_type='int', required=True,
                valid_check=lambda x: x > 1, error_msg='number of objectives must be greater than 1', changeable=False)
            widget_map['problem']['ref_point'] = create_widget('labeled_entry', 
                master=frame_problem, row=3, column=0, text=self.name_map['problem']['ref_point'], class_type='floatlist', width=10, 
                valid_check=lambda x: len(x) == widget_map['problem']['n_obj'].get(), error_msg='dimension of reference point mismatches number of objectives', changeable=False) # TODO: changeable

            for key in ['n_var', 'n_obj', 'ref_point']:
                widget_map['problem'][key].disable()

            def gui_config_design():
                '''
                Configure bounds for design variables
                '''
                # validity check
                try:
                    n_var = widget_map['problem']['n_var'].get()
                except:
                    error_msg = widget_map['problem']['n_var'].get_error_msg()
                    error_msg = '' if error_msg is None else ': ' + error_msg
                    tk.messagebox.showinfo('Error', 'Invalid value for "' + self.name_map['problem']['n_var'] + '"' + error_msg, parent=window)
                    return

                var_name = problem_cfg['var_name']
                if n_var != len(var_name):
                    var_name = [f'x{i + 1}' for i in range(n_var)]
                    problem_cfg['var_name'] = var_name

                titles = ['var_name', 'var_lb', 'var_ub']

                window_design = tk.Toplevel(master=window)
                window_design.title('Set Design Bounds')
                window_design.resizable(False, False)

                # design space section
                frame_design = create_widget('frame', master=window_design, row=0, column=0)
                create_widget('label', master=frame_design, row=0, column=0, text='Enter the bounds for design variables:')
                excel_design = Excel(master=frame_design, rows=n_var, columns=3, width=15,
                    title=[self.name_map['problem'][title] for title in titles], dtype=[str, float, float], default=[None, 0, 1])
                excel_design.grid(row=1, column=0)
                excel_design.set_column(0, var_name)
                excel_design.disable_column(0)

                if self.config is not None:
                    excel_design.set_column(1, self.config['problem']['var_lb'])
                    excel_design.set_column(2, self.config['problem']['var_ub'])

                def gui_save_design_space():
                    '''
                    Save design space parameters
                    '''
                    temp_cfg = {}
                    for column, key in zip([1, 2], ['var_lb', 'var_ub']):
                        try:
                            temp_cfg[key] = excel_design.get_column(column)
                        except:
                            tk.messagebox.showinfo('Error', 'Invalid value for "' + self.name_map['problem'][key] + '"', parent=window_design)
                            return
                    for key, val in temp_cfg.items():
                        problem_cfg[key] = val

                    window_design.destroy()

                # action section
                frame_action = tk.Frame(master=window_design)
                frame_action.grid(row=1, column=0)
                create_widget('button', master=frame_action, row=0, column=0, text='Save', command=gui_save_design_space)
                create_widget('button', master=frame_action, row=0, column=1, text='Cancel', command=window_design.destroy)

            def gui_config_performance():
                '''
                Configure bounds for objectives
                '''
                # validity check
                try:
                    n_obj = widget_map['problem']['n_obj'].get()
                except:
                    error_msg = widget_map['problem']['n_obj'].get_error_msg()
                    error_msg = '' if error_msg is None else ': ' + error_msg
                    tk.messagebox.showinfo('Error', 'Invalid value for "' + self.name_map['problem']['n_obj'] + '"' + error_msg, parent=window)
                    return

                obj_name = problem_cfg['obj_name']
                if n_obj != len(obj_name):
                    obj_name = [f'f{i + 1}' for i in range(n_obj)]
                    problem_cfg['obj_name'] = obj_name

                titles = ['obj_name', 'obj_lb', 'obj_ub']

                window_performance = tk.Toplevel(master=window)
                window_performance.title('Set Performance Bounds')
                window_performance.resizable(False, False)

                # performance space section
                frame_performance = create_widget('frame', master=window_performance, row=0, column=0)
                create_widget('label', master=frame_performance, row=0, column=0, text='Enter the bounds for performance values:')
                excel_performance = Excel(master=frame_performance, rows=n_obj, columns=3, width=15,
                    title=[self.name_map['problem'][title] for title in titles], dtype=[str, float, float])
                excel_performance.grid(row=1, column=0)
                excel_performance.set_column(0, obj_name)
                excel_performance.disable_column(0)

                if self.config is not None:
                    if 'obj_lb' in self.config['problem']:
                        excel_performance.set_column(1, self.config['problem']['obj_lb'])
                    if 'obj_ub' in self.config['problem']:
                        excel_performance.set_column(2, self.config['problem']['obj_ub'])

                def gui_save_performance_space():
                    '''
                    Save performance space parameters
                    '''
                    temp_cfg = {}
                    for column, key in zip([1, 2], ['obj_lb', 'obj_ub']):
                        try:
                            temp_cfg[key] = excel_performance.get_column(column)
                        except:
                            tk.messagebox.showinfo('Error', 'Invalid value for "' + self.name_map['problem'][key] + '"', parent=window_performance)
                            return
                    for key, val in temp_cfg.items():
                        problem_cfg[key] = val
                    
                    window_performance.destroy()

                # action section
                frame_action = tk.Frame(master=window_performance)
                frame_action.grid(row=1, column=0)
                create_widget('button', master=frame_action, row=0, column=0, text='Save', command=gui_save_performance_space)
                create_widget('button', master=frame_action, row=0, column=1, text='Cancel', command=window_performance.destroy)

            frame_space = tk.Frame(master=frame_problem)
            frame_space.grid(row=4, column=0)
            button_config_design = create_widget('button', master=frame_space, row=4, column=0, text='Set design bounds', command=gui_config_design)
            button_config_performance = create_widget('button', master=frame_space, row=4, column=1, text='Set performance bounds', command=gui_config_performance)

            def gui_set_x_init():
                '''
                Set path of provided initial design variables
                '''
                filename = tk.filedialog.askopenfilename(parent=window)
                if not isinstance(filename, str) or filename == '': return
                widget_x_init.set(filename)

            def gui_set_y_init():
                '''
                Set path of provided initial performance values
                '''
                filename = tk.filedialog.askopenfilename(parent=window)
                if not isinstance(filename, str) or filename == '': return
                widget_y_init.set(filename)

            widget_map['problem']['n_init_sample'] = create_widget('labeled_entry', 
                master=frame_problem, row=5, column=0, text=self.name_map['problem']['n_init_sample'], class_type='int', default=0, 
                valid_check=lambda x: x >= 0, error_msg='number of initial samples cannot be negative', changeable=False)
            button_browse_x_init, widget_x_init = create_widget('labeled_button_entry',
                master=frame_problem, row=6, column=0, label_text='Path of provided initial design variables', button_text='Browse', command=gui_set_x_init, 
                width=30, valid_check=lambda x: os.path.exists(x), error_msg="file not exists", changeable=False)
            button_browse_y_init, widget_y_init = create_widget('labeled_button_entry',
                master=frame_problem, row=7, column=0, label_text='Path of provided initial performance values', button_text='Browse', command=gui_set_y_init, 
                width=30, valid_check=lambda x: os.path.exists(x), error_msg="file not exists", changeable=False)

            if not change:
                button_config_design.disable()
                button_config_performance.disable()
                widget_map['problem']['n_init_sample'].disable()
                button_browse_x_init.disable()
                button_browse_y_init.disable()
                widget_x_init.disable()
                widget_y_init.disable()

            def gui_select_problem(event):
                '''
                Select problem to configure
                '''
                for key in ['n_var', 'n_obj', 'ref_point', 'n_init_sample']:
                    widget_map['problem'][key].enable()
                button_config_design.enable()
                button_config_performance.enable()
                button_browse_x_init.enable()
                button_browse_y_init.enable()
                widget_x_init.enable()
                widget_y_init.enable()

                name = event.widget.get()
                config = get_problem_config(name)
                for key in ['n_var', 'n_obj']:
                    widget_map['problem'][key].set(config[key])
                
                for key in ['var_name', 'var_lb', 'var_ub', 'obj_name', 'obj_lb', 'obj_ub']:
                    problem_cfg.update({key: config[key]})
                
                init_sample_path = config['init_sample_path']
                if init_sample_path is not None:
                    if isinstance(init_sample_path, list) and len(init_sample_path) == 2:
                        x_init_path, y_init_path = init_sample_path[0], init_sample_path[1]
                        widget_x_init.set(x_init_path)
                        widget_y_init.set(y_init_path)
                    elif isinstance(init_sample_path, str):
                        x_init_path = init_sample_path
                        widget_x_init.set(x_init_path)
                    else:
                        tk.messagebox.showinfo('Error', 'Error in problem definition: init_sample_path must be specified as 1) a list [x_path, y_path]; or 2) a string x_path', parent=window)

            widget_map['problem']['name'].widget.bind('<<ComboboxSelected>>', gui_select_problem)

            # algorithm subsection
            frame_algorithm = create_widget('labeled_frame', master=frame_param, row=1, column=0, text='Algorithm')
            grid_configure(frame_algorithm, [0], [0])
            widget_map['algorithm']['name'] = create_widget('labeled_combobox', 
                master=frame_algorithm, row=0, column=0, text=self.name_map['algorithm']['name'], values=get_available_algorithms(), required=True)
            widget_map['algorithm']['n_process'] = create_widget('labeled_entry', 
                master=frame_algorithm, row=1, column=0, text=self.name_map['algorithm']['n_process'], class_type='int', default=1, 
                valid_check=lambda x: x > 0, error_msg='number of processes to use must be positive')

            def gui_select_algorithm(event):
                '''
                Select algorithm
                '''
                button_advanced.enable()

            widget_map['algorithm']['name'].widget.bind('<<ComboboxSelected>>', gui_select_algorithm)

            def gui_set_advanced():
                '''
                Set advanced settings of algorithm
                '''
                window_advanced = tk.Toplevel(master=window)
                window_advanced.title('Advanced Settings')
                window_advanced.resizable(False, False)

                widget_map_algo = {
                    'surrogate': {}, 
                    'acquisition': {}, 
                    'solver': {},
                    'selection': {},
                }

                # parameter section
                frame_param_algo = tk.Frame(master=window_advanced)
                frame_param_algo.grid(row=0, column=0)
                grid_configure(frame_param_algo, [0, 1, 2], [0])

                # TODO: decouple setting default values from widgets creation

                # surrogate model subsection
                frame_surrogate = create_widget('labeled_frame', master=frame_param_algo, row=0, column=0, text='Surrogate Model')
                grid_configure(frame_surrogate, [0, 1, 2, 3], [0])
                widget_map_algo['surrogate']['name'] = create_widget('labeled_combobox',
                    master=frame_surrogate, row=0, column=0, width=20, text=self.name_map_algo['surrogate']['name'], 
                    values=list(self.value_map_algo['surrogate']['name'].values()), required=True)
                widget_map_algo['surrogate']['nu'] = create_widget('labeled_combobox',
                    master=frame_surrogate, row=1, column=0, width=5, text=self.name_map_algo['surrogate']['nu'], values=[1, 3, 5, -1],
                    class_type='int', default=5)
                widget_map_algo['surrogate']['n_spectral_pts'] = create_widget('labeled_entry',
                    master=frame_surrogate, row=2, column=0, text=self.name_map_algo['surrogate']['n_spectral_pts'], class_type='int', default=100,
                    valid_check=lambda x: x > 0, error_msg='number of spectral sampling points must be positive')
                widget_map_algo['surrogate']['mean_sample'] = create_widget('checkbutton',
                    master=frame_surrogate, row=3, column=0, text=self.name_map_algo['surrogate']['mean_sample'])

                surrogate_ts_visible = [False]
                widget_map_algo['surrogate']['n_spectral_pts'].widget.master.grid_remove()
                widget_map_algo['surrogate']['mean_sample'].master.grid_remove()

                def gui_select_surrogate(event):
                    '''
                    Select surrogate model type
                    '''
                    name = event.widget.get()
                    if name == 'Gaussian Process' or name == 'Neural Network': # TODO
                        if surrogate_ts_visible[0]:
                            widget_map_algo['surrogate']['n_spectral_pts'].widget.master.grid_remove()
                            widget_map_algo['surrogate']['mean_sample'].master.grid_remove()
                            surrogate_ts_visible[0] = False
                    elif name == 'Thompson Sampling':
                        if not surrogate_ts_visible[0]:
                            widget_map_algo['surrogate']['n_spectral_pts'].widget.master.grid()
                            widget_map_algo['surrogate']['mean_sample'].master.grid()
                            surrogate_ts_visible[0] = True
                    else:
                        raise NotImplementedError

                widget_map_algo['surrogate']['name'].widget.bind('<<ComboboxSelected>>', gui_select_surrogate)

                # acquisition function subsection
                frame_acquisition = create_widget('labeled_frame', master=frame_param_algo, row=1, column=0, text='Acquisition Function')
                grid_configure(frame_acquisition, [0], [0])
                widget_map_algo['acquisition']['name'] = create_widget('labeled_combobox',
                    master=frame_acquisition, row=0, column=0, width=25, text=self.name_map_algo['acquisition']['name'], 
                    values=list(self.value_map_algo['acquisition']['name'].values()), required=True)

                # multi-objective solver subsection
                frame_solver = create_widget('labeled_frame', master=frame_param_algo, row=2, column=0, text='Multi-Objective Solver')
                grid_configure(frame_solver, [0, 1, 2, 3], [0])
                widget_map_algo['solver']['name'] = create_widget('labeled_combobox',
                    master=frame_solver, row=0, column=0, width=15, text=self.name_map_algo['solver']['name'], 
                    values=list(self.value_map_algo['solver']['name'].values()), required=True)
                widget_map_algo['solver']['n_gen'] = create_widget('labeled_entry',
                    master=frame_solver, row=1, column=0, text=self.name_map_algo['solver']['n_gen'], class_type='int', default=200,
                    valid_check=lambda x: x > 0, error_msg='number of generations must be positive')
                widget_map_algo['solver']['pop_size'] = create_widget('labeled_entry',
                    master=frame_solver, row=2, column=0, text=self.name_map_algo['solver']['pop_size'], class_type='int', default=100,
                    valid_check=lambda x: x > 0, error_msg='population size must be positive')
                widget_map_algo['solver']['pop_init_method'] = create_widget('labeled_combobox',
                    master=frame_solver, row=3, column=0, width=25, text=self.name_map_algo['solver']['pop_init_method'], 
                    values=list(self.value_map_algo['solver']['pop_init_method'].values()), default='Non-Dominated Sort')

                # selection method subsection
                frame_selection = create_widget('labeled_frame', master=frame_param_algo, row=3, column=0, text='Selection Method')
                grid_configure(frame_selection, [0], [0])
                widget_map_algo['selection']['name'] = create_widget('labeled_combobox',
                    master=frame_selection, row=0, column=0, width=25, text=self.name_map_algo['selection']['name'], 
                    values=list(self.value_map_algo['selection']['name'].values()), required=True)

                def load_curr_config_algo():
                    '''
                    Load advanced settings of algorithm
                    '''
                    if algo_cfg == {}:
                        algo_cfg.update(self.config['algorithm'])
                        algo_cfg.pop('name')
                        algo_cfg.pop('n_process')
                    for cfg_type, val_map in widget_map_algo.items():
                        for cfg_name, widget in val_map.items():
                            if cfg_name not in algo_cfg[cfg_type]: continue
                            val = algo_cfg[cfg_type][cfg_name]
                            if cfg_name in self.value_map_algo[cfg_type]:
                                widget.set(self.value_map_algo[cfg_type][cfg_name][val])
                            else:
                                widget.set(val)
                    
                    widget_map_algo['surrogate']['name'].select()

                def gui_save_config_algo():
                    '''
                    Save advanced settings of algorithm
                    '''
                    temp_cfg = {}
                    for cfg_type, val_map in widget_map_algo.items():
                        temp_cfg[cfg_type] = {}
                        for cfg_name, widget in val_map.items():
                            try:
                                val = widget.get()
                            except:
                                show_widget_error(master=window_advanced, widget=widget, name=self.name_map_algo[cfg_type][cfg_name])
                                return
                            if cfg_name in self.value_inv_map_algo[cfg_type]:
                                val = self.value_inv_map_algo[cfg_type][cfg_name][val]
                            temp_cfg[cfg_type][cfg_name] = val

                    window_advanced.destroy()

                    for key, val in temp_cfg.items():
                        algo_cfg[key] = val

                # action section
                frame_action = tk.Frame(master=window_advanced)
                frame_action.grid(row=1, column=0)
                create_widget('button', master=frame_action, row=0, column=0, text='Save', command=gui_save_config_algo)
                create_widget('button', master=frame_action, row=0, column=1, text='Cancel', command=window_advanced.destroy)

                # load current config values to entry if not first time setting config
                if change and widget_map['algorithm']['name'].get() == self.config['algorithm']['name']:
                    load_curr_config_algo()

            button_advanced = create_widget('button', master=frame_algorithm, row=2, column=0, text='Advanced Settings', command=gui_set_advanced, sticky=None)
            button_advanced.disable()

            # evaluation subsection
            frame_general = create_widget('labeled_frame', master=frame_param, row=2, column=0, text='Evaluation')
            grid_configure(frame_general, [0], [0])
            widget_map['general']['n_worker'] = create_widget('labeled_entry',
                master=frame_general, row=1, column=0, text=self.name_map['general']['n_worker'], class_type='int', default=1,
                valid_check=lambda x: x > 0, error_msg='max number of evaluation workers must be positive')

            def load_curr_config():
                '''
                Set values of widgets as current configuration values
                '''
                for cfg_type, val_map in widget_map.items():
                    for cfg_name, widget in val_map.items():
                        widget.enable()
                        widget.set(self.config[cfg_type][cfg_name])
                        if not widget.changeable:
                            widget.disable()
                button_advanced.enable()
                problem_cfg.clear()
                problem_cfg.update(self.config['problem'])

            def gui_save_config():
                '''
                Save specified configuration values
                '''
                config = {
                    'general': {}, 
                    'problem': {}, 
                    'algorithm': {},
                }

                # specifically deal with provided initial samples
                try:
                    x_init_path = widget_x_init.get()
                except:
                    show_widget_error(master=window, widget=widget_x_init, name='Path of provided initial design variables')
                    return
                try:
                    y_init_path = widget_y_init.get()
                except:
                    show_widget_error(master=window, widget=widget_y_init, name='Path of provided initial performance values')
                    return

                if x_init_path is None and y_init_path is None: # no path of initial samples is provided
                    config['problem']['init_sample_path'] = None
                elif x_init_path is None: # only path of initial Y is provided, error
                    tk.messagebox.showinfo('Error', 'Only path of initial performance values is provided', parent=window)
                    return
                elif y_init_path is None: # only path of initial X is provided
                    config['problem']['init_sample_path'] = x_init_path
                else: # both path of initial X and initial Y are provided
                    config['problem']['init_sample_path'] = [x_init_path, y_init_path]

                # set config values from widgets
                for cfg_type, val_map in widget_map.items():
                    for cfg_name, widget in val_map.items():
                        try:
                            config[cfg_type][cfg_name] = widget.get()
                        except:
                            show_widget_error(master=window, widget=widget, name=self.name_map[cfg_type][cfg_name])
                            return

                # validity check
                n_var, n_obj = config['problem']['n_var'], config['problem']['n_obj']
                if n_var != len(problem_cfg['var_name']):
                    tk.messagebox.showinfo('Error', 'Number of design variables changed, please reconfigure design space', parent=window)
                    return
                if n_obj != len(problem_cfg['obj_name']):
                    tk.messagebox.showinfo('Error', 'Number of objectives changed, please reconfigure performance space', parent=window)
                    return

                if x_init_path is None and widget_map['problem']['n_init_sample'].get() == 0:
                    tk.messagebox.showinfo('Error', 'Either number of initial samples or path of initial design variables needs to be provided', parent=window)
                    return

                config['problem'].update(problem_cfg)
                config['algorithm'].update(algo_cfg)

                self._set_config(config, window)
                window.destroy()

            # action section
            frame_action = tk.Frame(master=window)
            frame_action.grid(row=1, column=0, columnspan=3)
            create_widget('button', master=frame_action, row=0, column=0, text='Save', command=gui_save_config)
            create_widget('button', master=frame_action, row=0, column=1, text='Cancel', command=window.destroy)

            # load current config values to entry if not first time setting config
            if change:
                load_curr_config()

        def gui_create_config():
            '''
            Create config from GUI
            '''
            gui_build_config_window(change=False)

        def gui_change_config():
            '''
            Change config from GUI
            '''
            gui_build_config_window(change=True)

        # link menu command
        self.menu_config.entryconfig(0, command=gui_load_config)
        self.menu_config.entryconfig(1, command=gui_create_config)
        self.menu_config.entryconfig(2, command=gui_change_config, state=tk.DISABLED)

    def _init_problem_menu(self):
        '''
        Problem menu initialization
        '''
        self.menu_problem.add_command(label='Manage')

        def gui_manage_problem():
            '''
            Manage problems
            '''
            window = tk.Toplevel(master=self.root)
            window.title('Manage Problem')
            window.resizable(False, False)

            # problem section
            frame_problem = create_widget('frame', master=window, row=0, column=0)
            frame_list = create_widget('labeled_frame', master=frame_problem, row=0, column=0, text='Problem List')
            frame_list_display = create_widget('frame', master=frame_list, row=0, column=0, padx=5, pady=5)
            frame_list_action = create_widget('frame', master=frame_list, row=1, column=0, padx=0, pady=0)
            frame_config = create_widget('labeled_frame', master=frame_problem, row=0, column=1, text='Problem Config')
            frame_config_display = create_widget('frame', master=frame_config, row=0, column=0, padx=0, pady=0)
            frame_config_action = create_widget('frame', master=frame_config, row=1, column=0, padx=0, pady=0, sticky=None)
            
            grid_configure(frame_list, [0], [0])

            # list subsection
            listbox_problem = Listbox(master=frame_list_display)
            listbox_problem.grid()
            
            button_create = create_widget('button', master=frame_list_action, row=0, column=0, text='Create')
            button_delete = create_widget('button', master=frame_list_action, row=0, column=1, text='Delete')

            # config subsection
            widget_map = {}
            widget_map['name'] = create_widget('labeled_entry', 
                master=frame_config_display, row=0, column=0, text=self.name_map['problem']['name'], class_type='string', width=15, required=True)
            widget_map['n_var'] = create_widget('labeled_entry', 
                master=frame_config_display, row=1, column=0, text=self.name_map['problem']['n_var'], class_type='int', required=True,
                valid_check=lambda x: x > 0, error_msg='number of design variables must be positive')
            widget_map['n_obj'] = create_widget('labeled_entry', 
                master=frame_config_display, row=2, column=0, text=self.name_map['problem']['n_obj'], class_type='int', required=True,
                valid_check=lambda x: x > 1, error_msg='number of objectives must be greater than 1')
            widget_map['n_constr'] = create_widget('labeled_entry', 
                master=frame_config_display, row=3, column=0, text=self.name_map['problem']['n_constr'], class_type='int', default=0, 
                valid_check=lambda x: x >= 0, error_msg='number of constraints must be positive')

            problem_cfg = {}

            frame_config_space = tk.Frame(master=frame_config_display)
            frame_config_space.grid(row=4, column=0)
            button_config_design = create_widget('button', master=frame_config_space, row=0, column=0, text='Configure design space')
            button_config_performance = create_widget('button', master=frame_config_space, row=0, column=1, text='Configure performance space')

            def gui_set_performance_script():
                '''
                Set path of performance evaluation script
                '''
                filename = tk.filedialog.askopenfilename(parent=window)
                if not isinstance(filename, str) or filename == '': return
                widget_map['performance_eval'].set(filename)

            def performance_script_valid_check(path):
                '''
                Check validity of performance script located at path
                '''
                if path is None:
                    return False
                try:
                    module = import_module_from_path('eval_check', path)
                    module.evaluate_performance
                except:
                    return False
                return True

            button_browse_performance, widget_map['performance_eval'] = create_widget('labeled_button_entry',
                master=frame_config_display, row=5, column=0, label_text=self.name_map['problem']['performance_eval'], button_text='Browse', command=gui_set_performance_script,
                width=30, valid_check=performance_script_valid_check, error_msg="performance evaluation script doesn't exist or no evaluate_performance() function inside")

            def gui_set_constraint_script():
                '''
                Set path of constraint evaluation script
                '''
                filename = tk.filedialog.askopenfilename(parent=window)
                if not isinstance(filename, str) or filename == '': return
                widget_map['constraint_eval'].set(filename)

            def constraint_script_valid_check(path):
                '''
                Check validity of constraint script located at path
                '''
                if path is None:
                    return False
                try:
                    module = import_module_from_path('eval_check', path)
                    module.evaluate_constraint
                except:
                    return False
                return True

            button_browse_constraint, widget_map['constraint_eval'] = create_widget('labeled_button_entry',
                master=frame_config_display, row=6, column=0, label_text=self.name_map['problem']['constraint_eval'], button_text='Browse', command=gui_set_constraint_script,
                width=30, valid_check=constraint_script_valid_check, error_msg="constraint evaluation script doesn't exist or no evaluate_constraint() function inside")

            button_save = create_widget('button', master=frame_config_action, row=0, column=0, text='Save')
            button_cancel = create_widget('button', master=frame_config_action, row=0, column=1, text='Cancel')

            def gui_set_design_space():
                '''
                Set design space parameters
                '''
                # validity check
                try:
                    n_var = widget_map['n_var'].get()
                except:
                    error_msg = widget_map['n_var'].get_error_msg()
                    error_msg = '' if error_msg is None else ': ' + error_msg
                    tk.messagebox.showinfo('Error', 'Invalid value for "' + self.name_map['problem']['n_var'] + '"' + error_msg, parent=window)
                    return

                titles = ['var_name', 'var_lb', 'var_ub']

                window_design = tk.Toplevel(master=window)
                window_design.title('Configure Design Space')
                window_design.resizable(False, False)

                # design space section
                frame_design = create_widget('labeled_frame', master=window_design, row=0, column=0, text='Design Space')
                create_widget('label', master=frame_design, row=0, column=0, text='Enter the properties for design variables:')
                excel_design = Excel(master=frame_design, rows=n_var, columns=3, width=15,
                    title=[self.name_map['problem'][title] for title in titles], dtype=[str, float, float], default=[None, 0, 1])
                excel_design.grid(row=1, column=0)
                excel_design.set_column(0, [f'x{i + 1}' for i in range(n_var)])

                # load configured design space
                for column, key in enumerate(titles):
                    if key in problem_cfg:
                        excel_design.set_column(column, problem_cfg[key])

                def gui_save_design_space():
                    '''
                    Save design space parameters
                    '''
                    temp_cfg = {}
                    for column, key in enumerate(titles):
                        try:
                            temp_cfg[key] = excel_design.get_column(column)
                        except:
                            tk.messagebox.showinfo('Error', 'Invalid value for "' + self.name_map['problem'][key] + '"', parent=window_design)
                            return

                    window_design.destroy()

                    for key, val in temp_cfg.items():
                        problem_cfg[key] = val

                # action section
                frame_action = tk.Frame(master=window_design)
                frame_action.grid(row=1, column=0)
                create_widget('button', master=frame_action, row=0, column=0, text='Save', command=gui_save_design_space)
                create_widget('button', master=frame_action, row=0, column=1, text='Cancel', command=window_design.destroy)

            def gui_set_performance_space():
                '''
                Set performance space parameters
                '''
                # validity check
                try:
                    n_obj = widget_map['n_obj'].get()
                except:
                    error_msg = widget_map['n_obj'].get_error_msg()
                    error_msg = '' if error_msg is None else ': ' + error_msg
                    tk.messagebox.showinfo('Error', 'Invalid value for "' + self.name_map['problem']['n_obj'] + '"' + error_msg, parent=window)
                    return

                titles = ['obj_name', 'obj_lb', 'obj_ub']

                window_performance = tk.Toplevel(master=window)
                window_performance.title('Configure Performance Space')
                window_performance.resizable(False, False)

                # performance space section
                frame_performance = create_widget('labeled_frame', master=window_performance, row=0, column=0, text='Performance Space')
                create_widget('label', master=frame_performance, row=0, column=0, text='Enter the properties for objectives:')
                excel_performance = Excel(master=frame_performance, rows=n_obj, columns=3, width=15,
                    title=[self.name_map['problem'][title] for title in titles], dtype=[str, float, float])
                excel_performance.grid(row=1, column=0)
                excel_performance.set_column(0, [f'f{i + 1}' for i in range(n_obj)])

                # load configured performance space
                for column, key in enumerate(titles):
                    if key in problem_cfg:
                        excel_performance.set_column(column, problem_cfg[key])

                def gui_save_performance_space():
                    '''
                    Save performance space parameters
                    '''
                    temp_cfg = {}
                    for column, key in enumerate(titles):
                        try:
                            temp_cfg[key] = excel_performance.get_column(column)
                        except:
                            tk.messagebox.showinfo('Error', 'Invalid value for "' + self.name_map['problem'][key] + '"', parent=window_performance)
                            return
                    
                    window_performance.destroy()

                    for key, val in temp_cfg.items():
                        problem_cfg[key] = val

                # action section
                frame_action = tk.Frame(master=window_performance)
                frame_action.grid(row=1, column=0)
                create_widget('button', master=frame_action, row=0, column=0, text='Save', command=gui_save_performance_space)
                create_widget('button', master=frame_action, row=0, column=1, text='Cancel', command=window_performance.destroy)

            def exit_creating_problem():
                '''
                Exit creating problem status
                '''
                self.in_creating_problem = False
                button_create.enable()
                listbox_problem.delete(tk.END)

            def enable_config_widgets():
                '''
                Enable all config widgets
                '''
                for button in [button_save, button_cancel, button_config_design, button_config_performance, button_browse_performance, button_browse_constraint]:
                    button.enable()
                for widget in widget_map.values():
                    widget.enable()
                    widget.set(None)

            def disable_config_widgets():
                '''
                Disable all config widgets
                '''
                for button in [button_save, button_cancel, button_config_design, button_config_performance, button_browse_performance, button_browse_constraint]:
                    button.disable()
                for widget in widget_map.values():
                    widget.set(None)
                    widget.disable()

            def save_entry_values(entry_map, config):
                '''
                Save values of entries to config dict
                '''
                temp_config = {}
                for name, widget in entry_map.items():
                    try:
                        temp_config[name] = widget.get()
                    except:
                        error_msg = widget.get_error_msg()
                        error_msg = '' if error_msg is None else ': ' + error_msg
                        tk.messagebox.showinfo('Error', 'Invalid value for "' + self.name_map['problem'][name] + '"' + error_msg, parent=window)
                        raise Exception()
                for key, val in temp_config.items():
                    config[key] = val

            def load_entry_values(entry_map, config):
                '''
                Load values of entries from config dict
                '''
                for name, widget in entry_map.items():
                    widget.set(config[name])

            def gui_save_change():
                '''
                Save changes to problem
                '''
                if self.in_creating_problem:
                    # try to save changes
                    try:
                        name = widget_map['name'].get()
                    except:
                        error_msg = widget_map['name'].get_error_msg()
                        error_msg = '' if error_msg is None else ': ' + error_msg
                        tk.messagebox.showinfo('Error', 'Invalid value for "' + self.name_map['problem']['name'] + '"' + error_msg, parent=window)
                        return

                    if name in get_problem_list():
                        tk.messagebox.showinfo('Error', f'Problem {name} already exists', parent=window)
                        return
                    try:
                        save_entry_values(widget_map, problem_cfg)
                    except:
                        return
                    self.manager_problem.save_problem(problem_cfg)
                    tk.messagebox.showinfo('Success', f'Problem {name} saved', parent=window)
                    
                    # reload
                    exit_creating_problem()
                    listbox_problem.reload()
                    listbox_problem.select(name)
                else:
                    old_name = listbox_problem.get(tk.ANCHOR)
                    if_save = tk.messagebox.askquestion('Save Changes', f'Are you sure to save the changes for problem "{old_name}"?', parent=window)

                    if if_save == 'yes':
                        # try to save changes
                        new_name = widget_map['name'].get()
                        if old_name != new_name: # problem name changed
                            if new_name in get_problem_list():
                                tk.messagebox.showinfo('Error', f'Problem {new_name} already exists', parent=window)
                                return
                        try:
                            save_entry_values(widget_map, problem_cfg)
                        except:
                            return
                        if old_name != new_name:
                            self.manager_problem.remove_problem(old_name)
                        self.manager_problem.save_problem(problem_cfg)
                        tk.messagebox.showinfo('Success', f'Problem {problem_cfg["name"]} saved', parent=window)

                        # reload
                        listbox_problem.reload()
                        listbox_problem.select(new_name)
                    else:
                        # cancel changes
                        return

            def gui_cancel_change():
                '''
                Cancel changes to problem
                '''
                if self.in_creating_problem:
                    exit_creating_problem()
                    disable_config_widgets()
                listbox_problem.select_event()

            def gui_create_problem():
                '''
                Create new problem
                '''
                self.in_creating_problem = True
                
                listbox_problem.insert(tk.END, '')
                listbox_problem.select_clear(0, tk.END)
                listbox_problem.select_set(tk.END)

                enable_config_widgets()
                button_create.disable()
                button_delete.disable()

            def gui_delete_problem():
                '''
                Delete selected problem
                '''
                index = int(listbox_problem.curselection()[0])
                name = listbox_problem.get(index)
                if_delete = tk.messagebox.askquestion('Delete Problem', f'Are you sure to delete problem "{name}"?', parent=window)
                if if_delete == 'yes':
                    listbox_problem.delete(index)
                    listbox_size = listbox_problem.size()
                    if listbox_size == 0:
                        button_delete.disable()
                        disable_config_widgets()
                    else:
                        listbox_problem.select_set(min(index, listbox_size - 1))
                        listbox_problem.select_event()
                    self.manager_problem.remove_problem(name)
                else:
                    return

            def gui_select_problem(event):
                '''
                Select problem, load problem config
                '''
                try:
                    index = int(event.widget.curselection()[0])
                except:
                    return
                name = event.widget.get(index)
                if name == '':
                    return
                elif self.in_creating_problem:
                    exit_creating_problem()

                enable_config_widgets()
                config = self.manager_problem.load_problem(name)
                load_entry_values(widget_map, config)

                button_delete.enable()

            listbox_problem.bind_cmd(reload_cmd=get_yaml_problem_list, select_cmd=gui_select_problem)
            listbox_problem.reload()

            button_config_design.configure(command=gui_set_design_space)
            button_config_performance.configure(command=gui_set_performance_space)
            button_save.configure(command=gui_save_change)
            button_cancel.configure(command=gui_cancel_change)
            button_create.configure(command=gui_create_problem)
            button_delete.configure(command=gui_delete_problem)
            button_delete.disable()
            disable_config_widgets()

        self.menu_problem.entryconfig(0, command=gui_manage_problem)

    def _init_worker_menu(self):
        '''
        Worker menu initialization
        '''
        self.menu_worker.add_command(label='Manage')

        def gui_manage_worker():
            '''
            Manage workers
            '''
            window = tk.Toplevel(master=self.root)
            window.title('Manage Worker')
            window.resizable(False, False)

            # worker section
            frame_worker = create_widget('frame', master=window, row=0, column=0)
            frame_list = create_widget('labeled_frame', master=frame_worker, row=0, column=0, text='Worker List')
            frame_list_display = create_widget('frame', master=frame_list, row=0, column=0, padx=5, pady=5)
            frame_list_action = create_widget('frame', master=frame_list, row=1, column=0, padx=0, pady=0)
            frame_config = create_widget('labeled_frame', master=frame_worker, row=0, column=1, text='Worker Config')
            frame_config_display = create_widget('frame', master=frame_config, row=0, column=0, padx=0, pady=0)
            frame_config_action = create_widget('frame', master=frame_config, row=1, column=0, padx=0, pady=0, sticky=None)
            
            grid_configure(frame_list, [0], [0])
            grid_configure(frame_config, [0], [0])

            # list subsection
            listbox_worker = Listbox(master=frame_list_display)
            listbox_worker.grid()
            
            button_create = create_widget('button', master=frame_list_action, row=0, column=0, text='Create')
            button_delete = create_widget('button', master=frame_list_action, row=0, column=1, text='Delete')

            # config subsection
            worker_cfg = {}
            widget_map = {}

            widget_map['id'] = create_widget('labeled_entry', master=frame_config_display, row=0, column=0, text=self.name_map_worker['id'],
                class_type='string', width=10, required=True, valid_check=lambda x: x not in self.manager_worker.list_worker(), error_msg='duplicate worker ID')
            widget_map['name'] = create_widget('labeled_entry', master=frame_config_display, row=1, column=0, text=self.name_map_worker['name'],
                class_type='string', width=10)
            widget_map['timeout'] = create_widget('labeled_entry', master=frame_config_display, row=2, column=0, text=self.name_map_worker['timeout'],
                class_type='float', width=10, valid_check=lambda x: x > 0, error_msg='timeout must be positive')

            button_save = create_widget('button', master=frame_config_action, row=0, column=0, text='Save')
            button_cancel = create_widget('button', master=frame_config_action, row=0, column=1, text='Cancel')

            def exit_creating_worker():
                '''
                Exit creating worker status
                '''
                self.in_creating_worker = False
                button_create.enable()
                listbox_worker.delete(tk.END)

            def enable_config_widgets():
                '''
                Enable all config widgets
                '''
                for button in [button_save, button_cancel]:
                    button.enable()
                for widget in widget_map.values():
                    widget.enable()
                    widget.set(None)

            def disable_config_widgets():
                '''
                Disable all config widgets
                '''
                for button in [button_save, button_cancel]:
                    button.disable()
                for widget in widget_map.values():
                    widget.set(None)
                    widget.disable()

            def save_entry_values(entry_map, config):
                '''
                Save values of entries to config dict
                '''
                temp_config = {}
                for name, widget in entry_map.items():
                    try:
                        temp_config[name] = widget.get()
                    except:
                        error_msg = widget.get_error_msg()
                        error_msg = '' if error_msg is None else ': ' + error_msg
                        tk.messagebox.showinfo('Error', 'Invalid value for "' + self.name_map_worker[name] + '"' + error_msg, parent=window)
                        raise Exception()
                for key, val in temp_config.items():
                    config[key] = val

            def load_entry_values(entry_map, config):
                '''
                Load values of entries from config dict
                '''
                for name, widget in entry_map.items():
                    widget.set(config[name])

            def gui_save_change():
                '''
                Save changes to worker
                '''
                if self.in_creating_worker:
                    # try to save changes
                    try:
                        save_entry_values(widget_map, worker_cfg)
                    except:
                        return
                    self.manager_worker.save_worker(worker_cfg)
                    wid = worker_cfg['id']
                    tk.messagebox.showinfo('Success', f'Worker {wid} saved', parent=window)
                    
                    # reload
                    exit_creating_worker()
                    listbox_worker.reload()
                    listbox_worker.select(wid)
                else:
                    old_wid = listbox_worker.get(tk.ANCHOR)
                    if_save = tk.messagebox.askquestion('Save Changes', f'Are you sure to save the changes for worker "{old_wid}"?', parent=window)

                    if if_save == 'yes':
                        # try to save changes
                        try:
                            save_entry_values(widget_map, worker_cfg)
                        except:
                            return
                        new_wid = worker_cfg['id']
                        if old_wid != new_wid:
                            self.manager_worker.remove_worker(old_wid)
                        self.manager_worker.save_worker(new_wid)
                        tk.messagebox.showinfo('Success', f'Worker {new_wid} saved', parent=window)

                        # reload
                        listbox_worker.reload()
                        listbox_worker.select(new_wid)
                    else:
                        # cancel changes
                        return

            def gui_cancel_change():
                '''
                Cancel changes to worker
                '''
                if self.in_creating_worker:
                    exit_creating_worker()
                    disable_config_widgets()
                listbox_worker.select_event()

            def gui_create_worker():
                '''
                Create new worker
                '''
                self.in_creating_worker = True
                
                listbox_worker.insert(tk.END, '')
                listbox_worker.select_clear(0, tk.END)
                listbox_worker.select_set(tk.END)

                enable_config_widgets()
                button_create.disable()
                button_delete.disable()

            def gui_delete_worker():
                '''
                Delete selected worker
                '''
                index = int(listbox_worker.curselection()[0])
                wid = listbox_worker.get(index)
                if_delete = tk.messagebox.askquestion('Delete Worker', f'Are you sure to delete worker "{wid}"?', parent=window)
                if if_delete == 'yes':
                    listbox_worker.delete(index)
                    listbox_size = listbox_worker.size()
                    if listbox_size == 0:
                        button_delete.disable()
                        disable_config_widgets()
                    else:
                        listbox_worker.select_set(min(index, listbox_size - 1))
                        listbox_worker.select_event()
                    self.manager_worker.remove_worker(wid)
                else:
                    return

            def gui_select_worker(event):
                '''
                Select worker, load worker config
                '''
                try:
                    index = int(event.widget.curselection()[0])
                except:
                    return
                wid = event.widget.get(index)
                if wid == '':
                    return
                elif self.in_creating_worker:
                    exit_creating_worker()

                enable_config_widgets()
                config = self.manager_worker.load_worker(wid)
                load_entry_values(widget_map, config)

                button_delete.enable()

            listbox_worker.bind_cmd(reload_cmd=self.manager_worker.list_worker, select_cmd=gui_select_worker)
            listbox_worker.reload()

            button_save.configure(command=gui_save_change)
            button_cancel.configure(command=gui_cancel_change)
            button_create.configure(command=gui_create_worker)
            button_delete.configure(command=gui_delete_worker)
            button_delete.disable()
            disable_config_widgets()

        # link menu command
        self.menu_worker.entryconfig(0, command=gui_manage_worker)

    def _init_log_menu(self):
        '''
        Log menu initialization
        '''
        self.menu_log.add_command(label='Clear')

        def gui_log_clear():
            '''
            Clear texts in GUI log
            '''
            self.scrtext_log.configure(state=tk.NORMAL)
            self.scrtext_log.delete('1.0', tk.END)
            self.scrtext_log.configure(state=tk.DISABLED)

        # link menu command
        self.menu_log.entryconfig(0, command=gui_log_clear)
        
    def _init_widgets(self):
        '''
        Widgets initialization
        '''
        self._init_tab_widgets()
        self._init_control_widgets()
        self._init_log_widgets()

    def _init_tab_widgets(self):
        '''
        Tab widgets initialization (for visualization)
        '''
        frame_viz = tk.Frame(master=self.root)
        frame_viz.grid(row=0, column=0, rowspan=2, sticky='NSEW')
        grid_configure(frame_viz, [0], [0])

        # configure tab widgets
        self.nb_viz = ttk.Notebook(master=frame_viz)
        self.nb_viz.grid(row=0, column=0, sticky='NSEW')
        self.frame_plot = tk.Frame(master=self.nb_viz)
        self.frame_stat = tk.Frame(master=self.nb_viz)
        self.frame_db = tk.Frame(master=self.nb_viz)
        self.nb_viz.add(child=self.frame_plot, text='Visualization')
        self.nb_viz.add(child=self.frame_stat, text='Statistics')
        self.nb_viz.add(child=self.frame_db, text='Database')

        # temporarily disable tabs until data loaded
        self.nb_viz.tab(0, state=tk.DISABLED)
        self.nb_viz.tab(1, state=tk.DISABLED)
        self.nb_viz.tab(2, state=tk.DISABLED)

        # initialize tutorial image
        self.image_tutorial = ImageFrame(master=self.root, img_path='./tutorial.png')
        self.image_tutorial.grid(row=0, column=0, rowspan=2, sticky='NSEW')

    def _init_viz_widgets(self, problem):
        '''
        Visualization widgets initialization (design/performance space, statistics, database)
        '''
        n_var, n_obj = problem.n_var, problem.n_obj
        var_name, obj_name = problem.var_name, problem.obj_name
        var_lb, var_ub = problem.xl, problem.xu
        if var_lb is None: var_lb = np.zeros(n_var)
        if var_ub is None: var_ub = np.ones(n_var)

        assert n_obj in [2, 3], 'only 2 and 3 objectives are supported' # TODO

        grid_configure(self.frame_plot, [0], [0])
        grid_configure(self.frame_stat, [0], [0])
        grid_configure(self.frame_db, [1], [0])
        
        # figure placeholder in GUI
        self.fig1 = plt.figure(figsize=(10, 5))
        self.gs1 = GridSpec(1, 2, figure=self.fig1, width_ratios=[3, 2])
        self.fig2 = plt.figure(figsize=(10, 5))

        # connect matplotlib figure with tkinter GUI
        embed_figure(self.fig1, self.frame_plot)
        embed_figure(self.fig2, self.frame_stat)

        # performance space figure
        if n_obj == 2:
            self.ax11 = self.fig1.add_subplot(self.gs1[0])
        elif n_obj == 3:
            self.ax11 = self.fig1.add_subplot(self.gs1[0], projection='3d')
        else:
            raise NotImplementedError
        self.ax11.set_title('Performance Space')
        self.ax11.set_xlabel(obj_name[0])
        self.ax11.set_ylabel(obj_name[1])
        if n_obj == 3:
            self.ax11.set_zlabel(obj_name[2])

        # design space figure
        if n_var > 2:
            self.theta = radar_factory(n_var)
            self.ax12 = self.fig1.add_subplot(self.gs1[1], projection='radar')
            self.ax12.set_xticks(self.theta)
            self.ax12.set_varlabels(var_name)
            self.ax12.set_yticklabels([])
            self.ax12.set_title('Design Space', position=(0.5, 1.1))
            self.ax12.set_ylim(0, 1)
        else:
            self.ax12 = self.fig1.add_subplot(self.gs1[1])
            for spine in self.ax12.spines.values():
                spine.set_visible(False)
            self.ax12.get_xaxis().set_ticks([])
            self.ax12.get_yaxis().set_ticks([])
            xticks = [0] if n_var == 1 else [-1, 1]
            self.ax12.bar(xticks, [1] * n_var, color='g', alpha=0.2)
            self.ax12.set_xticks(xticks)
            for i in range(n_var):
                self.ax12.text(xticks[i] - 0.5, 0, str(var_lb[i]), horizontalalignment='right', verticalalignment='center')
                self.ax12.text(xticks[i] - 0.5, 1, str(var_ub[i]), horizontalalignment='right', verticalalignment='center')
            self.ax12.set_xticklabels(var_name)
            self.ax12.set_title('Design Space')
            self.ax12.set_xlim(-3, 3)
            self.ax12.set_ylim(0, 1.04)

        # hypervolume curve figure
        self.ax21 = self.fig2.add_subplot(121)
        self.ax21.set_title('Hypervolume')
        self.ax21.set_xlabel('Evaluations')
        self.ax21.set_ylabel('Hypervolume')
        self.ax21.xaxis.set_major_locator(MaxNLocator(integer=True))

        # model prediction error figure
        self.ax22 = self.fig2.add_subplot(122)
        self.ax22.set_title('Model Prediction Error')
        self.ax22.set_xlabel('Evaluations')
        self.ax22.set_ylabel('Average Error')
        self.ax22.xaxis.set_major_locator(MaxNLocator(integer=True))

        # configure slider widget
        frame_slider = tk.Frame(master=self.frame_plot)
        frame_slider.grid(row=2, column=0, padx=5, pady=0, sticky='EW')
        grid_configure(frame_slider, [0], [1])
        
        label_iter = tk.Label(master=frame_slider, text='Iteration:')
        label_iter.grid(row=0, column=0, sticky='EW')
        self.scale_iter = tk.Scale(master=frame_slider, orient=tk.HORIZONTAL, variable=self.curr_iter, from_=0, to=0)
        self.scale_iter.grid(row=0, column=1, sticky='EW')

        def gui_redraw_viz(val):
            '''
            Redraw design and performance space when slider changes
            '''
            # get current iteration from slider value
            curr_iter = int(val)

            # clear design space
            self._clear_design_space()

            # replot performance space
            self._redraw_performance_space(curr_iter)

        self.scale_iter.configure(command=gui_redraw_viz)

        # load from database
        X, Y, is_pareto = self.agent_data.load(['X', 'Y', 'is_pareto'])

        # update status
        self.n_init_sample = len(Y)
        self.n_sample = self.n_init_sample
        self.n_valid_sample = self.n_init_sample

        # calculate pfront limit (for rescale plot afterwards)
        if self.true_pfront is not None:
            self.pfront_limit = [np.min(self.true_pfront, axis=1), np.max(self.true_pfront, axis=1)]

        # plot performance space
        scatter_list = []
        if self.true_pfront is not None:
            scatter_pfront = self.ax11.scatter(*self.true_pfront.T, color='gray', s=5, label='Oracle') # plot true pareto front
            scatter_list.append(scatter_pfront)
        self.scatter_x = X
        self.scatter_y = self.ax11.scatter(*Y.T, color='blue', s=10, label='Evaluated')
        self.scatter_y_pareto = self.ax11.scatter(*Y[is_pareto].T, color='red', s=10, label='Pareto front')
        self.scatter_y_new = self.ax11.scatter([], [], color='m', s=10, label='New evaluated')
        self.scatter_y_pred = self.ax11.scatter([], [], facecolors=(0, 0, 0, 0), edgecolors='m', s=15, label='New predicted')
        scatter_list.extend([self.scatter_y, self.scatter_y_pareto, self.scatter_y_new, self.scatter_y_pred])

        # plot hypervolume curve
        hv_value = np.full(self.n_init_sample, calc_hypervolume(Y, self.config['problem']['ref_point']))
        self.line_hv = self.ax21.plot(list(range(self.n_init_sample)), hv_value)[0]
        self.ax21.set_title('Hypervolume: %.4f' % hv_value[-1])

        # plot prediction error curve
        self.line_error = self.ax22.plot([], [])[0]

        def check_design_values(event):
            '''
            Mouse clicking event, for checking design values
            '''
            if event.inaxes != self.ax11: return

            if event.button == MouseButton.LEFT and event.dblclick: # check certain design values
                # find nearest performance values with associated design values
                loc = [event.xdata, event.ydata]
                all_y = self.scatter_y._offsets
                closest_y, closest_idx = find_closest_point(loc, all_y, return_index=True)
                closest_x = self.scatter_x[closest_idx]
                if n_obj == 3:
                    closest_y = np.array(self.scatter_y._offsets3d).T[closest_idx]

                # clear checked design values
                self._clear_design_space()

                # highlight selected point
                self.scatter_selected = self.ax11.scatter(*closest_y, s=50, facecolors=(0, 0, 0, 0), edgecolors='g', linewidths=2)

                # plot checked design values as radar plot or bar chart
                transformed_x = (np.array(closest_x) - var_lb) / (var_ub - var_lb)
                if n_var > 2:
                    self.line_x = self.ax12.plot(self.theta, transformed_x, color='g')[0]
                    self.fill_x = self.ax12.fill(self.theta, transformed_x, color='g', alpha=0.2)[0]
                    self.ax12.set_varlabels([f'{var_name[i]}\n{closest_x[i]:.4g}' for i in range(n_var)])
                else:
                    self.bar_x = self.ax12.bar(xticks, transformed_x, color='g')
                    self.text_x = []
                    for i in range(n_var):
                        text = self.ax12.text(xticks[i], transformed_x[i], f'{closest_x[i]:.4g}', horizontalalignment='center', verticalalignment='bottom')
                        self.text_x.append(text)

            elif event.button == MouseButton.RIGHT: # clear checked design values
                self._clear_design_space()
                
            self.fig1.canvas.draw()
        
        self.fig1.canvas.mpl_connect('button_press_event', check_design_values)

        # set pick event on legend to enable/disable certain visualization
        legend = self.fig1.legend(loc='lower center', ncol=5)
        picker_map = {}
        for plot_obj, leg_obj, text in zip(scatter_list, legend.legendHandles, legend.get_texts()):
            leg_obj.set_picker(True)
            text.set_picker(True)
            picker_map[leg_obj] = plot_obj
            picker_map[text] = plot_obj

        def toggle_visibility(event):
            '''
            Toggle visibility of plotted objs
            '''
            plot_obj = picker_map[event.artist]
            vis = not plot_obj.get_visible()
            plot_obj.set_visible(vis)

            if not self.scatter_y_new.get_visible() or not self.scatter_y_pred.get_visible():
                for line in self.line_y_pred_list:
                    line.set_visible(False)
            if self.scatter_y_new.get_visible() and self.scatter_y_pred.get_visible():
                for line in self.line_y_pred_list:
                    line.set_visible(True)

            self.fig1.canvas.draw()
        
        self.fig1.canvas.mpl_connect('pick_event', toggle_visibility)

        # adjust layout
        self.fig1.subplots_adjust(bottom=0.15)
        self.fig2.tight_layout()

        # refresh figure
        self.fig1.canvas.draw()
        self.fig2.canvas.draw()

        def gui_enter_design():
            '''
            Enter design variables from database panel
            '''
            window = tk.Toplevel(master=self.frame_db)
            window.title('Enter Design Variables')
            window.resizable(False, False)

            frame_n_row = create_widget('frame', master=window, row=0, column=0, sticky=None, pady=0)
            entry_n_row = create_widget('labeled_entry',
                master=frame_n_row, row=0, column=0, text='Number of rows', class_type='int', default=1, 
                valid_check=lambda x: x > 0, error_msg='number of rows must be positive')
            entry_n_row.set(1)
            button_n_row = create_widget('button', master=frame_n_row, row=0, column=1, text='Update')

            n_var = self.config['problem']['n_var']
            var_lb, var_ub = self.config['problem']['var_lb'], self.config['problem']['var_ub']
            if not (isinstance(var_lb, list) or isinstance(var_lb, np.ndarray)):
                var_lb = [var_lb] * n_var
            if not (isinstance(var_ub, list) or isinstance(var_ub, np.ndarray)):
                var_ub = [var_ub] * n_var
            excel_design = Excel(master=window, rows=1, columns=n_var, width=10, 
                title=[f'x{i + 1}' for i in range(n_var)], dtype=[float] * n_var, default=None, required=[True] * n_var, valid_check=[lambda x: x >= var_lb[i] and x <= var_ub[i] for i in range(n_var)])
            excel_design.grid(row=1, column=0)

            def gui_update_table():
                '''
                Update excel table of design variables to be added
                '''
                n_row = entry_n_row.get()
                excel_design.update_n_row(n_row)

            button_n_row.configure(command=gui_update_table)

            var_eval = create_widget('checkbutton', master=window, row=2, column=0, text='Automatically evaluate')

            def gui_add_design():
                '''
                Add input design variables, then predict (and evaluate)
                '''
                try:
                    X_next = np.atleast_2d(excel_design.get_all())
                except:
                    tk.messagebox.showinfo('Error', 'Invalid design values', parent=window)
                    return

                if_eval = var_eval.get() == 1 # TODO: fail when no eval script is linked
                window.destroy()

                # predict, add result to database
                rowids = self.agent_data.predict(self.config, self.config_id, X_next)
                self.opt_completed = True

                # call evaluation worker
                if if_eval:
                    for rowid in rowids:
                        self.agent_worker.add_eval_worker(rowid)

            frame_action = create_widget('frame', master=window, row=3, column=0, sticky=None, pady=0)
            create_widget('button', master=frame_action, row=0, column=0, text='Save', command=gui_add_design)
            create_widget('button', master=frame_action, row=0, column=1, text='Cancel', command=window.destroy)

        def gui_enter_performance():
            '''
            Enter performance values at certain rows from database panel
            '''
            window = tk.Toplevel(master=self.frame_db)
            window.title('Enter Performance Values')
            window.resizable(False, False)

            frame_n_row = create_widget('frame', master=window, row=0, column=0, sticky=None, pady=0)
            entry_n_row = create_widget('labeled_entry',
                master=frame_n_row, row=0, column=0, text='Number of rows', class_type='int', default=1, 
                valid_check=lambda x: x > 0, error_msg='number of rows must be positive')
            entry_n_row.set(1)
            button_n_row = create_widget('button', master=frame_n_row, row=0, column=1, text='Update')

            n_obj = self.config['problem']['n_obj']
            excel_performance = Excel(master=window, rows=1, columns=n_obj + 1, width=10, 
                title=['Row number'] + [f'f{i + 1}' for i in range(n_obj)], dtype=[int] + [float] * n_obj, default=None, required=[True] * (n_obj + 1), valid_check=[lambda x: x > 0 and x <= self.table_db.n_rows] + [None] * n_obj)
            excel_performance.grid(row=1, column=0)

            def gui_update_table():
                '''
                Update excel table of design variables to be added
                '''
                n_row = entry_n_row.get()
                excel_performance.update_n_row(n_row)

            button_n_row.configure(command=gui_update_table)

            def gui_add_performance():
                '''
                Add performance values
                '''
                try:
                    rowids = excel_performance.get_column(0)
                    if len(np.unique(rowids)) != len(rowids):
                        raise Exception('Duplicate row numbers')
                except:
                    tk.messagebox.showinfo('Error', 'Invalid row numbers', parent=window)
                    return

                # check for overwriting
                overwrite = False
                for rowid in rowids:
                    for i in range(n_obj):
                        if self.table_db.get(rowid - 1, f'f{i + 1}') != 'N/A':
                            overwrite = True
                if overwrite and tk.messagebox.askquestion('Overwrite Data', 'Are you sure to overwrite evaluated data?', parent=window) == 'no': return

                try:
                    Y = excel_performance.get_grid(column_start=1)
                except:
                    tk.messagebox.showinfo('Error', 'Invalid performance values', parent=window)
                    return
                
                window.destroy()

                # update database
                self.agent_data.update_batch(Y, rowids)

                # update table gui
                self.table_db.update({'Y': Y}, rowids=rowids)
            
            frame_action = create_widget('frame', master=window, row=2, column=0, sticky=None, pady=0)
            create_widget('button', master=frame_action, row=0, column=0, text='Save', command=gui_add_performance)
            create_widget('button', master=frame_action, row=0, column=1, text='Cancel', command=window.destroy)
        
        def gui_start_local_evaluate():
            '''
            Manually start local evaluation workers for certain rows from database panel (TODO: disable when no eval script linked)
            '''
            window = tk.Toplevel(master=self.frame_db)
            window.title('Start Local Evaluation')
            window.resizable(False, False)

            frame_n_row = create_widget('frame', master=window, row=0, column=0, sticky=None, pady=0)
            entry_n_row = create_widget('labeled_entry',
                master=frame_n_row, row=0, column=0, text='Number of rows', class_type='int', default=1, 
                valid_check=lambda x: x > 0, error_msg='number of rows must be positive')
            entry_n_row.set(1)
            button_n_row = create_widget('button', master=frame_n_row, row=0, column=1, text='Update')

            excel_rowid = Excel(master=window, rows=1, columns=1, width=10, 
                title=['Row number'], dtype=[int], default=None, required=[True], valid_check=[lambda x: x > 0 and x <= self.table_db.n_rows])
            excel_rowid.grid(row=1, column=0)

            def gui_update_table():
                '''
                Update excel table of design variables to be added
                '''
                n_row = entry_n_row.get()
                excel_rowid.update_n_row(n_row)

            button_n_row.configure(command=gui_update_table)
            
            def gui_start_eval_worker():
                '''
                Start evaluation workers
                '''
                try:
                    rowids = excel_rowid.get_column(0)
                except:
                    tk.messagebox.showinfo('Error', 'Invalid row numbers', parent=window)
                    return

                # check for overwriting
                overwrite = False
                n_obj = self.config['problem']['n_obj']
                for rowid in rowids:
                    for i in range(n_obj):
                        if self.table_db.get(rowid - 1, f'f{i + 1}') != 'N/A':
                            overwrite = True
                if overwrite and tk.messagebox.askquestion('Overwrite Data', 'Are you sure to overwrite evaluated data?', parent=window) == 'no': return

                window.destroy()

                for rowid in rowids:
                    self.agent_worker.add_eval_worker(rowid)

            frame_action = create_widget('frame', master=window, row=2, column=0, sticky=None, pady=0)
            create_widget('button', master=frame_action, row=0, column=0, text='Evaluate', command=gui_start_eval_worker)
            create_widget('button', master=frame_action, row=0, column=1, text='Cancel', command=window.destroy)

        def gui_start_remote_evaluate():
            '''
            Manually start remote evaluation workers for certain rows from database panel
            '''
            window = tk.Toplevel(master=self.frame_db)
            window.title('Start Remote Evaluation')
            window.resizable(False, False)

            # TODO

        def gui_stop_evaluate():
            '''
            Manually stop evaluation workers for certain rows from database panel (TODO: disable when no eval script linked)
            '''
            window = tk.Toplevel(master=self.frame_db)
            window.title('Stop Evaluation')
            window.resizable(False, False)

            frame_n_row = create_widget('frame', master=window, row=0, column=0, sticky=None, pady=0)
            entry_n_row = create_widget('labeled_entry',
                master=frame_n_row, row=0, column=0, text='Number of rows', class_type='int', default=1, 
                valid_check=lambda x: x > 0, error_msg='number of rows must be positive')
            entry_n_row.set(1)
            button_n_row = create_widget('button', master=frame_n_row, row=0, column=1, text='Update')

            excel_rowid = Excel(master=window, rows=1, columns=1, width=10, 
                title=['Row number'], dtype=[int], default=None, required=[True], valid_check=[lambda x: x > 0 and x <= self.table_db.n_rows])
            excel_rowid.grid(row=1, column=0)

            def gui_update_table():
                '''
                Update excel table of design variables to be added
                '''
                n_row = entry_n_row.get()
                excel_rowid.update_n_row(n_row)

            button_n_row.configure(command=gui_update_table)

            def gui_stop_eval_worker():
                '''
                Stop evaluation workers
                '''
                try:
                    rowids = excel_rowid.get_column(0)
                except:
                    tk.messagebox.showinfo('Error', 'Invalid row numbers', parent=window)
                    return

                window.destroy()

                for rowid in rowids:
                    self.agent_worker.stop_eval_worker(rowid)

            frame_action = create_widget('frame', master=window, row=2, column=0, sticky=None, pady=0)
            create_widget('button', master=frame_action, row=0, column=0, text='Stop', command=gui_stop_eval_worker)
            create_widget('button', master=frame_action, row=0, column=1, text='Cancel', command=window.destroy)

        frame_db_ctrl = create_widget('frame', master=self.frame_db, row=0, column=0, sticky=None)
        grid_configure(frame_db_ctrl, [0], [0, 1, 2, 3])
        create_widget('button', master=frame_db_ctrl, row=0, column=0, text='Enter Design Variables', command=gui_enter_design)
        create_widget('button', master=frame_db_ctrl, row=0, column=1, text='Enter Performance Values', command=gui_enter_performance)
        create_widget('button', master=frame_db_ctrl, row=0, column=2, text='Start Local Evaluation', command=gui_start_local_evaluate)
        create_widget('button', master=frame_db_ctrl, row=0, column=3, text='Start Remote Evaluation', command=gui_start_remote_evaluate)
        create_widget('button', master=frame_db_ctrl, row=0, column=4, text='Stop Evaluation', command=gui_stop_evaluate)

        self.frame_db_table = create_widget('frame', master=self.frame_db, row=1, column=0)
        
        # initialize database table
        n_var, n_obj = X.shape[1], Y.shape[1]
        titles = ['status'] + [f'x{i + 1}' for i in range(n_var)] + \
            [f'f{i + 1}' for i in range(n_obj)] + \
            [f'f{i + 1}_expected' for i in range(n_obj)] + \
            [f'f{i + 1}_uncertainty' for i in range(n_obj)] + \
            ['pareto', 'config_id', 'batch_id']
        key_map = {
            'X': [f'x{i + 1}' for i in range(n_var)],
            'Y': [f'f{i + 1}' for i in range(n_obj)],
            'Y_expected': [f'f{i + 1}_expected' for i in range(n_obj)],
            'Y_uncertainty': [f'f{i + 1}_uncertainty' for i in range(n_obj)],
        }

        self.table_db = Table(master=self.frame_db_table, titles=titles)
        self.table_db.register_key_map(key_map)
        self.table_db.insert({
            'status': ['evaluated'] * self.n_init_sample,
            'X': X, 
            'Y': Y, 
            'Y_expected': np.full_like(Y, 'N/A', dtype=object),
            'Y_uncertainty': np.full_like(Y, 'N/A', dtype=object),
            'pareto': is_pareto, 
            'config_id': np.zeros(self.n_init_sample, dtype=int), 
            'batch_id': np.zeros(self.n_init_sample, dtype=int)
        })

        # activate visualization tabs
        self.nb_viz.tab(0, state=tk.NORMAL)
        self.nb_viz.tab(1, state=tk.NORMAL)
        self.nb_viz.tab(2, state=tk.NORMAL)
        self.nb_viz.select(0)

    def _init_control_widgets(self):
        '''
        Control widgets initialization (optimize, stop, user input, show history)
        '''
        # control overall frame
        frame_control = create_widget('labeled_frame', master=self.root, row=0, column=1, text='Control')

        widget_map = {}
        widget_map['mode'] = create_widget('labeled_combobox',
            master=frame_control, row=0, column=0, columnspan=2, text='Optimization mode', values=['manual', 'auto'], required=True, required_mark=False)
        widget_map['batch_size'] = create_widget('labeled_entry', 
            master=frame_control, row=1, column=0, columnspan=2, text=self.name_map['general']['batch_size'], class_type='int', required=True, required_mark=False,
            valid_check=lambda x: x > 0, error_msg='number of batch size must be positive')
        widget_map['n_iter'] = create_widget('labeled_entry', 
            master=frame_control, row=2, column=0, columnspan=2, text=self.name_map['general']['n_iter'], class_type='int', required=True, required_mark=False,
            valid_check=lambda x: x > 0, error_msg='number of optimization iteration must be positive')

        def gui_set_stop_criterion():
            '''
            Set stopping criterion for optimization
            '''
            window = tk.Toplevel(master=self.root)
            window.title('Stopping Criterion')
            window.resizable(False, False)

            frame_options = create_widget('frame', master=window, row=0, column=0, padx=0, pady=0)
            name_options = {'time': 'Time', 'n_sample': 'Number of samples', 'hv_value': 'Hypervolume value', 'hv_conv': 'Hypervolume convergence'}
            var_options = {}
            entry_options = {}

            frame_time = create_widget('frame', master=frame_options, row=0, column=0)
            var_options['time'] = tk.IntVar()
            tk.Checkbutton(master=frame_time, variable=var_options['time'], highlightthickness=0, bd=0).grid(row=0, column=0, sticky='W')
            tk.Label(master=frame_time, text=name_options['time'] + ': stop after').grid(row=0, column=1, sticky='W')
            entry_options['time'] = create_widget('entry', master=frame_time, row=0, column=2, class_type='float', 
                required=True, valid_check=lambda x: x > 0, error_msg='time limit must be positive', pady=0)
            tk.Label(master=frame_time, text='seconds').grid(row=0, column=3, sticky='W')

            frame_n_sample = create_widget('frame', master=frame_options, row=1, column=0)
            var_options['n_sample'] = tk.IntVar()
            tk.Checkbutton(master=frame_n_sample, variable=var_options['n_sample'], highlightthickness=0, bd=0).grid(row=0, column=0, sticky='W')
            tk.Label(master=frame_n_sample, text=name_options['n_sample'] + ': stop when number of samples reaches').grid(row=0, column=1, sticky='W')
            entry_options['n_sample'] = create_widget('entry', master=frame_n_sample, row=0, column=2, class_type='int', 
                required=True, valid_check=lambda x: x > 0, error_msg='number of samples must be positive', pady=0)

            frame_hv_value = create_widget('frame', master=frame_options, row=2, column=0)
            var_options['hv_value'] = tk.IntVar()
            tk.Checkbutton(master=frame_hv_value, variable=var_options['hv_value'], highlightthickness=0, bd=0).grid(row=0, column=0, sticky='W')
            tk.Label(master=frame_hv_value, text=name_options['hv_value'] + ': stop when hypervolume reaches').grid(row=0, column=1, sticky='W')
            entry_options['hv_value'] = create_widget('entry', master=frame_hv_value, row=0, column=2, class_type='float', 
                required=True, valid_check=lambda x: x > 0, error_msg='hypervolume value must be positive', pady=0)

            frame_hv_conv = create_widget('frame', master=frame_options, row=3, column=0)
            var_options['hv_conv'] = tk.IntVar()
            tk.Checkbutton(master=frame_hv_conv, variable=var_options['hv_conv'], highlightthickness=0, bd=0).grid(row=0, column=0, sticky='W')
            tk.Label(master=frame_hv_conv, text=name_options['hv_conv'] + ': stop when hypervolume stops to improve over past').grid(row=0, column=1, sticky='W')
            entry_options['hv_conv'] = create_widget('entry', master=frame_hv_conv, row=0, column=2, class_type='float', 
                required=True, valid_check=lambda x: x > 0 and x < 100, error_msg='percentage must be between 0~100', pady=0)
            tk.Label(master=frame_hv_conv, text='% number of samples').grid(row=0, column=3, sticky='W')

            def load_stop_criterion():
                '''
                Load current stopping criterion
                '''
                for key, val in self.stop_criterion.items():
                    var_options[key].set(1)
                    if key == 'time':
                        val -= time() - self.timestamp
                        self.stop_criterion[key] = val
                        self.timestamp = time()
                    entry_options[key].set(val)

            def gui_save_stop_criterion():
                '''
                Save stopping criterion
                '''
                self.stop_criterion = {}
                for key in ['time', 'n_sample', 'hv_value', 'hv_conv']:
                    if var_options[key].get() == 1:
                        try:
                            self.stop_criterion[key] = entry_options[key].get()
                        except:
                            error_msg = entry_options[key].get_error_msg()
                            error_msg = '' if error_msg is None else ': ' + error_msg
                            tk.messagebox.showinfo('Error', f'Invalid value for "{name_options[key]}"' + error_msg, parent=window)
                            return
                        if key == 'time':
                            self.timestamp = time()
                window.destroy()

            frame_action = create_widget('frame', master=window, row=1, column=0, pady=0, sticky=None)
            create_widget('button', master=frame_action, row=0, column=0, text='Save', command=gui_save_stop_criterion)
            create_widget('button', master=frame_action, row=0, column=1, text='Cancel', command=window.destroy)

            load_stop_criterion()

        self.button_stopcri = create_widget('labeled_button', master=frame_control, row=3, column=0, columnspan=2, 
            label_text='Stopping criterion', button_text='Set', command=gui_set_stop_criterion, pady=5)

        self.entry_mode = widget_map['mode']
        self.entry_batch_size = widget_map['batch_size']
        self.entry_n_iter = widget_map['n_iter']
        self.entry_mode.disable()
        self.entry_batch_size.disable()
        self.entry_n_iter.disable()
        self.button_stopcri.disable()

        # optimization command
        self.button_optimize = Button(master=frame_control, text="Optimize", state=tk.DISABLED)
        self.button_optimize.grid(row=4, column=0, padx=5, pady=10, sticky='NSEW')

        # stop optimization command
        self.button_stop = Button(master=frame_control, text='Stop', state=tk.DISABLED)
        self.button_stop.grid(row=4, column=1, padx=5, pady=10, sticky='NSEW')

        def gui_optimize():
            '''
            Execute optimization
            '''
            config = self.config.copy()
            for key in ['batch_size', 'n_iter']:
                try:
                    config['general'][key] = widget_map[key].get()
                except:
                    error_msg = widget_map[key].get_error_msg()
                    error_msg = '' if error_msg is None else ': ' + error_msg
                    tk.messagebox.showinfo('Error', 'Invalid value for "' + self.name_map['general'][key] + '"' + error_msg, parent=self.root)
                    return

            self._set_config(config)

            self.menu_config.entryconfig(0, state=tk.DISABLED)
            self.menu_config.entryconfig(2, state=tk.DISABLED)
            self.entry_mode.disable()
            if self.entry_mode.get() == 'auto':
                self.button_optimize.disable()
            self.button_stop.enable()

            self.agent_worker.set_mode(self.entry_mode.get())
            self.agent_worker.set_config(self.config, self.config_id)
            self.agent_worker.add_opt_worker()

        def gui_stop_optimize():
            '''
            Stop optimization (TODO: support stopping individual process)
            '''
            self.agent_worker.stop_worker()
            self.entry_mode.enable()
            self.button_stop.disable()

        # link to commands
        self.button_optimize.configure(command=gui_optimize)
        self.button_stop.configure(command=gui_stop_optimize)

    def _init_log_widgets(self):
        '''
        Display widgets initialization (config, log)
        '''
        frame_log = create_widget('labeled_frame', master=self.root, row=1, column=1, text='Log')
        grid_configure(frame_log, [0], [0])

        # log display
        self.scrtext_log = scrolledtext.ScrolledText(master=frame_log, width=10, height=10, state=tk.DISABLED)
        self.scrtext_log.grid(row=0, column=0, sticky='NSEW', padx=5, pady=5)

    def _save_config(self, config):
        '''
        Save configurations to file
        '''
        self.config_id += 1
        with open(os.path.join(self.result_dir, 'config', f'config_{self.config_id}.yml'), 'w') as fp:
            yaml.dump(config, fp, default_flow_style=False, sort_keys=False)

    def _set_config(self, config, window=None):
        '''
        Setting configurations
        '''
        try:
            config = process_config(config)
        except:
            tk.messagebox.showinfo('Error', 'Invalid configurations', parent=window)
            return

        # update raw config (config will be processed and changed later)
        self.config_raw = config.copy()
        
        old_config = None if self.config is None else self.config.copy()

        # set parent window for displaying potential error messagebox
        if window is None: window = self.root

        if self.config is None: # first time setting config
            # check if result_dir folder exists
            if os.path.exists(self.result_dir) and os.listdir(self.result_dir) != []:
                tk.messagebox.showinfo('Error', f'Result folder {self.result_dir} is not empty, please change another folder for saving results by clicking: File -> Save in...', parent=window)
                return

            os.makedirs(self.result_dir, exist_ok=True)
            config_dir = os.path.join(self.result_dir, 'config')
            os.makedirs(config_dir)

            # initialize problem and data storage (agent)
            try:
                problem, self.true_pfront = build_problem(config['problem'], get_pfront=True)
            except:
                tk.messagebox.showinfo('Error', 'Invalid values in configuration', parent=window)
                return

            self.config = config

            # remove tutorial image
            self.image_tutorial.destroy()

            # build agents
            self.agent_data = DataAgent(n_var=problem.n_var, n_obj=problem.n_obj, result_dir=self.result_dir)
            self.agent_worker = WorkerAgent(mode='manual', config=config, agent_data=self.agent_data, eval=hasattr(problem, 'evaluate_performance'))

            # data initialization
            X_init_evaluated, X_init_unevaluated, Y_init_evaluated = get_initial_samples(config['problem'], problem)
            if X_init_evaluated is not None:
                self.agent_data.initialize(X_init_evaluated, Y_init_evaluated)
            if X_init_unevaluated is not None:
                rowids = self.agent_data.initialize(X_init_unevaluated)
                for rowid in rowids:
                    self.agent_worker.add_eval_worker(rowid)
                
                # wait until initialization is completed
                while not self.agent_worker.empty():
                    self.agent_worker.refresh()
                    sleep(self.refresh_rate / 1000.0)

            # calculate reference point
            if self.config['problem']['ref_point'] is None:
                Y = self.agent_data.load('Y')
                ref_point = np.max(Y, axis=0).tolist()
                self.config['problem']['ref_point'] = ref_point

            # initialize visualization widgets
            self._init_viz_widgets(problem)

            # disable changing saving location
            self.menu_file.entryconfig(0, state=tk.DISABLED)

            # change config create/change status
            self.menu_config.entryconfig(1, state=tk.DISABLED)
            self.menu_config.entryconfig(2, state=tk.NORMAL)

            # activate optimization widgets
            self.entry_mode.enable(readonly=False)
            self.entry_mode.set('manual')
            self.entry_mode.enable(readonly=True)

            self.entry_batch_size.enable()
            try:
                self.entry_batch_size.set(self.config['general']['batch_size'])
            except:
                self.entry_batch_size.set(5)

            self.entry_n_iter.enable()
            try:
                self.entry_n_iter.set(self.config['general']['n_iter'])
            except:
                self.entry_n_iter.set(1)

            self.button_optimize.enable()
            self.button_stopcri.enable()

            # trigger periodic refresh
            self.root.after(self.refresh_rate, self._refresh)

        else: # user changed config in the middle
            try:
                # some keys cannot be changed
                unchanged_keys = ['name', 'n_var', 'n_obj', 'var_name', 'obj_name', 'n_init_sample']
                if self.config_raw['problem']['ref_point'] is not None:
                    unchanged_keys.append('ref_point')
                for key in unchanged_keys:
                    assert self.config_raw['problem'][key] == config['problem'][key]
            except:
                tk.messagebox.showinfo('Error', 'Invalid configuration values for reloading', parent=window)
                return

            self.config = config
        
        if self.config != old_config:
            self._save_config(self.config)
            self.agent_worker.set_config(self.config, self.config_id)

    def _log(self, string):
        '''
        Log texts to ScrolledText widget for logging
        '''
        if string == []: return
        self.scrtext_log.configure(state=tk.NORMAL)
        if isinstance(string, str):
            self.scrtext_log.insert(tk.INSERT, string + '\n')
        elif isinstance(string, list):
            self.scrtext_log.insert(tk.INSERT, '\n'.join(string) + '\n')
        else:
            raise NotImplementedError
        self.scrtext_log.configure(state=tk.DISABLED)
        self.scrtext_log.yview_pickplace('end')

    def _refresh(self):
        '''
        Refresh current GUI status and redraw if data has changed
        '''
        self.agent_worker.refresh()
        
        # can optimize and load config when worker agent is empty
        if self.agent_worker.empty():
            self.entry_mode.enable()
            self.button_optimize.enable()
            self.button_stop.disable()
            if self.menu_config.entrycget(0, 'state') == tk.DISABLED:
                self.menu_config.entryconfig(0, state=tk.NORMAL)
            if self.menu_config.entrycget(2, 'state') == tk.DISABLED:
                self.menu_config.entryconfig(2, state=tk.NORMAL)

        # post-process worker logs
        log_list = []
        status, rowids = [], []
        evaluated = False
        for log in self.agent_worker.read_log():
            log = log.split('/')
            log_text = log[0]
            log_list.append(log_text)

            if not log_text.startswith('evaluation'): continue

            # evaluation worker log, update database table status
            if len(log) > 1:
                rowid = int(log[1])
                if log_text.endswith('started'):
                    status.append('evaluating')
                elif log_text.endswith('stopped'):
                    status.append('unevaluated')
                elif log_text.endswith('completed'):
                    status.append('evaluated')
                    evaluated = True
                else:
                    raise NotImplementedError
                rowids.append(rowid)

        # log display
        self._log(log_list)

        # update visualization
        self._redraw(evaluated)

        # update database table status (TODO: optimize)
        if evaluated:
            for s, rowid in zip(status, rowids):
                if s == 'evaluated':
                    Y = self.agent_data.load('Y', rowid=rowid)
                    self.table_db.update({'status': [s], 'Y': Y}, [rowid])
                else:
                    self.table_db.update({'status': [s]}, [rowid])
        else:
            self.table_db.update({'status': status}, rowids)

        # check stopping criterion
        self._check_stop_criterion()
        
        # trigger another refresh
        self.root.after(self.refresh_rate, self._refresh)

    def _check_stop_criterion(self):
        '''
        Check if stopping criterion is met
        '''
        stop = False
        for key, val in self.stop_criterion.items():
            if key == 'time': # optimization & evaluation time
                if time() - self.timestamp >= val:
                    stop = True
                    self.timestamp = None
            elif key == 'n_sample': # number of samples
                if self.n_valid_sample >= val:
                    stop = True
            elif key == 'hv_value': # hypervolume value
                if self.line_hv.get_ydata()[-1] >= val:
                    stop = True
            elif key == 'hv_conv': # hypervolume convergence
                hv_history = self.line_hv.get_ydata()
                checkpoint = np.clip(int(self.n_valid_sample * val / 100.0), 1, self.n_valid_sample - 1)
                if hv_history[-checkpoint] == hv_history[-1]:
                    stop = True
            else:
                raise NotImplementedError
        
        if stop:
            self.stop_criterion = {}
            self.agent_worker.stop_worker()
            self._log('stopping criterion is met')

    def _clear_design_space(self):
        '''
        Clear design space plot
        '''
        if self.scatter_selected is not None:
            self.scatter_selected.remove()
            self.scatter_selected = None
            
        n_var, var_name = self.config['problem']['n_var'], self.config['problem']['var_name']

        if n_var > 2:
            self.ax12.set_varlabels(var_name)
            if self.line_x is not None:
                self.line_x.remove()
                self.line_x = None
            if self.fill_x is not None:
                self.fill_x.remove()
                self.fill_x = None
        else:
            if self.bar_x is not None:
                self.bar_x.remove()
                self.bar_x = None
            for text in self.text_x:
                text.remove()
            self.text_x = []

    def _redraw_performance_space(self, draw_iter=None):
        '''
        Redraw performance space
        '''
        X, Y, Y_expected, is_pareto, batch_id = self.agent_data.load(['X', 'Y', 'Y_expected', 'is_pareto', 'batch_id'])
        if draw_iter is not None and draw_iter < batch_id[-1]:
            draw_idx = batch_id <= draw_iter
            X, Y, Y_expected, batch_id = X[draw_idx], Y[draw_idx], Y_expected[draw_idx], batch_id[draw_idx]
            is_pareto = check_pareto(Y)
        
        # replot evaluated & pareto points
        self.scatter_x = X
        n_obj = Y.shape[1]
        if n_obj == 2:
            self.scatter_y.set_offsets(Y)
            self.scatter_y_pareto.set_offsets(Y[is_pareto])
        elif n_obj == 3:
            self.scatter_y._offsets_3d = Y
            self.scatter_y_pareto._offsets_3d = Y[is_pareto]
        
        # rescale plot according to Y and true_pfront
        n_obj = self.config['problem']['n_obj']
        x_min, x_max = np.min(Y[:, 0]), np.max(Y[:, 0])
        y_min, y_max = np.min(Y[:, 1]), np.max(Y[:, 1])
        if n_obj == 3: z_min, z_max = np.min(Y[:, 2]), np.max(Y[:, 2])
        if self.pfront_limit is not None:
            x_min, x_max = min(x_min, self.pfront_limit[0][0]), max(x_max, self.pfront_limit[1][0])
            y_min, y_max = min(y_min, self.pfront_limit[0][1]), max(y_max, self.pfront_limit[1][1])
            if n_obj == 3: z_min, z_max = min(z_min, self.pfront_limit[0][2]), max(z_max, self.pfront_limit[1][2])
        x_offset = (x_max - x_min) / 20
        y_offset = (y_max - y_min) / 20
        if n_obj == 3: z_offset = (z_max - z_min) / 20
        self.ax11.set_xlim(x_min - x_offset, x_max + x_offset)
        self.ax11.set_ylim(y_min - y_offset, y_max + y_offset)
        if n_obj == 3: self.ax11.set_zlim(z_min - z_offset, z_max + z_offset)

        # replot new evaluated & predicted points
        try:
            self.scatter_y_new.remove()
            self.scatter_y_pred.remove()
        except:
            pass
        for line in self.line_y_pred_list:
            line.remove()
        self.line_y_pred_list = []

        if batch_id[-1] > 0:
            last_batch_idx = np.where(batch_id == batch_id[-1])[0]
            if n_obj == 2:
                self.scatter_y_new.set_offsets(Y[last_batch_idx])
                self.scatter_y_pred.set_offsets(Y_expected[last_batch_idx])
            elif n_obj == 3:
                self.scatter_y._offsets_3d = Y[last_batch_idx]
                self.scatter_y_pareto._offsets_3d = Y_expected[last_batch_idx]
            for y, y_expected in zip(Y[last_batch_idx], Y_expected[last_batch_idx]):
                line = self.ax11.plot(*[[y[i], y_expected[i]] for i in range(n_obj)], '--', color='m', alpha=0.5)[0]
                self.line_y_pred_list.append(line)

        self.fig1.canvas.draw()

    def _redraw(self, evaluated=False):
        '''
        Redraw figures and database viz
        '''
        # check if database was updated
        db_status = self.agent_data.get_status()
        if db_status == self.db_status: return
        self.db_status = db_status
        
        # load from database
        X, Y, Y_expected, Y_uncertainty, is_pareto, config_id, batch_id = \
            self.agent_data.load(['X', 'Y', 'Y_expected', 'Y_uncertainty', 'is_pareto', 'config_id', 'batch_id'], valid_only=False)

        # check if any completed optimization
        n_curr_sample = len(X)
        n_prev_sample = self.n_sample
        self.n_sample = n_curr_sample
        opt_completed = (n_prev_sample < n_curr_sample)

        # check if any completed evaluation
        valid_idx = ~np.isnan(Y).any(axis=1)
        n_curr_valid_sample = int(np.sum(valid_idx))
        n_prev_valid_sample = self.n_valid_sample
        self.n_valid_sample = n_curr_valid_sample
        eval_completed = (n_prev_valid_sample < n_curr_valid_sample) or evaluated

        # replot if evaluation completed
        if eval_completed:
            # replot performance space if currently focusing on the lastest iteration
            if self.curr_iter.get() == self.max_iter:
                self.max_iter = batch_id[valid_idx][-1]
                self.scale_iter.configure(to=self.max_iter)
                self.curr_iter.set(self.max_iter)
                self._redraw_performance_space()
            else:
                self.max_iter = batch_id[valid_idx][-1]
                self.scale_iter.configure(to=self.max_iter)

            if batch_id[-1] > 0:
                # replot hypervolume curve
                line_hv_y = self.line_hv.get_ydata()
                hv_value = calc_hypervolume(Y[valid_idx], self.config['problem']['ref_point'])
                hv_value = np.concatenate([line_hv_y, np.full(self.n_valid_sample - len(line_hv_y), hv_value)])
                self.line_hv.set_data(list(range(self.n_valid_sample)), hv_value)
                self.ax21.relim()
                self.ax21.autoscale_view()
                self.ax21.set_title('Hypervolume: %.4f' % hv_value[-1])

                # replot prediction error curve
                line_error_y = self.line_error.get_ydata()
                pred_error = calc_pred_error(Y[valid_idx][self.n_init_sample:], Y_expected[valid_idx][self.n_init_sample:])
                pred_error = np.concatenate([line_error_y, np.full(self.n_valid_sample - self.n_init_sample - len(line_error_y), pred_error)])
                self.line_error.set_data(list(range(self.n_init_sample, self.n_valid_sample)), pred_error)
                self.ax22.relim()
                self.ax22.autoscale_view()
                self.ax22.set_title('Model Prediction Error: %.4f' % pred_error[-1])

                # refresh figure
                self.fig2.canvas.draw()
        
        # insert to table if optimization completed (TODO: optimize)
        if opt_completed:
            insert_len = len(Y_expected[n_prev_sample:])
            self.table_db.insert({
                # confirmed value
                'X': X[n_prev_sample:], 
                'Y_expected': Y_expected[n_prev_sample:],
                'Y_uncertainty': Y_uncertainty[n_prev_sample:],
                'config_id': config_id[n_prev_sample:], 
                'batch_id': batch_id[n_prev_sample:],
                # unconfirmed value
                'status': ['unevaluated'] * insert_len,
                'Y': np.ones_like(Y_expected[n_prev_sample:]) * np.nan,
                'pareto': [False] * insert_len,
            })

        # update table if evaluation completed (TODO: optimize)
        if eval_completed:
            self.table_db.update({
                'Y': Y, 
                'pareto': is_pareto,
            })

    def mainloop(self):
        '''
        Start mainloop of GUI
        '''
        tk.mainloop()

    def _quit(self):
        '''
        Quit handling
        '''
        if self.agent_data is not None:
            self.agent_data.quit()

        if self.agent_worker is not None:
            self.agent_worker.quit()

        self.root.quit()
        self.root.destroy()
