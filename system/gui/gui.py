import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MaxNLocator
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import MouseButton


import os
import yaml
import numpy as np
from multiprocessing import Lock, Process
from problems.common import build_problem
from system.utils import process_config, load_config, get_available_algorithms, get_available_problems, find_closest_point
from system.gui.radar import radar_factory


class GUI:
    '''
    Interactive local tkinter-based GUI
    '''
    def __init__(self, init_command, optimize_command, predict_command, update_command, load_command, quit_command=None):
        '''
        GUI initialization
        Input:
            init_command: command for data storage & agent initialization
            optimize_command: command for algorithm optimization
            predict_command: command for design variable prediction
            update_command: command for database update
            load_command: command for data loading when GUI periodically refreshes
            quit_command: command when quitting program
        '''
        # GUI control panel
        self.root_ctrl = tk.Tk()
        self.root_ctrl.title('MOBO - Control')
        self.root_ctrl.configure(bg='white')
        self.root_ctrl.protocol("WM_DELETE_WINDOW", self._quit)

        # GUI visualization panel
        self.root_viz = tk.Tk()
        self.root_viz.title('MOBO - Visualization')
        self.root_viz.configure(bg='white')
        self.root_viz.protocol("WM_DELETE_WINDOW", self._quit)

        self.refresh_rate = 100 # ms
        self.result_dir = os.path.abspath('result')

        # interaction commands
        self.init_command = init_command
        self.optimize_command = optimize_command
        self.predict_command = predict_command
        self.update_command = update_command
        self.load_command = load_command
        self.quit_command = quit_command

        # running processes
        self.processes = []
        self.process_id = 0
        self.lock = Lock()

        # variables need to be initialized
        self.config = None
        self.config_raw = None
        self.config_id = -1

        # event widgets
        self.button_load = None
        self.button_customize = None
        self.button_optimize = None
        self.button_stop = None
        self.button_clear = None
        self.scrtext_config = None
        self.scrtext_log = None
        self.entry_path = None

        # data to be plotted
        self.scatter_x = None
        self.scatter_y = None
        self.scatter_y_pareto = None
        self.annotate = None
        self.line_hv = None
        self.line_error = None
        self.line_design = None
        self.fill_design = None
        self.n_init_sample = None
        self.n_curr_sample = None

        # widget initialization
        self._init_figure_widgets()
        self._init_storage_widgets()
        self._init_config_widgets()
        self._init_control_widgets()
        self._init_log_widgets()

    def _init_figure_widgets(self):
        '''
        GUI figure widgets initialization
        Layout:
            Figure 1: performance space (evaluated points, approximated Pareto front and true Pareto front)
            Figure 2: hypervolume curve (hypervolume value w.r.t. number of evaluations)
            Figure 3: surrogate model prediction error (averaged relative error w.r.t. number of evaluations) 
        '''
        # figure placeholder in GUI (NOTE: only 2-dim performance space is supported)
        self.fig = plt.figure(figsize=(13, 6))
        self.gs = GridSpec(6, 13, figure=self.fig)

        # performance space figure
        self.ax1 = self.fig.add_subplot(self.gs[:, 4:10])
        self.ax1.set_title('Performance Space')

        # hypervolume curve figure
        self.ax2 = self.fig.add_subplot(self.gs[:3, 10:])
        self.ax2.set_title('Hypervolume')
        self.ax2.set_xlabel('Evaluations')
        self.ax2.set_ylabel('Hypervolume')
        self.ax2.xaxis.set_major_locator(MaxNLocator(integer=True))

        # model prediction error figure
        self.ax3 = self.fig.add_subplot(self.gs[3:, 10:])
        self.ax3.set_title('Model Prediction Error')
        self.ax3.set_xlabel('Evaluations')
        self.ax3.set_ylabel('Averaged Relative Error (%)')
        self.ax3.xaxis.set_major_locator(MaxNLocator(integer=True))

        # design space figure
        n_var_init = 5
        self.theta = radar_factory(n_var_init)
        self.ax4 = self.fig.add_subplot(self.gs[1:5, :4], projection='radar')
        self.ax4.set_xticks(self.theta)
        self.ax4.set_varlabels([f'x{i + 1}' for i in range(n_var_init)])
        self.ax4.set_yticklabels([])
        self.ax4.set_title('Design Space', position=(0.5, 1.1))

        # connect matplotlib figure with tkinter GUI
        plt.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root_viz)
        self.canvas.draw()
        widget = self.canvas.get_tk_widget()
        widget.grid(row=0, column=0)

    def _init_storage_widgets(self):
        '''
        GUI data storage related widgets initialization
        Layout:
            Entry: display saving path
            Button "Browse": change saving path by opening file browser
        '''
        # storage overall frame
        frame_storage = tk.LabelFrame(master=self.root_ctrl, bg='white', text='Storage', font=('courier', 12, 'normal'))
        frame_storage.grid(row=0, column=0, padx=10, pady=10, sticky='NSEW')

        # description label
        label_path = tk.Label(master=frame_storage, bg='white', text='File location for data saving:')
        label_path.grid(row=0, column=0, padx=10, pady=10, sticky='W')

        # path display entry
        def sv_path_callback(sv):
            self.result_dir = sv.get()
        sv_path = tk.StringVar()
        sv_path.trace('w', lambda name, index, mode, sv=sv_path: sv_path_callback(sv))
        self.entry_path = tk.Entry(master=frame_storage, bg='white', textvariable=sv_path, width=36)
        self.entry_path.grid(row=1, column=0, padx=10, sticky='EW')
        self.entry_path.insert(tk.END, self.result_dir)

        # path change command
        button_path = tk.Button(master=frame_storage, text='Browse')
        button_path.grid(row=2, column=0, ipadx=30, padx=10, pady=10)

        def gui_change_saving_path():
            '''
            GUI change data saving path
            '''
            dirname = tk.filedialog.askdirectory(parent=self.root_ctrl)
            if not isinstance(dirname, str) or dirname == '': return

            self.entry_path.delete(0, tk.END)
            self.result_dir = dirname
            self.entry_path.insert(tk.END, self.result_dir)

        # link to commands
        button_path.configure(command=gui_change_saving_path)

    def _init_config_widgets(self):
        '''
        GUI configuration widgets initialization
        Layout:
            Button "Load": load configuration yaml file
            Button "Customize": customize configuration from GUI
            ScrolledText: display loaded/customized configuration
        '''
        # config overall frame
        frame_config = tk.LabelFrame(master=self.root_ctrl, bg='white', text='Configurations', font=('courier', 12, 'normal'))
        frame_config.grid(row=1, rowspan=2, column=0, padx=10, pady=10, sticky='NSEW')

        # config file loading command
        self.button_load = tk.Button(master=frame_config, text='Load')
        self.button_load.grid(row=0, column=0, ipadx=30, padx=5, pady=20)

        # config customization command
        self.button_customize = tk.Button(master=frame_config, text='Customize')
        self.button_customize.grid(row=0, column=1, ipadx=30, padx=5, pady=20)

        # config display
        self.scrtext_config = scrolledtext.ScrolledText(master=frame_config, width=10, height=10, state=tk.DISABLED)
        self.scrtext_config.grid(row=1, column=0, columnspan=2, ipadx=80, ipady=120, padx=5, pady=10, sticky='NSEW')

        def gui_open_file():
            '''
            GUI load config from file
            '''
            filename = tk.filedialog.askopenfilename(parent=self.root_ctrl)
            if not isinstance(filename, str) or filename == '': return

            try:
                config = load_config(filename)
            except:
                tk.messagebox.showinfo('Error', 'Invalid yaml file', parent=self.root_ctrl)
                self.button_optimize.configure(state=tk.DISABLED)
                return
                
            self._set_config(config)

        def gui_customize():
            '''
            GUI customize configurations from popup window
            '''
            window = tk.Toplevel(master=self.root_ctrl)
            window.title('Customize Configurations')
            window.configure(bg='white')

            # predefined formatting
            title_font = ('courier', 12, 'normal')
            label_font = ('courier', 10, 'normal')
            entry_width = 5
            combobox_width = 10

            # widget creation tools
            def create_frame(master, row, column, text):
                frame = tk.LabelFrame(master=master, bg='white', text=text, font=title_font)
                frame.grid(row=row, column=column, padx=10, pady=10, sticky='NSEW')
                return frame

            def create_label(master, row, column, text):
                label = tk.Label(master=master, bg='white', text=text, font=label_font)
                label.grid(row=row, column=column, padx=10, pady=10, sticky='W')

            def create_multiple_label(master, text_list):
                for i, text in enumerate(text_list):
                    create_label(master=master, row=i, column=0, text=text)

            def create_entry(master, row, column, class_type, width=entry_width, valid_check=None):
                entry = tk.Entry(master=master, bg='white', width=width)
                entry.grid(row=row, column=column, padx=10, pady=10, sticky='W')
                return class_type(entry, valid_check=valid_check)

            def create_combobox(master, row, column, values, valid_check=None):
                combobox = ttk.Combobox(master=master, values=values, width=combobox_width)
                combobox.grid(row=row, column=column, padx=10, pady=10, sticky='W')
                return Entry(combobox, valid_check=valid_check)

            def create_button(master, row, column, text, command):
                button = tk.Button(master=master, text=text, command=command)
                button.grid(row=row, column=column, padx=10, pady=10)
                return button

            # parameter section
            frame_param = tk.Frame(master=window, bg='white')
            frame_param.grid(row=0, column=0)

            # general subsection
            frame_general = create_frame(frame_param, 0, 0, 'General')
            create_multiple_label(frame_general, ['n_init_sample*', 'batch_size*', 'n_iter*', 'n_process'])
            entry_general_0 = create_entry(frame_general, 0, 1, IntEntry, valid_check=lambda x: x > 0)
            entry_general_1 = create_entry(frame_general, 1, 1, IntEntry, valid_check=lambda x: x > 0)
            entry_general_2 = create_entry(frame_general, 2, 1, IntEntry, valid_check=lambda x: x > 0)
            entry_general_3 = create_entry(frame_general, 3, 1, IntEntry, valid_check=lambda x: x > 0)

            # problem subsection
            frame_problem = create_frame(frame_param, 0, 1, 'Problem')
            create_multiple_label(frame_problem, ['name*', 'n_var*', 'n_obj*', 'xl', 'xu', 'var_name', 'obj_name', 'ref_point'])
            combobox_problem_0 = create_combobox(frame_problem, 0, 1, get_available_problems(), valid_check=lambda x: x in get_available_problems())
            entry_problem_1 = create_entry(frame_problem, 1, 1, IntEntry, valid_check=lambda x: x > 0)
            entry_problem_2 = create_entry(frame_problem, 2, 1, IntEntry, valid_check=lambda x: x > 0)
            entry_problem_3 = create_entry(frame_problem, 3, 1, FloatListEntry, width=10, valid_check=lambda x: x == '' or len(x) in [1, entry_problem_1.get()])
            entry_problem_4 = create_entry(frame_problem, 4, 1, FloatListEntry, width=10, valid_check=lambda x: x == '' or len(x) in [1, entry_problem_1.get()])
            entry_problem_5 = create_entry(frame_problem, 5, 1, StringListEntry, width=10, valid_check=lambda x: x == '' or len(x) == entry_problem_1.get())
            entry_problem_6 = create_entry(frame_problem, 6, 1, StringListEntry, width=10, valid_check=lambda x: x == '' or len(x) == entry_problem_2.get())
            entry_problem_7 = create_entry(frame_problem, 7, 1, FloatListEntry, width=10, valid_check=lambda x: x == '' or len(x) == entry_problem_2.get())

            # algorithm subsection
            frame_algorithm = create_frame(frame_param, 0, 2, 'Algorithm')
            create_multiple_label(frame_algorithm, ['name*'])
            combobox_algorithm_0 = create_combobox(frame_algorithm, 0, 1, get_available_algorithms(), valid_check=lambda x: x in get_available_algorithms())

            def save_config():
                '''
                Save specified configuration values
                '''
                try:
                    config = {
                        'general': {
                            'n_init_sample': entry_general_0.get(), 
                            'batch_size': entry_general_1.get(),
                            'n_iter': entry_general_2.get(),
                            'n_process': entry_general_3.get(),
                        },
                        'problem': {
                            'name': combobox_problem_0.get(),
                            'n_var': entry_problem_1.get(),
                            'n_obj': entry_problem_2.get(),
                            'xl': entry_problem_3.get(),
                            'xu': entry_problem_4.get(),
                            'var_name': entry_problem_5.get(),
                            'obj_name': entry_problem_6.get(),
                            'ref_point': entry_problem_7.get(),
                        },
                        'algorithm': {
                            'name': combobox_algorithm_0.get(),
                        }
                    }
                    config = process_config(config)
                except:
                    tk.messagebox.showinfo('Error', 'Invalid configurations', parent=window)
                    return

                self._set_config(config)
                window.destroy()

            # action section
            frame_action = tk.Frame(master=window, bg='white')
            frame_action.grid(row=1, column=0, columnspan=3)
            create_button(frame_action, 0, 0, 'Save', save_config)
            create_button(frame_action, 0, 1, 'Cancel', window.destroy)

        # link to commands
        self.button_load.configure(command=gui_open_file)
        self.button_customize.configure(command=gui_customize)

    def _init_control_widgets(self):
        '''
        GUI control widgets initialization
        Layout:
            Button "Optimize": run an algorithm optimization
            Button "Stop" stop all algorithm optimizations
        '''
        # control overall frame
        frame_control = tk.LabelFrame(master=self.root_ctrl, bg='white', text='Control', font=('courier', 12, 'normal'))
        frame_control.grid(row=0, column=1, padx=10, pady=10, sticky='NSEW')

        # optimization command
        self.button_optimize = tk.Button(master=frame_control, text="Optimize", state=tk.DISABLED)
        self.button_optimize.grid(row=0, column=0, ipadx=40, padx=5, pady=20)

        # stop optimization command
        self.button_stop = tk.Button(master=frame_control, text='Stop', state=tk.DISABLED)
        self.button_stop.grid(row=0, column=1, ipadx=20, padx=5, pady=20)

        # get design variables from user input
        self.button_input = tk.Button(master=frame_control, text='User Input', state=tk.DISABLED)
        self.button_input.grid(row=1, column=0, columnspan=2, ipadx=30, padx=10, pady=0)

        def gui_optimize():
            '''
            GUI execute optimization
            '''
            self.button_load.configure(state=tk.DISABLED)
            self.button_customize.configure(state=tk.DISABLED)
            self.button_stop.configure(state=tk.NORMAL)
            worker = Process(target=self.optimize_command, args=(self.config, self.config_id))
            worker.start()
            self.processes.append([self.process_id, worker])
            self._log(f'worker {self.process_id} started')
            self.process_id += 1

        def gui_stop_optimize():
            '''
            GUI stop optimization
            '''
            with self.lock:
                for p in self.processes:
                    pid, worker = p
                    if worker.is_alive():
                        worker.terminate()
                        self._log(f'worker {pid} interrupted')
                self.processes = []
            self.button_stop.configure(state=tk.DISABLED)

        def gui_user_input():
            '''
            GUI getting design variables from user input
            '''
            window = tk.Toplevel(master=self.root_ctrl)
            window.title('User Input')
            window.configure(bg='white')

            # description label
            label_x = tk.Label(master=window, bg='white', text='Design variable values (seperated by ","):')
            label_x.grid(row=0, column=0, padx=10, pady=10, sticky='W')

            # design variable entry
            entry_x = tk.Entry(master=window, bg='white', width=50)
            entry_x.grid(row=1, column=0, padx=10, sticky='EW')
            entry_x = FloatListEntry(widget=entry_x, valid_check=lambda x: len(x) == self.config['problem']['n_var'])

            # evaluation checkbox
            eval_var = tk.IntVar()
            checkbutton_eval = tk.Checkbutton(master=window, bg='white', text='Ask before evaluation', variable=eval_var)
            checkbutton_eval.grid(row=2, column=0, padx=10, pady=10)

            # add input design variables
            button_add = tk.Button(master=window, text='Add')
            button_add.grid(row=3, column=0, ipadx=40, padx=10, pady=10)

            def add_user_input():
                '''
                Predict performance of user inputted design variables, optionally do real evaluation and add to database
                '''
                # TODO: add batch input support
                try:
                    X_next = np.atleast_2d(entry_x.get())
                except:
                    tk.messagebox.showinfo('Error', 'Invalid design values', parent=window)
                    return

                if_eval = eval_var.get() == 1
                window.destroy()

                Y_expected, Y_uncertainty = self.predict_command(self.config, X_next)

                if if_eval:
                    window2 = tk.Toplevel(master=self.root_ctrl)
                    window2.title('Prediction Completed')
                    window2.configure(bg='white')

                    # Y_expected description
                    label_y_mean = tk.Label(master=window2, bg='white', text=f'Y_expected: ({",".join([str(y) for y in Y_expected.squeeze()])})')
                    label_y_mean.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky='W')

                    # Y_uncertainty description
                    label_y_std = tk.Label(master=window2, bg='white', text=f'Y_uncertainty: ({",".join([str(y) for y in Y_uncertainty.squeeze()])})')
                    label_y_std.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='W')

                    # evaluate button
                    button_eval = tk.Button(master=window2, text='Evaluate')
                    button_eval.grid(row=2, column=0, ipadx=30, padx=10, pady=10)

                    # cancel button
                    button_cancel = tk.Button(master=window2, text='Cancel')
                    button_cancel.grid(row=2, column=1, ipadx=30, padx=10, pady=10)

                    def eval_user_input():
                        self.update_command(self.config, X_next, Y_expected, Y_uncertainty, self.config_id)
                        # TODO: highlight user input in viz
                        window2.destroy()

                    button_eval.configure(command=eval_user_input)
                    button_cancel.configure(command=window2.destroy)
                else:
                    self.update_command(self.config, X_next, Y_expected, Y_uncertainty, self.config_id)
                    # TODO: highlight user input in viz

            button_add.configure(command=add_user_input)

        # link to commands
        self.button_optimize.configure(command=gui_optimize)
        self.button_stop.configure(command=gui_stop_optimize)
        self.button_input.configure(command=gui_user_input)

    def _init_log_widgets(self):
        '''
        GUI log widgets initialization
        Layout:
            ScrolledText: display log info
            Button "clear": clear log info
        '''
        # log overall frame
        frame_log = tk.LabelFrame(master=self.root_ctrl, bg='white', text='Log', font=('courier', 12, 'normal'))
        frame_log.grid(row=1, rowspan=2, column=1, padx=10, pady=10, sticky='NSEW')

        # log display
        self.scrtext_log = scrolledtext.ScrolledText(master=frame_log, width=10, height=10, state=tk.DISABLED)
        self.scrtext_log.grid(row=0, column=0, ipadx=90, ipady=120, padx=5, pady=10, sticky='NSEW')

        # log clear command
        self.button_clear = tk.Button(master=frame_log, text="Clear")
        self.button_clear.grid(row=1, column=0, ipadx=40, padx=5, pady=10, sticky='N')

        def gui_log_clear():
            '''
            Clear texts in GUI log
            '''
            self.scrtext_log.configure(state=tk.NORMAL)
            self.scrtext_log.delete('1.0', tk.END)
            self.scrtext_log.configure(state=tk.DISABLED)

        # link to commands
        self.button_clear.configure(command=gui_log_clear)

    def _save_config(self, config):
        '''
        Save configurations to file
        '''
        self.config_id += 1
        with open(os.path.join(self.result_dir, 'config', f'config_{self.config_id}.yml'), 'w') as fp:
            yaml.dump(config, fp, default_flow_style=False, sort_keys=False)

    def _set_config(self, config):
        '''
        GUI setting configurations
        '''
        # update raw config (config will be processed and changed later in build_problem())
        self.config_raw = config.copy()

        if self.config is None: # first time setting config
            # check if result_dir folder exists
            if os.path.exists(self.result_dir):
                tk.messagebox.showinfo('Error', f'Folder {self.result_dir} exists, please change another folder')
                return

            os.makedirs(self.result_dir)
            config_dir = os.path.join(self.result_dir, 'config')
            os.makedirs(config_dir)

            # initialize problem and data storage
            try:
                _, true_pfront = build_problem(config['problem'], get_pfront=True)
                self.init_command(config, self.result_dir)
            except:
                tk.messagebox.showinfo('Error', 'Invalid values in configuration')
                return

            self.config = config

            # update plot
            f1_name, f2_name = self.config['problem']['obj_name']
            self.ax1.set_xlabel(f1_name)
            self.ax1.set_ylabel(f2_name)

            n_var = self.config['problem']['n_var']
            self.theta = radar_factory(n_var)
            self.fig.delaxes(self.ax4)
            self.ax4 = self.fig.add_subplot(self.gs[1:5, :4], projection='radar')
            self.ax4.set_xticks(self.theta)
            var_name, self.xl, self.xu = self.config['problem']['var_name'], np.array(self.config['problem']['xl']), np.array(self.config['problem']['xu'])
            self.ax4.set_varlabels([f'{var_name[i]}\n[{self.xl[i]},{self.xu[i]}]' for i in range(n_var)])
            self.ax4.set_yticklabels([])
            self.ax4.set_title('Design Space', position=(0.5, 1.1))
            self.ax4.set_ylim(0, 1)

            self._init_draw(true_pfront)

            # lock path entry
            self.entry_path.configure(state=tk.DISABLED)

            # activate optimization button
            self.button_optimize.configure(state=tk.NORMAL)
            self.button_input.configure(state=tk.NORMAL)

            # refresh config display
            self.scrtext_config.configure(state=tk.NORMAL)
            self.scrtext_config.insert(tk.INSERT, yaml.dump(self.config, default_flow_style=False, sort_keys=False))
            self.scrtext_config.configure(state=tk.DISABLED)

            # trigger periodic refresh
            self.root_ctrl.after(self.refresh_rate, self._refresh)

        else: # user changed config in the middle
            try:
                # some keys cannot be changed
                for key in ['n_init_sample']:
                    assert self.config_raw['general'][key] == config['general'][key]
                for key in ['name', 'n_var', 'n_obj', 'var_name', 'obj_name', 'ref_point']: # TODO
                    assert self.config_raw['problem'][key] == config['problem'][key]           
            except:
                tk.messagebox.showinfo('Error', 'Invalid configuration values for reloading')
                return

            self.config = config

            # refresh config display
            self.scrtext_config.configure(state=tk.NORMAL)
            self.scrtext_config.delete('1.0', tk.END)
            self.scrtext_config.insert(tk.INSERT, yaml.dump(self.config, default_flow_style=False, sort_keys=False))
            self.scrtext_config.configure(state=tk.DISABLED)
        
        self._save_config(self.config)

    def _init_draw(self, true_pfront):
        '''
        First draw of performance space, hypervolume curve and model prediction error
        '''
        # load from database
        X, Y, Y_pareto, hv_value, _ = self.load_command()

        # update status
        self.n_init_sample = len(Y)
        self.n_curr_sample = self.n_init_sample

        # plot performance space
        if true_pfront is not None:
            self.ax1.scatter(*true_pfront.T, color='gray', s=5, label='True Pareto front') # plot true pareto front
        self.scatter_x = X
        self.scatter_y = self.ax1.scatter(*Y.T, color='blue', s=10, label='Evaluated points')
        self.scatter_y_pareto = self.ax1.scatter(*Y_pareto.T, color='red', s=10, label='Approximated Pareto front')
        self.ax1.legend(loc='upper right')

        # plot hypervolume curve
        self.line_hv = self.ax2.plot(list(range(self.n_init_sample)), hv_value)[0]
        self.ax2.set_title('Hypervolume: %.2f' % hv_value[-1])

        # plot prediction error curve
        self.line_error = self.ax3.plot([], [])[0]

         # mouse clicking event
        def check_design_values(event):
            if event.inaxes != self.ax1: return
            if event.button == MouseButton.LEFT:
                loc = [event.xdata, event.ydata]
                all_y = self.scatter_y._offsets
                closest_y, closest_idx = find_closest_point(loc, all_y, return_index=True)
                closest_x = self.scatter_x[closest_idx]
                x_str = '\n'.join([f'{name}: {val:.4g}' for name, val in zip(self.config['problem']['var_name'], closest_x)])
                if self.annotate is not None:
                    self.annotate.remove()
                    self.annotate = None
                if self.line_design is not None:
                    self.line_design.remove()
                    self.fill_design.remove()
                    self.line_design = None
                    self.fill_design = None
                y_range = np.max(all_y, axis=0) - np.min(all_y, axis=0)
                text_loc = [closest_y[i] + 0.05 * y_range[i] for i in range(2)]
                self.annotate = self.ax1.annotate(x_str, xy=closest_y, xytext=text_loc,
                    bbox=dict(boxstyle="round", fc="w", alpha=0.7),
                    arrowprops=dict(arrowstyle="->"))
                transformed_x = (np.array(closest_x) - self.xl) / (self.xu - self.xl)
                self.line_design = self.ax4.plot(self.theta, transformed_x)[0]
                self.fill_design = self.ax4.fill(self.theta, transformed_x, alpha=0.2)[0]
            elif event.button == MouseButton.RIGHT:
                if self.annotate is not None:
                    self.annotate.remove()
                    self.annotate = None
                if self.line_design is not None:
                    self.line_design.remove()
                    self.fill_design.remove()
                    self.line_design = None
                    self.fill_design = None
                
            self.fig.canvas.draw()
        
        self.fig.canvas.mpl_connect('button_press_event', check_design_values)

        # refresh figure
        self.fig.canvas.draw()

    def _log(self, string):
        '''
        Log texts to ScrolledText widget for logging
        '''
        self.scrtext_log.configure(state=tk.NORMAL)
        self.scrtext_log.insert(tk.INSERT, string + '\n')
        self.scrtext_log.configure(state=tk.DISABLED)

    def _refresh(self):
        '''
        Refresh current GUI status and redraw if data has changed
        '''
        self._check_status()
        self._redraw()
        self.root_ctrl.after(self.refresh_rate, self._refresh)

    def _check_status(self):
        '''
        Check if current processes are alive
        '''
        with self.lock:
            completed_ps = []
            for p in self.processes:
                pid, worker = p
                if not worker.is_alive():
                    completed_ps.append(p)
                    self._log(f'worker {pid} completed')
            for p in completed_ps:
                self.processes.remove(p)
        if len(self.processes) == 0:
            self.button_stop.configure(state=tk.DISABLED)
            self.button_load.configure(state=tk.NORMAL)
            self.button_customize.configure(state=tk.NORMAL)

    def _redraw(self):
        '''
        Redraw performance space, hypervolume curve and model prediction error
        '''
        # load from database
        X, Y, Y_pareto, hv_value, pred_error = self.load_command()

        # check if needs redraw
        if len(Y) == self.n_curr_sample: return
        self.n_curr_sample = len(Y)

        # replot performance space
        self.scatter_x = X
        self.scatter_y.set_offsets(Y)
        self.scatter_y_pareto.set_offsets(Y_pareto)

        # replot hypervolume curve
        self.line_hv.set_data(list(range(len(Y))), hv_value)
        self.ax2.relim()
        self.ax2.autoscale_view()
        self.ax2.set_title('Hypervolume: %.2f' % hv_value[-1])

        # replot prediction error curve
        self.line_error.set_data(list(range(self.n_init_sample, len(Y))), pred_error[self.n_init_sample:])
        self.ax3.relim()
        self.ax3.autoscale_view()
        self.ax3.set_title('Model Prediction Error: %.2f%%' % pred_error[-1])

        # refresh figure
        self.fig.canvas.draw()

    def mainloop(self):
        '''
        Start mainloop of GUI
        '''
        tk.mainloop()

    def _quit(self):
        '''
        GUI quit handling
        '''
        if self.quit_command is not None:
            self.quit_command()

        for p in self.processes:
            _, worker = p
            worker.terminate()

        self.root_ctrl.quit()
        self.root_ctrl.destroy()
        self.root_viz.quit()
        self.root_viz.destroy()


class Entry:
    '''
    Entry widget creation tools
    '''
    def __init__(self, widget, valid_check=None):
        self.widget = widget
        self.valid_check = valid_check
    def get(self):
        val = self.widget.get()
        if val == '':
            return None
        result = self._get(val)
        if self.valid_check is not None:
            if not self.valid_check(result):
                raise Exception('Invalid value specified in the entry')
        return result
    def _get(self, val):
        return val

class IntEntry(Entry):
    def _get(self, val):
        return int(val)

class FloatEntry(Entry):
    def _get(self, val):
        return float(val)
        
class FloatListEntry(Entry):
    def _get(self, val):
        return [float(num) for num in val.split(',')]

class StringListEntry(Entry):
    def _get(self, val):
        return val.split(',')