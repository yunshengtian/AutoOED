import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MaxNLocator
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler

import os
import yaml
from multiprocessing import Lock, Process
from .utils import process_config, load_config, get_available_algorithms, get_available_problems


class InteractiveGUI:
    '''
    Interactive local tkinter-based GUI
    '''
    def __init__(self, data_format, init_command, optimize_command, load_command, quit_command=None):
        '''
        GUI initialization
        Input:
            data_format: format of data to be saved, e.g., 'csv', 'db'
            init_command: command for problem initialization (usage: init_command(config, data_path) -> problem, true_pfront)
            optimize_command: command for algorithm optimization (usage: optimize_command(process_id, config, data_path, problem))
            load_command: command for data loading when GUI periodically refreshes (usage: load_command(config, data_path) -> Y, Y_pareto, hv_value, pred_error)
            quit_command: command when quitting program (usage: quit_command())
        '''
        # GUI root
        self.root = tk.Tk()
        self.root.title('Multi-Objective Bayesian Optimization')
        self.root.configure(bg='white')
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        self.refresh_rate = 100 # ms
        self.data_format = data_format
        self.data_path = os.path.abspath('data.' + self.data_format)

        # interaction commands
        self.init_command = init_command
        self.optimize_command = optimize_command
        self.load_command = load_command
        self.quit_command = quit_command

        # running processes
        self.processes = []
        self.process_id = 0
        self.lock = Lock()

        # variables need to be initialized
        self.config = None
        self.problem = None

        # event widgets
        self.button_load = None
        self.button_customize = None
        self.button_optimize = None
        self.button_stop = None
        self.button_clear = None
        self.scrtext_config = None
        self.scrtext_log = None

        # data to be plotted
        self.scatter_y = None
        self.scatter_y_pareto = None
        self.line_hv = None
        self.line_error = None
        self.n_init_sample = None
        self.n_curr_sample = None

        # widget initialization
        self._init_figure_widgets()
        self._init_config_widgets()
        self._init_storage_widgets()
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
        # figure overall frame
        frame_figure = tk.LabelFrame(master=self.root, bg='white', text='Visualization', font=('courier', 12, 'normal'))
        frame_figure.grid(row=0, rowspan=3, column=1, padx=10, pady=10, sticky='NSEW')

        # figure placeholder in GUI (NOTE: only 2-dim performance space is supported)
        self.fig = plt.figure(figsize=(10, 6))
        gs = GridSpec(2, 3, figure=self.fig)

        # performance space figure
        self.ax1 = self.fig.add_subplot(gs[:, :2])
        self.ax1.set_title('Performance Space')

        # hypervolume curve figure
        self.ax2 = self.fig.add_subplot(gs[0, 2])
        self.ax2.set_title('Hypervolume')
        self.ax2.set_xlabel('Evaluations')
        self.ax2.set_ylabel('Hypervolume')
        self.ax2.xaxis.set_major_locator(MaxNLocator(integer=True))

        # model prediction error figure
        self.ax3 = self.fig.add_subplot(gs[1, 2])
        self.ax3.set_title('Model Prediction Error')
        self.ax3.set_xlabel('Evaluations')
        self.ax3.set_ylabel('Averaged Relative Error (%)')
        self.ax3.xaxis.set_major_locator(MaxNLocator(integer=True))

        # connect matplotlib figure with tkinter GUI
        plt.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_figure)
        self.canvas.draw()
        widget = self.canvas.get_tk_widget()
        widget.grid(row=0, column=1)

    def _init_config_widgets(self):
        '''
        GUI configuration widgets initialization
        Layout:
            Button "Load": load configuration yaml file
            Button "Customize": customize configuration from GUI
            ScrolledText: display loaded/customized configuration
        '''
        # config overall frame
        frame_config = tk.LabelFrame(master=self.root, bg='white', text='Configurations', font=('courier', 12, 'normal'))
        frame_config.grid(row=0, column=0, padx=10, pady=10, sticky='NSEW')

        # config file loading command
        self.button_load = tk.Button(master=frame_config, text='Load')
        self.button_load.grid(row=0, column=0, ipadx=30, padx=5, pady=20)

        # config customization command
        self.button_customize = tk.Button(master=frame_config, text='Customize')
        self.button_customize.grid(row=0, column=1, ipadx=30, padx=5, pady=20)

        # config display
        self.scrtext_config = scrolledtext.ScrolledText(master=frame_config, width=10, height=10, state=tk.DISABLED)
        self.scrtext_config.grid(row=1, column=0, columnspan=2, ipadx=80, ipady=80, padx=5, pady=10, sticky='NSEW')

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
            class Entry:
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
            create_multiple_label(frame_problem, ['name*', 'n_var*', 'n_obj*', 'var_name', 'obj_name', 'ref_point'])
            combobox_problem_0 = create_combobox(frame_problem, 0, 1, get_available_problems(), valid_check=lambda x: x in get_available_problems())
            entry_problem_1 = create_entry(frame_problem, 1, 1, IntEntry, valid_check=lambda x: x > 0)
            entry_problem_2 = create_entry(frame_problem, 2, 1, IntEntry, valid_check=lambda x: x > 0)
            entry_problem_3 = create_entry(frame_problem, 3, 1, StringListEntry, width=10, valid_check=lambda x: x == '' or len(x) == entry_problem_1.get())
            entry_problem_4 = create_entry(frame_problem, 4, 1, StringListEntry, width=10, valid_check=lambda x: x == '' or len(x) == entry_problem_2.get())
            entry_problem_5 = create_entry(frame_problem, 5, 1, FloatListEntry, width=10, valid_check=lambda x: x == '' or len(x) == entry_problem_2.get())

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
                            'var_name': entry_problem_3.get(),
                            'obj_name': entry_problem_4.get(),
                            'ref_point': entry_problem_5.get(),
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

    def _init_storage_widgets(self):
        '''
        GUI data storage related widgets initialization
        Layout:
            Entry: display saving path
            Button "Browse": change saving path by opening file browser
        '''
        # storage overall frame
        frame_storage = tk.LabelFrame(master=self.root, bg='white', text='Storage', font=('courier', 12, 'normal'))
        frame_storage.grid(row=1, column=0, padx=10, pady=10, sticky='NSEW')

        # description label
        label_path = tk.Label(master=frame_storage, bg='white', text='File location for data saving:')
        label_path.grid(row=0, column=0, padx=10, pady=10, sticky='W')

        # path display entry
        def sv_path_callback(sv):
            self.data_path = sv.get()
        sv_path = tk.StringVar()
        sv_path.trace('w', lambda name, index, mode, sv=sv_path: sv_path_callback(sv))
        entry_path = tk.Entry(master=frame_storage, bg='white', textvariable=sv_path, width=36)
        entry_path.grid(row=1, column=0, padx=10, sticky='EW')
        entry_path.insert(tk.END, self.data_path)

        # path change command
        button_path = tk.Button(master=frame_storage, text='Browse')
        button_path.grid(row=2, column=0, ipadx=30, padx=10, pady=10)

        def gui_change_saving_path():
            '''
            GUI change data saving path
            '''
            dirname = tk.filedialog.askdirectory(parent=self.root)
            if not isinstance(dirname, str) or dirname == '': return

            entry_path.delete(0, tk.END)
            self.data_path = os.path.join(dirname, 'data.' + self.data_format)
            entry_path.insert(tk.END, self.data_path)

        # link to commands
        button_path.configure(command=gui_change_saving_path)

    def _init_control_widgets(self):
        '''
        GUI control widgets initialization
        Layout:
            Button "Optimize": run an algorithm optimization
            Button "Stop" stop all algorithm optimizations
        '''
        # control overall frame
        frame_control = tk.LabelFrame(master=self.root, bg='white', text='Control', font=('courier', 12, 'normal'))
        frame_control.grid(row=2, column=0, padx=10, pady=10, sticky='NSEW')

        # optimization command
        self.button_optimize = tk.Button(master=frame_control, text="Optimize", state=tk.DISABLED)
        self.button_optimize.grid(row=0, column=0, ipadx=40, padx=5, pady=10, sticky='NS')

        # stop optimization command
        self.button_stop = tk.Button(master=frame_control, text='Stop', state=tk.DISABLED)
        self.button_stop.grid(row=0, column=1, ipadx=20, padx=5, pady=10, sticky='NS')

        def gui_optimize():
            '''
            GUI execute optimization
            '''
            self.button_load.configure(state=tk.DISABLED)
            self.button_customize.configure(state=tk.DISABLED)
            self.button_stop.configure(state=tk.NORMAL)
            worker = Process(target=self.optimize_command, args=(self.process_id, self.config, self.data_path, self.problem))
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

        # link to commands
        self.button_optimize.configure(command=gui_optimize)
        self.button_stop.configure(command=gui_stop_optimize)

    def _init_log_widgets(self):
        '''
        GUI log widgets initialization
        Layout:
            ScrolledText: display log info
            Button "clear": clear log info
        '''
        # log overall frame
        frame_log = tk.LabelFrame(master=self.root, bg='white', text='Log', font=('courier', 12, 'normal'))
        frame_log.grid(row=0, rowspan=3, column=2, padx=10, pady=10, sticky='NSEW')

        # log display
        self.scrtext_log = scrolledtext.ScrolledText(master=frame_log, width=10, height=10, state=tk.DISABLED)
        self.scrtext_log.grid(row=0, column=0, ipadx=80, ipady=200, padx=5, pady=10, sticky='NSEW')

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

    def _set_config(self, config):
        '''
        GUI setting configurations
        '''
        # check if data_path file exists
        if os.path.exists(self.data_path):
            tk.messagebox.showinfo('Error', f'File {self.data_path} exists, please change another file name')
            return

        # initialize
        try:
            self.problem, true_pfront = self.init_command(config, self.data_path)
        except:
            tk.messagebox.showinfo('Error', 'Invalid values in configuration')
            return

        self.config = config

        # update plot
        f1_name, f2_name = self.config['problem']['obj_name']
        self.ax1.set_xlabel(f1_name)
        self.ax1.set_ylabel(f2_name)
        self._init_draw(true_pfront)

        # activate optimization button
        self.button_optimize.configure(state=tk.NORMAL)
        self.scrtext_config.configure(state=tk.NORMAL)
        self.scrtext_config.insert(tk.INSERT, yaml.dump(self.config, default_flow_style=False, sort_keys=False))
        self.scrtext_config.configure(state=tk.DISABLED)

        # trigger periodic refresh
        self.root.after(self.refresh_rate, self._refresh)

    def _init_draw(self, true_pfront):
        '''
        First draw of performance space, hypervolume curve and model prediction error
        '''
        # load from database
        Y, Y_pareto, hv_value, _ = self.load_command(self.config, self.data_path)

        # update status
        self.n_init_sample = len(Y)
        self.n_curr_sample = self.n_init_sample

        # plot performance space
        if true_pfront is not None:
            self.ax1.scatter(*true_pfront.T, color='gray', s=5, label='True Pareto front') # plot true pareto front
        self.scatter_y = self.ax1.scatter(*Y.T, color='blue', s=10, label='Evaluated points')
        self.scatter_y_pareto = self.ax1.scatter(*Y_pareto.T, color='red', s=10, label='Approximated Pareto front')
        self.ax1.legend(loc='upper right')

        # plot hypervolume curve
        self.line_hv = self.ax2.plot(list(range(self.n_init_sample)), hv_value)[0]
        self.ax2.set_title('Hypervolume: %.2f' % hv_value[-1])

        # plot prediction error curve
        self.line_error = self.ax3.plot([], [])[0]

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
        self.root.after(self.refresh_rate, self._refresh)

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

    def _redraw(self):
        '''
        Redraw performance space, hypervolume curve and model prediction error
        '''
        # load from database
        Y, Y_pareto, hv_value, pred_error = self.load_command(self.config, self.data_path)

        # check if needs redraw
        if len(Y) == self.n_curr_sample: return
        self.n_curr_sample = len(Y)

        # replot performance space
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
        self.root.quit()
        self.root.destroy()