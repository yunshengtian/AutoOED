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
from problems.common import build_problem
from system.agent import Agent
from system.utils import process_config, load_config, get_available_algorithms, get_available_problems, find_closest_point
from system.gui.radar import radar_factory
from system.gui.utils import *


class GUI:
    '''
    Interactive local tkinter-based GUI
    '''
    def __init__(self):
        '''
        GUI initialization
        '''
        # GUI
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

        self.refresh_rate = 100 # ms
        self.result_dir = os.path.abspath('result') # initial result directory

        # agent
        self.agent = None

        # running processes
        self.processes = []
        self.process_id = 0
        self.lock = Lock()

        # config related
        self.config = None
        self.config_raw = None
        self.config_id = -1

        # event widgets
        self.button_optimize = None
        self.button_stop = None
        self.button_clear = None
        self.scrtext_config = None
        self.scrtext_log = None

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
        self._init_menu()
        self._init_figure_widgets()
        self._init_control_widgets()
        self._init_display_widgets()

    def _init_menu(self):
        '''
        GUI menu initialization
        '''
        # top-level menu
        self.menu = tk.Menu(master=self.root, relief='raised')
        self.root.config(menu=self.menu)

        # sub-level menu
        self.menu_file = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='File', menu=self.menu_file)
        self.menu_config = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='Config', menu=self.menu_config)
        self.menu_log = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='Log', menu=self.menu_log)

        def gui_change_saving_path():
            '''
            GUI change data saving path
            '''
            dirname = tk.filedialog.askdirectory(parent=self.root)
            if not isinstance(dirname, str) or dirname == '': return
            self.result_dir = dirname

        # link menu entry command
        self.menu_file.add_command(label='Choose saving location', command=gui_change_saving_path)

    def _init_figure_widgets(self):
        '''
        GUI figure widgets initialization (visualization, statistics)
        '''
        frame_figure = tk.Frame(master=self.root)
        frame_figure.grid(row=0, column=0, rowspan=2, sticky='NSEW')
        grid_configure(frame_figure, [0], [0])

        # configure tab widgets
        nb = ttk.Notebook(master=frame_figure)
        nb.grid(row=0, column=0, sticky='NSEW')
        frame_viz = tk.Frame(master=nb)
        frame_stat = tk.Frame(master=nb)
        grid_configure(frame_viz, [0], [0])
        grid_configure(frame_stat, [0], [0])
        nb.add(child=frame_viz, text='Visualization')
        nb.add(child=frame_stat, text='Statistics')

        # configure slider widget
        frame_slider = tk.Frame(master=frame_figure)
        frame_slider.grid(row=1, column=0, pady=5, sticky='EW')
        grid_configure(frame_slider, [0], [1])
        
        label_iter = tk.Label(master=frame_slider, text='Iteration:')
        label_iter.grid(row=0, column=0, sticky='EW')
        self.scale_iter = tk.Scale(master=frame_slider, orient=tk.HORIZONTAL, from_=0, to=0)
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
        embed_figure(self.fig1, frame_viz)
        embed_figure(self.fig2, frame_stat)

    def _init_control_widgets(self):
        '''
        GUI control widgets initialization (optimize, stop, user input, show history)
        '''
        # control overall frame
        frame_control = tk.Frame(master=self.root)
        frame_control.grid(row=0, column=1, sticky='NSEW')

        # optimization command
        self.button_optimize = tk.Button(master=frame_control, text="Optimize", state=tk.DISABLED)
        self.button_optimize.grid(row=0, column=0, padx=5, pady=20, sticky='NSEW')

        # stop optimization command
        self.button_stop = tk.Button(master=frame_control, text='Stop', state=tk.DISABLED)
        self.button_stop.grid(row=0, column=1, padx=5, pady=20, sticky='NSEW')

        # get design variables from user input
        self.button_input = tk.Button(master=frame_control, text='User Input', state=tk.DISABLED)
        self.button_input.grid(row=1, column=0, padx=5, pady=5, sticky='NSEW')

        # show optimization history
        self.button_history = tk.Button(master=frame_control, text='Show History', state=tk.DISABLED)
        self.button_history.grid(row=1, column=1, padx=5, pady=5, sticky='NSEW')

        def gui_optimize():
            '''
            GUI execute optimization
            '''
            self.menu_config.entryconfig(0, state=tk.DISABLED)
            self.menu_config.entryconfig(1, state=tk.DISABLED)
            self.button_stop.configure(state=tk.NORMAL)
            worker = Process(target=self.agent.optimize, args=(self.config, self.config_id))
            self._start_worker(worker)

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
            window = tk.Toplevel(master=self.root)
            window.title('User Input')
            window.configure(bg='white')

            # description label
            label_x = tk.Label(master=window, bg='white', text='Design variable values (seperated by ","):')
            label_x.grid(row=0, column=0, padx=10, pady=10, sticky='W')

            # design variable entry
            entry_x = tk.Entry(master=window, bg='white', width=50)
            entry_x.grid(row=1, column=0, padx=10, sticky='EW')
            entry_x = FloatListEntry(widget=entry_x, valid_check=lambda x: len(x) == self.config['problem']['n_var'])

            # ask before evaluation checkbox
            ask_var = tk.IntVar()
            checkbutton_ask = tk.Checkbutton(master=window, bg='white', text='Ask before evaluation', variable=ask_var)
            checkbutton_ask.grid(row=2, column=0, padx=10, pady=10)

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

                ask = ask_var.get() == 1
                window.destroy()

                Y_expected, Y_uncertainty = self.agent.predict(self.config, X_next)

                if ask:
                    window2 = tk.Toplevel(master=self.root)
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
                        worker = Process(target=self.agent.update, args=(self.config, X_next, Y_expected, Y_uncertainty, self.config_id))
                        self._start_worker(worker)
                        window2.destroy()

                    button_eval.configure(command=eval_user_input)
                    button_cancel.configure(command=window2.destroy)
                else:
                    worker = Process(target=self.agent.update, args=(self.config, X_next, Y_expected, Y_uncertainty, self.config_id))
                    self._start_worker(worker)

            button_add.configure(command=add_user_input)

        def gui_show_history():
            # TODO
            pass

        # link to commands
        self.button_optimize.configure(command=gui_optimize)
        self.button_stop.configure(command=gui_stop_optimize)
        self.button_input.configure(command=gui_user_input)
        self.button_history.configure(command=gui_show_history)

    def _init_display_widgets(self):
        '''
        GUI display widgets initialization (config, log)
        '''
        # configure tab widgets
        nb = ttk.Notebook(master=self.root)
        nb.grid(row=1, column=1, sticky='NSEW')
        frame_config = tk.Frame(master=nb)
        frame_log = tk.Frame(master=nb)
        nb.add(child=frame_config, text='Config')
        nb.add(child=frame_log, text='Log')

        # configure for resolution change
        grid_configure(frame_config, [0], [0])
        grid_configure(frame_log, [0], [0])

        # config display
        self.scrtext_config = scrolledtext.ScrolledText(master=frame_config, width=10, height=10, state=tk.DISABLED)
        self.scrtext_config.grid(row=0, column=0, sticky='NSEW')

        def gui_open_file():
            '''
            GUI load config from file
            '''
            filename = tk.filedialog.askopenfilename(parent=self.root)
            if not isinstance(filename, str) or filename == '': return

            try:
                config = load_config(filename)
            except:
                tk.messagebox.showinfo('Error', 'Invalid yaml file', parent=self.root)
                self.button_optimize.configure(state=tk.DISABLED)
                return
                
            self._set_config(config)

        def gui_customize():
            '''
            GUI customize configurations from popup window
            '''
            window = tk.Toplevel(master=self.root)
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
        self.menu_config.add_command(label='Load', command=gui_open_file)
        self.menu_config.add_command(label='Customize', command=gui_customize)

        # log display
        self.scrtext_log = scrolledtext.ScrolledText(master=frame_log, width=10, height=10, state=tk.DISABLED)
        self.scrtext_log.grid(row=0, column=0, sticky='NSEW')

        def gui_log_clear():
            '''
            Clear texts in GUI log
            '''
            self.scrtext_log.configure(state=tk.NORMAL)
            self.scrtext_log.delete('1.0', tk.END)
            self.scrtext_log.configure(state=tk.DISABLED)

        # link to commands
        self.menu_log.add_command(label='Clear', command=gui_log_clear)

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

            # initialize problem and data storage (agent)
            try:
                _, true_pfront = build_problem(config['problem'], get_pfront=True)
                self.agent = Agent(config, self.result_dir)
            except:
                tk.messagebox.showinfo('Error', 'Invalid values in configuration')
                return

            self.config = config

            # update plot
            f1_name, f2_name = self.config['problem']['obj_name']
            self.ax11.set_xlabel(f1_name)
            self.ax11.set_ylabel(f2_name)

            n_var = self.config['problem']['n_var']
            self.theta = radar_factory(n_var)
            self.fig1.delaxes(self.ax12)
            self.ax12 = self.fig1.add_subplot(self.gs1[1], projection='radar')
            self.ax12.set_xticks(self.theta)
            var_name, self.xl, self.xu = self.config['problem']['var_name'], np.array(self.config['problem']['xl']), np.array(self.config['problem']['xu'])
            self.ax12.set_varlabels([f'{var_name[i]}\n[{self.xl[i]},{self.xu[i]}]' for i in range(n_var)])
            self.ax12.set_yticklabels([])
            self.ax12.set_title('Design Space', position=(0.5, 1.1))
            self.ax12.set_ylim(0, 1)

            self._init_draw(true_pfront)

            # disable changing saving location
            self.menu_file.entryconfig(0, state=tk.DISABLED)

            # activate optimization button
            self.button_optimize.configure(state=tk.NORMAL)
            self.button_input.configure(state=tk.NORMAL)

            # refresh config display
            self.scrtext_config.configure(state=tk.NORMAL)
            self.scrtext_config.insert(tk.INSERT, yaml.dump(self.config, default_flow_style=False, sort_keys=False))
            self.scrtext_config.configure(state=tk.DISABLED)

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
        X, Y, hv_value, is_pareto = self.agent.load(['X', 'Y', 'hv', 'is_pareto'])

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
            if event.button == MouseButton.LEFT and event.dblclick:
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
                self.annotate = self.ax11.annotate(x_str, xy=closest_y, xytext=text_loc,
                    bbox=dict(boxstyle="round", fc="w", alpha=0.7),
                    arrowprops=dict(arrowstyle="->"))
                transformed_x = (np.array(closest_x) - self.xl) / (self.xu - self.xl)
                self.line_design = self.ax12.plot(self.theta, transformed_x)[0]
                self.fill_design = self.ax12.fill(self.theta, transformed_x, alpha=0.2)[0]
            elif event.button == MouseButton.RIGHT:
                if self.annotate is not None:
                    self.annotate.remove()
                    self.annotate = None
                if self.line_design is not None:
                    self.line_design.remove()
                    self.fill_design.remove()
                    self.line_design = None
                    self.fill_design = None
                
            self.fig1.canvas.draw()
        
        self.fig1.canvas.mpl_connect('button_press_event', check_design_values)

        # refresh figure
        self.fig1.canvas.draw()
        self.fig2.canvas.draw()

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
        self.root.after(self.refresh_rate, self._refresh)

    def _start_worker(self, worker):
        '''
        Start a worker process
        '''
        worker.start()
        self.processes.append([self.process_id, worker])
        self._log(f'worker {self.process_id} started')
        self.process_id += 1

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
            self.menu_config.entryconfig(0, state=tk.NORMAL)
            self.menu_config.entryconfig(1, state=tk.NORMAL)

    def _redraw(self):
        '''
        Redraw performance space, hypervolume curve and model prediction error
        '''
        # load from database
        X, Y, Y_expected, hv_value, pred_error, is_pareto, batch_id = self.agent.load(['X', 'Y', 'Y_expected', 'hv', 'pred_error', 'is_pareto', 'batch_id'])

        # check if needs redraw
        if len(Y) == self.n_curr_sample: return
        self.n_curr_sample = len(Y)

        # replot performance space
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
        self.scatter_y_new.remove()
        self.scatter_y_pred.remove()
        for line in self.line_y_pred_list:
            line.remove()
        self.line_y_pred_list = []

        last_batch_idx = np.where(batch_id == batch_id[-1])[0]
        self.scatter_y_new = self.ax11.scatter(*Y[last_batch_idx].T, color='m', s=10, label='New evaluated points')
        self.scatter_y_pred = self.ax11.scatter(*Y_expected[last_batch_idx].T, facecolors='none', edgecolors='m', s=15, label='New predicted points')
        for y, y_expected in zip(Y[last_batch_idx], Y_expected[last_batch_idx]):
            line = self.ax11.plot([y[0], y_expected[0]], [y[1], y_expected[1]], '--', color='m', alpha=0.5)[0]
            self.line_y_pred_list.append(line)
            
        # replot hypervolume curve
        self.line_hv.set_data(list(range(len(Y))), hv_value)
        self.ax21.relim()
        self.ax21.autoscale_view()
        self.ax21.set_title('Hypervolume: %.2f' % hv_value[-1])

        # replot prediction error curve
        self.line_error.set_data(list(range(self.n_init_sample, len(Y))), pred_error[self.n_init_sample:])
        self.ax22.relim()
        self.ax22.autoscale_view()
        self.ax22.set_title('Model Prediction Error: %.2f%%' % pred_error[-1])

        # refresh figure
        self.fig1.canvas.draw()
        self.fig2.canvas.draw()

    def mainloop(self):
        '''
        Start mainloop of GUI
        '''
        tk.mainloop()

    def _quit(self):
        '''
        GUI quit handling
        '''
        if self.agent is not None:
            self.agent.quit()

        for p in self.processes:
            _, worker = p
            worker.terminate()

        self.root.quit()
        self.root.destroy()
