import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MaxNLocator
from matplotlib.backend_bases import MouseButton


import os
import yaml
import numpy as np
from multiprocessing import Lock, Process
from problems.common import build_problem, get_problem_list, get_yaml_problem_list, get_problem_config
from problems.utils import import_module_from_path
from system.agent import DataAgent, ProblemAgent, WorkerAgent
from system.utils import process_config, load_config, get_available_algorithms, find_closest_point, check_pareto
from system.gui.utils.button import Button
from system.gui.utils.entry import get_entry
from system.gui.utils.excel import Excel
from system.gui.utils.listbox import Listbox
from system.gui.utils.table import Table
from system.gui.utils.grid import grid_configure, embed_figure
from system.gui.utils.radar import radar_factory
from system.gui.utils.widget_creation import create_widget


class GUI:
    '''
    Interactive local tkinter-based GUI
    '''
    def __init__(self):
        '''
        GUI initialization
        '''
        # GUI root initialization
        self.root = tk.Tk()
        self.root.title('MOBO')
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
        self.agent_problem = ProblemAgent()
        self.agent_worker = None

        # config related
        self.config = None
        self.config_raw = None
        self.config_id = -1

        # event widgets
        self.button_optimize = None
        self.button_stop = None
        self.scrtext_log = None
        self.entry_mode = None
        self.entry_batch_size = None
        self.entry_n_iter = None
        self.nb_viz = None
        self.frame_db = None
        self.table_db = None

        # data to be plotted
        self.scatter_x = None
        self.scatter_y = None
        self.scatter_y_pareto = None
        self.annotate = None
        self.line_x = None
        self.fill_x = None
        self.line_hv = None
        self.line_error = None

        # status variables
        self.n_init_sample = None
        self.n_curr_sample = None
        self.curr_iter = tk.IntVar()
        self.max_iter = 0
        self.in_creating_problem = False

        # displayed name of each property in config
        self.name_map = {
            'general': {
                'n_init_sample': 'Number of initial samples',
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
            },
            'algorithm': {
                'name': 'Name of algorithm',
                'n_process': 'Number of parallel processes to use',
            },
        }

        # GUI modules initialization
        self._init_menu()
        self._init_widgets()

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
        self.menu_log = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='Log', menu=self.menu_log)

        # init sub-level menu
        self._init_file_menu()
        self._init_config_menu()
        self._init_problem_menu()
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

            window = tk.Toplevel(master=self.root)
            if change:
                window.title('Change Configurations')
            else:
                window.title('Create Configurations')
            window.configure(bg='white')
            window.resizable(False, False)

            # parameter section
            frame_param = tk.Frame(master=window, bg='white')
            frame_param.grid(row=0, column=0)
            grid_configure(frame_param, [0, 1, 2], [0])

            # general subsection
            frame_general = create_widget('labeled_frame', master=frame_param, row=0, column=0, text='General')
            grid_configure(frame_general, [0, 1, 2, 3], [0])
            widget_map['general']['n_init_sample'] = create_widget('labeled_entry', 
                master=frame_general, row=0, column=0, text=self.name_map['general']['n_init_sample'], class_type='int', required=True, 
                valid_check=lambda x: x > 0, error_msg='number of initial samples must be positive', changeable=False)
            widget_map['general']['n_worker'] = create_widget('labeled_entry',
                master=frame_general, row=1, column=0, text=self.name_map['general']['n_worker'], class_type='int', default=1,
                valid_check=lambda x: x > 0, error_msg='max number of evaluation workers must be positive')

            # problem subsection
            frame_problem = create_widget('labeled_frame', master=frame_param, row=1, column=0, text='Problem')
            grid_configure(frame_problem, [0, 1, 2, 3, 4, 5], [0])
            widget_map['problem']['name'] = create_widget('labeled_combobox', 
                master=frame_problem, row=0, column=0, text=self.name_map['problem']['name'], values=get_problem_list(), required=True, changeable=False)
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
                window_design.title('Configure Design Space')
                window_design.configure(bg='white')
                window_design.resizable(False, False)

                # design space section
                frame_design = create_widget('labeled_frame', master=window_design, row=0, column=0, text='Design Space')
                create_widget('label', master=frame_design, row=0, column=0, text='Enter the properties for design variables:')
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
                frame_action = tk.Frame(master=window_design, bg='white')
                frame_action.grid(row=1, column=0)
                create_widget('button', frame_action, 0, 0, 'Save', gui_save_design_space)
                create_widget('button', frame_action, 0, 1, 'Cancel', window_design.destroy)

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
                window_performance.title('Configure Performance Space')
                window_performance.configure(bg='white')
                window_performance.resizable(False, False)

                # performance space section
                frame_performance = create_widget('labeled_frame', master=window_performance, row=0, column=0, text='Performance Space')
                create_widget('label', master=frame_performance, row=0, column=0, text='Enter the properties for performance variables:')
                excel_performance = Excel(master=frame_performance, rows=n_obj, columns=3, width=15,
                    title=[self.name_map['problem'][title] for title in titles], dtype=[str, float, float])
                excel_performance.grid(row=1, column=0)
                excel_performance.set_column(0, obj_name)
                excel_performance.disable_column(0)

                if self.config is not None:
                    excel_performance.set_column(1, self.config['problem']['obj_lb'])
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
                frame_action = tk.Frame(master=window_performance, bg='white')
                frame_action.grid(row=1, column=0)
                create_widget('button', frame_action, 0, 0, 'Save', gui_save_performance_space)
                create_widget('button', frame_action, 0, 1, 'Cancel', window_performance.destroy)

            frame_space = create_widget('frame', master=frame_problem, row=4, column=0)
            button_config_design = create_widget('button', master=frame_space, row=4, column=0, text='Configure design bounds', command=gui_config_design, pady=0)
            button_config_performance = create_widget('button', master=frame_space, row=4, column=1, text='Configure performance bounds', command=gui_config_performance, pady=0)

            if not change:
                button_config_design.disable()
                button_config_performance.disable()

            def gui_select_problem(event):
                '''
                Select problem to configure
                '''
                for key in ['n_var', 'n_obj', 'ref_point']:
                    widget_map['problem'][key].enable()
                button_config_design.enable()
                button_config_performance.enable()

                name = event.widget.get()
                config = get_problem_config(name)
                for key in ['n_var', 'n_obj']:
                    widget_map['problem'][key].set(config[key])
                
                for key in ['var_name', 'var_lb', 'var_ub', 'obj_name', 'obj_lb', 'obj_ub']:
                    problem_cfg.update({key: config[key]})

            widget_map['problem']['name'].widget.bind('<<ComboboxSelected>>', gui_select_problem)

            # algorithm subsection
            frame_algorithm = create_widget('labeled_frame', master=frame_param, row=2, column=0, text='Algorithm')
            grid_configure(frame_algorithm, [0], [0])
            widget_map['algorithm']['name'] = create_widget('labeled_combobox', 
                master=frame_algorithm, row=0, column=0, text=self.name_map['algorithm']['name'], values=get_available_algorithms(), required=True)
            widget_map['algorithm']['n_process'] = create_widget('labeled_entry', 
                master=frame_algorithm, row=1, column=0, text=self.name_map['algorithm']['n_process'], class_type='int', default=1, 
                valid_check=lambda x: x > 0, error_msg='number of processes to use must be positive')

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

                # set config values from widgets
                for cfg_type, val_map in widget_map.items():
                    for cfg_name, widget in val_map.items():
                        try:
                            config[cfg_type][cfg_name] = widget.get()
                        except:
                            error_msg = widget.get_error_msg()
                            error_msg = '' if error_msg is None else ': ' + error_msg
                            tk.messagebox.showinfo('Error', f'Invalid value for "{self.name_map[cfg_type][cfg_name]}"' + error_msg, parent=window)
                            return

                # validity check
                n_var, n_obj = config['problem']['n_var'], config['problem']['n_obj']
                if n_var != len(problem_cfg['var_name']):
                    tk.messagebox.showinfo('Error', 'Number of design variables changed, please reconfigure design space', parent=window)
                    return
                if n_obj != len(problem_cfg['obj_name']):
                    tk.messagebox.showinfo('Error', 'Number of objectives changed, please reconfigure performance space', parent=window)
                    return

                config['problem'].update(problem_cfg)

                self._set_config(config, window)
                window.destroy()

            # action section
            frame_action = tk.Frame(master=window, bg='white')
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
            window.configure(bg='white')
            window.resizable(False, False)

            # problem section
            frame_problem = create_widget('frame', master=window, row=0, column=0)
            frame_list = create_widget('labeled_frame', master=frame_problem, row=0, column=0, text='Problem List')
            frame_list_display = create_widget('frame', master=frame_list, row=0, column=0, padx=5, pady=5)
            frame_list_action = create_widget('frame', master=frame_list, row=1, column=0, padx=0, pady=0)
            frame_config = create_widget('labeled_frame', master=frame_problem, row=0, column=1, text='Problem Config')
            frame_config_display = create_widget('frame', master=frame_config, row=0, column=0, padx=0, pady=0)
            frame_config_action = create_widget('frame', master=frame_config, row=1, column=0, padx=0, pady=0)
            
            grid_configure(frame_list, [0], [0])
            grid_configure(frame_config_action, [0], [0, 1])

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

            frame_config_space = create_widget('frame', master=frame_config_display, row=4, column=0)
            button_config_design = create_widget('button', master=frame_config_space, row=0, column=0, text='Configure design space', pady=0)
            button_config_performance = create_widget('button', master=frame_config_space, row=0, column=1, text='Configure performance space', pady=0)

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

            frame_performance_script = create_widget('frame', master=frame_config_display, row=5, column=0, padx=0)
            create_widget('label', master=frame_performance_script, row=0, column=0, text=self.name_map['problem']['performance_eval'] + ' (*): ', columnspan=2)
            button_browse_performance = create_widget('button', master=frame_performance_script, row=1, column=0, text='Browse', command=gui_set_performance_script, pady=0)
            widget_map['performance_eval'] = create_widget('entry', 
                master=frame_performance_script, row=1, column=1, class_type='string', width=30, required=True, 
                valid_check=performance_script_valid_check, error_msg="performance evaluation script doesn't exist or no evaluate_performance() function inside", 
                pady=0, sticky='EW')
            grid_configure(frame_performance_script, [0], [1])

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

            frame_constraint_script = create_widget('frame', master=frame_config_display, row=6, column=0, padx=0)
            create_widget('label', master=frame_constraint_script, row=0, column=0, text=self.name_map['problem']['constraint_eval'] + ': ', columnspan=2)
            button_browse_constraint = create_widget('button', master=frame_constraint_script, row=1, column=0, text='Browse', command=gui_set_constraint_script, pady=0)
            widget_map['constraint_eval'] = create_widget('entry', 
                master=frame_constraint_script, row=1, column=1, class_type='string', width=30, 
                valid_check=constraint_script_valid_check, error_msg="constraint evaluation script doesn't exist or no evaluate_constraint() function inside", 
                pady=0, sticky='EW')
            grid_configure(frame_constraint_script, [0], [1])

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
                window_design.configure(bg='white')
                window_design.resizable(False, False)

                # design space section
                frame_design = create_widget('labeled_frame', master=window_design, row=0, column=0, text='Design Space')
                create_widget('label', master=frame_design, row=0, column=0, text='Enter the properties for design variables:')
                excel_design = Excel(master=frame_design, rows=n_var, columns=3, width=15,
                    title=[self.name_map['problem'][title] for title in titles], dtype=[str, float, float], default=[None, 0, 1])
                excel_design.grid(row=1, column=0)
                excel_design.set_column(0, [f'x{i + 1}' for i in range(n_var)])

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
                    for key, val in temp_cfg.items():
                        problem_cfg[key] = val

                # action section
                frame_action = tk.Frame(master=window_design, bg='white')
                frame_action.grid(row=1, column=0)
                create_widget('button', frame_action, 0, 0, 'Save', gui_save_design_space)
                create_widget('button', frame_action, 0, 1, 'Cancel', window_design.destroy)

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
                window_performance.configure(bg='white')
                window_performance.resizable(False, False)

                # performance space section
                frame_performance = create_widget('labeled_frame', master=window_performance, row=0, column=0, text='Performance Space')
                create_widget('label', master=frame_performance, row=0, column=0, text='Enter the properties for objectives:')
                excel_performance = Excel(master=frame_performance, rows=n_obj, columns=3, width=15,
                    title=[self.name_map['problem'][title] for title in titles], dtype=[str, float, float])
                excel_performance.grid(row=1, column=0)
                excel_performance.set_column(0, [f'f{i + 1}' for i in range(n_obj)])

                def gui_save_performance_space():
                    '''
                    Save performance space parameters
                    '''
                    temp_cfg = {}
                    for column, key in enumerate(titles):
                        try:
                            temp_cfg[key] = excel.get_column(column)
                        except:
                            tk.messagebox.showinfo('Error', 'Invalid value for "' + self.name_map['problem'][key] + '"', parent=window_performance)
                            return
                    for key, val in temp_cfg.items():
                        problem_cfg[key] = val

                # action section
                frame_action = tk.Frame(master=window_performance, bg='white')
                frame_action.grid(row=1, column=0)
                create_widget('button', frame_action, 0, 0, 'Save', gui_save_performance_space)
                create_widget('button', frame_action, 0, 1, 'Cancel', window_performance.destroy)

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
                    self.agent_problem.save_problem(problem_cfg)
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
                            self.agent_problem.remove_problem(old_name)
                        self.agent_problem.save_problem(problem_cfg)
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
                    self.agent_problem.remove_problem(name)
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
                config = self.agent_problem.load_problem(name)
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
        self._init_viz_widgets()
        self._init_control_widgets()
        self._init_log_widgets()

    def _init_viz_widgets(self):
        '''
        Visualization widgets initialization (design/performance visualization, statistics, database)
        '''
        frame_viz = tk.Frame(master=self.root)
        frame_viz.grid(row=0, column=0, rowspan=2, sticky='NSEW')
        grid_configure(frame_viz, [0], [0])

        # configure tab widgets
        self.nb_viz = ttk.Notebook(master=frame_viz)
        self.nb_viz.grid(row=0, column=0, sticky='NSEW')
        frame_plot = tk.Frame(master=self.nb_viz)
        frame_stat = tk.Frame(master=self.nb_viz)
        frame_db = tk.Frame(master=self.nb_viz)
        grid_configure(frame_plot, [0], [0])
        grid_configure(frame_stat, [0], [0])
        self.nb_viz.add(child=frame_plot, text='Visualization')
        self.nb_viz.add(child=frame_stat, text='Statistics')
        self.nb_viz.add(child=frame_db, text='Database')

        # temporarily disable database tab until data loaded
        self.nb_viz.tab(2, state=tk.DISABLED)
        self.frame_db = frame_db

        # configure slider widget
        frame_slider = tk.Frame(master=frame_viz)
        frame_slider.grid(row=1, column=0, padx=5, pady=5, sticky='EW')
        grid_configure(frame_slider, [0], [1])
        
        label_iter = tk.Label(master=frame_slider, text='Iteration:')
        label_iter.grid(row=0, column=0, sticky='EW')
        self.scale_iter = tk.Scale(master=frame_slider, orient=tk.HORIZONTAL, variable=self.curr_iter, from_=0, to=0)
        self.scale_iter.grid(row=0, column=1, sticky='EW')

        # figure placeholder in GUI (NOTE: only 2-dim performance space is supported)
        self.fig1 = plt.figure(figsize=(10, 5))
        self.gs1 = GridSpec(1, 2, figure=self.fig1, width_ratios=[3, 2])
        self.fig2 = plt.figure(figsize=(10, 5))

        # performance space figure
        self.ax11 = self.fig1.add_subplot(self.gs1[0])
        self.ax11.set_title('Performance Space')

        # design space figure
        n_var_init = 5
        self.theta = radar_factory(n_var_init)
        self.ax12 = self.fig1.add_subplot(self.gs1[1], projection='radar')
        self.ax12.set_xticks(self.theta)
        self.ax12.set_varlabels([f'x{i + 1}' for i in range(n_var_init)])
        self.ax12.set_yticklabels([])
        self.ax12.set_title('Design Space', position=(0.5, 1.1))

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
        self.ax22.set_ylabel('Averaged Relative Error (%)')
        self.ax22.xaxis.set_major_locator(MaxNLocator(integer=True))

        # connect matplotlib figure with tkinter GUI
        embed_figure(self.fig1, frame_plot)
        embed_figure(self.fig2, frame_stat)

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

    def _init_control_widgets(self):
        '''
        Control widgets initialization (optimize, stop, user input, show history)
        '''
        # control overall frame
        frame_control = create_widget('labeled_frame', master=self.root, row=0, column=1, text='Control', bg=None)

        widget_map = {}
        widget_map['mode'] = create_widget('labeled_combobox',
            master=frame_control, row=0, column=0, columnspan=2, text='Optimization mode', values=['manual', 'auto'], required=True, required_mark=False, bg=None)
        widget_map['batch_size'] = create_widget('labeled_entry', 
            master=frame_control, row=1, column=0, columnspan=2, text=self.name_map['general']['batch_size'], class_type='int', required=True, required_mark=False,
            valid_check=lambda x: x > 0, error_msg='number of batch size must be positive', bg=None)
        widget_map['n_iter'] = create_widget('labeled_entry', 
            master=frame_control, row=2, column=0, columnspan=2, text=self.name_map['general']['n_iter'], class_type='int', required=True, required_mark=False,
            valid_check=lambda x: x > 0, error_msg='number of optimization iteration must be positive', bg=None)

        self.entry_mode = widget_map['mode']
        self.entry_batch_size = widget_map['batch_size']
        self.entry_n_iter = widget_map['n_iter']
        self.entry_mode.disable()
        self.entry_batch_size.disable()
        self.entry_n_iter.disable()

        # optimization command
        self.button_optimize = Button(master=frame_control, text="Optimize", state=tk.DISABLED)
        self.button_optimize.grid(row=3, column=0, padx=5, pady=10, sticky='NSEW')

        # stop optimization command
        self.button_stop = Button(master=frame_control, text='Stop', state=tk.DISABLED)
        self.button_stop.grid(row=3, column=1, padx=5, pady=10, sticky='NSEW')

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
        frame_log = create_widget('labeled_frame', master=self.root, row=1, column=1, text='Log', bg=None)
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

        # update raw config (config will be processed and changed later in build_problem()) (TODO: check)
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
                problem, true_pfront = build_problem(config['problem'], get_pfront=True)
            except:
                tk.messagebox.showinfo('Error', 'Invalid values in configuration', parent=window)
                return

            self.config = config

            # build agents
            self.agent_data = DataAgent(config=config, result_dir=self.result_dir)
            self.agent_worker = WorkerAgent(mode='manual', config=config, agent_data=self.agent_data)

            n_var, var_name, obj_name = problem.n_var, problem.var_name, problem.obj_name
            self.var_lb, self.var_ub = problem.xl, problem.xu
            if self.var_lb is None: self.var_lb = np.zeros(n_var)
            if self.var_ub is None: self.var_ub = np.ones(n_var)
            
            # update plot
            self.ax11.set_xlabel(obj_name[0])
            self.ax11.set_ylabel(obj_name[1])
            self.theta = radar_factory(n_var)
            self.fig1.delaxes(self.ax12)
            self.ax12 = self.fig1.add_subplot(self.gs1[1], projection='radar')
            self.ax12.set_xticks(self.theta)
            self.ax12.set_varlabels([f'{var_name[i]}\n[{self.var_lb[i]},{self.var_ub[i]}]' for i in range(n_var)])
            self.ax12.set_yticklabels([])
            self.ax12.set_title('Design Space', position=(0.5, 1.1))
            self.ax12.set_ylim(0, 1)

            self._init_draw(true_pfront)

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

            # trigger periodic refresh
            self.root.after(self.refresh_rate, self._refresh)

        else: # user changed config in the middle
            try:
                # some keys cannot be changed
                for key in ['n_init_sample']:
                    assert self.config_raw['general'][key] == config['general'][key]
                for key in ['name', 'n_var', 'n_obj', 'var_name', 'obj_name', 'ref_point']: # TODO
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

    def _refresh(self):
        '''
        Refresh current GUI status and redraw if data has changed
        '''
        self.agent_worker.refresh()
        
        # can optimize and load config when worker agent is empty
        if self.agent_worker.empty():
            self.button_stop.disable()
            if self.menu_config.entrycget(0, 'state') == tk.DISABLED:
                self.menu_config.entryconfig(0, state=tk.NORMAL)
            if self.menu_config.entrycget(2, 'state') == tk.DISABLED:
                self.menu_config.entryconfig(2, state=tk.NORMAL)

        self._log(self.agent_worker.read_log())
        self._redraw()
        self.root.after(self.refresh_rate, self._refresh)
        
    def _init_draw(self, true_pfront):
        '''
        First draw of figures and database viz
        '''
        # load from database
        X, Y, hv_value, is_pareto = self.agent_data.load(['X', 'Y', 'hv', 'is_pareto'])

        # update status
        self.n_init_sample = len(Y)
        self.n_curr_sample = self.n_init_sample

        # plot performance space
        if true_pfront is not None:
            self.ax11.scatter(*true_pfront.T, color='gray', s=5, label='True Pareto front') # plot true pareto front
        self.scatter_x = X
        self.scatter_y = self.ax11.scatter(*Y.T, color='blue', s=10, label='Evaluated points')
        self.scatter_y_pareto = self.ax11.scatter(*Y[is_pareto].T, color='red', s=10, label='Approximated Pareto front')
        self.scatter_y_new = self.ax11.scatter([], [], color='m', s=10, label='New evaluated points')
        self.scatter_y_pred = self.ax11.scatter([], [], facecolors='none', edgecolors='m', s=15, label='New predicted points')
        self.ax11.legend(loc='upper right')
        self.line_y_pred_list = []

        # plot hypervolume curve
        self.line_hv = self.ax21.plot(list(range(self.n_init_sample)), hv_value)[0]
        self.ax21.set_title('Hypervolume: %.2f' % hv_value[-1])

        # plot prediction error curve
        self.line_error = self.ax22.plot([], [])[0]

         # mouse clicking event
        def check_design_values(event):
            if event.inaxes != self.ax11: return

            if event.button == MouseButton.LEFT and event.dblclick: # check certain design values
                # find nearest performance values with associated design values
                loc = [event.xdata, event.ydata]
                all_y = self.scatter_y._offsets
                closest_y, closest_idx = find_closest_point(loc, all_y, return_index=True)
                closest_x = self.scatter_x[closest_idx]
                x_str = '\n'.join([f'{name}: {val:.4g}' for name, val in zip(self.config['problem']['var_name'], closest_x)])

                # clear checked design values
                self._clear_design_space()

                # plot checked design values (TODO: fix annotation location)
                y_range = np.max(all_y, axis=0) - np.min(all_y, axis=0)
                text_loc = [closest_y[i] + 0.05 * y_range[i] for i in range(2)]
                self.annotate = self.ax11.annotate(x_str, xy=closest_y, xytext=text_loc,
                    bbox=dict(boxstyle="round", fc="w", alpha=0.7),
                    arrowprops=dict(arrowstyle="->"))
                transformed_x = (np.array(closest_x) - self.var_lb) / (self.var_ub - self.var_lb)
                self.line_x = self.ax12.plot(self.theta, transformed_x)[0]
                self.fill_x = self.ax12.fill(self.theta, transformed_x, alpha=0.2)[0]

            elif event.button == MouseButton.RIGHT: # clear checked design values
                self._clear_design_space()
                
            self.fig1.canvas.draw()
        
        self.fig1.canvas.mpl_connect('button_press_event', check_design_values)

        # refresh figure
        self.fig1.canvas.draw()
        self.fig2.canvas.draw()

        # initialize database viz
        n_var, n_obj = X.shape[1], Y.shape[1]
        titles = [f'x{i + 1}' for i in range(n_var)] + \
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

        self.nb_viz.tab(2, state=tk.NORMAL)
        self.table_db = Table(master=self.frame_db, titles=titles)
        self.table_db.register_key_map(key_map)
        self.table_db.insert({
            'X': X, 
            'Y': Y, 
            'Y_expected': np.full_like(Y, 'N/A', dtype=object),
            'Y_uncertainty': np.full_like(Y, 'N/A', dtype=object),
            'pareto': is_pareto, 
            'config_id': np.zeros(self.n_init_sample, dtype=int), 
            'batch_id': np.zeros(self.n_init_sample, dtype=int)
        })

    def _clear_design_space(self):
        '''
        Clear design space value and annotation
        '''
        if self.annotate is not None:
            self.annotate.remove()
            self.annotate = None
        if self.line_x is not None:
            self.line_x.remove()
            self.line_x = None
        if self.fill_x is not None:
            self.fill_x.remove()
            self.fill_x = None

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
        self.scatter_y.set_offsets(Y)
        self.scatter_y_pareto.set_offsets(Y[is_pareto])
        
        # rescale plot
        x_min, x_max = np.min(Y[:, 0]), np.max(Y[:, 0])
        y_min, y_max = np.min(Y[:, 1]), np.max(Y[:, 1])
        x_offset = (x_max - x_min) / 20
        y_offset = (y_max - y_min) / 20
        curr_x_min, curr_x_max = self.ax11.get_xlim()
        curr_y_min, curr_y_max = self.ax11.get_ylim()
        x_min, x_max = min(x_min - x_offset, curr_x_min), max(x_max + x_offset, curr_x_max)
        y_min, y_max = min(y_min - y_offset, curr_y_min), max(y_max + y_offset, curr_y_max)
        self.ax11.set_xlim(x_min, x_max)
        self.ax11.set_ylim(y_min, y_max)

        # replot new evaluated & predicted points
        if self.scatter_y_new is not None:
            self.scatter_y_new.remove()
            self.scatter_y_new = None
        if self.scatter_y_pred is not None:
            self.scatter_y_pred.remove()
            self.scatter_y_pred = None
        for line in self.line_y_pred_list:
            line.remove()
        self.line_y_pred_list = []

        if batch_id[-1] > 0:
            last_batch_idx = np.where(batch_id == batch_id[-1])[0]
            self.scatter_y_new = self.ax11.scatter(*Y[last_batch_idx].T, color='m', s=10, label='New evaluated points')
            self.scatter_y_pred = self.ax11.scatter(*Y_expected[last_batch_idx].T, facecolors='none', edgecolors='m', s=15, label='New predicted points')
            for y, y_expected in zip(Y[last_batch_idx], Y_expected[last_batch_idx]):
                line = self.ax11.plot([y[0], y_expected[0]], [y[1], y_expected[1]], '--', color='m', alpha=0.5)[0]
                self.line_y_pred_list.append(line)

        self.fig1.canvas.draw()

    def _redraw(self):
        '''
        Redraw figures and database viz
        '''
        # check if needs redraw
        if self.agent_data.get_sample_num() == self.n_curr_sample: return

        # load from database (TODO: optimize)
        X, Y, Y_expected, Y_uncertainty, hv_value, pred_error, is_pareto, config_id, batch_id = \
            self.agent_data.load(['X', 'Y', 'Y_expected', 'Y_uncertainty', 'hv', 'pred_error', 'is_pareto', 'config_id', 'batch_id'])
        n_prev_sample = self.n_curr_sample
        self.n_curr_sample = len(batch_id)

        # replot performance space if currently focusing on the lastest iteration
        if self.curr_iter.get() == self.max_iter:
            self.max_iter = batch_id[-1]
            self.scale_iter.configure(to=self.max_iter)
            self.curr_iter.set(self.max_iter)
            self._redraw_performance_space()
        else:
            self.max_iter = batch_id[-1]
            self.scale_iter.configure(to=self.max_iter)
            
        # replot hypervolume curve
        self.line_hv.set_data(list(range(self.n_curr_sample)), hv_value)
        self.ax21.relim()
        self.ax21.autoscale_view()
        self.ax21.set_title('Hypervolume: %.2f' % hv_value[-1])

        # replot prediction error curve
        self.line_error.set_data(list(range(self.n_init_sample, self.n_curr_sample)), pred_error[self.n_init_sample:])
        self.ax22.relim()
        self.ax22.autoscale_view()
        self.ax22.set_title('Model Prediction Error: %.2f%%' % pred_error[-1])

        # refresh figure
        self.fig2.canvas.draw()

        # update database viz (TODO: optimize)
        self.table_db.insert({
            'X': X[n_prev_sample:self.n_curr_sample], 
            'Y': Y[n_prev_sample:self.n_curr_sample], 
            'Y_expected': Y_expected[n_prev_sample:self.n_curr_sample],
            'Y_uncertainty': Y_uncertainty[n_prev_sample:self.n_curr_sample],
            'config_id': config_id[n_prev_sample:self.n_curr_sample], 
            'batch_id': batch_id[n_prev_sample:self.n_curr_sample],
        })

        self.table_db.update({
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
