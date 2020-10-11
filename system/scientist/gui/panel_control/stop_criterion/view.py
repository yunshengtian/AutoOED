import tkinter as tk
from system.gui.widgets.factory import create_widget


class StopCriterionView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.window = tk.Toplevel(master=self.root_view.root)
        self.window.title('Stopping Criterion')
        self.window.resizable(False, False)

        self.widget = {
            'var': {},
            'entry': {},
        }

        frame_options = create_widget('frame', master=self.window, row=0, column=0, padx=0, pady=0)
        self.name_options = {'time': 'Time', 'n_sample': 'Number of samples', 'hv_value': 'Hypervolume value', 'hv_conv': 'Hypervolume convergence'}

        frame_time = create_widget('frame', master=frame_options, row=0, column=0)
        self.widget['var']['time'] = tk.IntVar()
        tk.Checkbutton(master=frame_time, variable=self.widget['var']['time'], highlightthickness=0, bd=0).grid(row=0, column=0, sticky='W')
        tk.Label(master=frame_time, text=self.name_options['time'] + ': stop after').grid(row=0, column=1, sticky='W')
        self.widget['entry']['time'] = create_widget('entry', master=frame_time, row=0, column=2, class_type='float', 
            required=True, valid_check=lambda x: x > 0, error_msg='time limit must be positive', pady=0)
        tk.Label(master=frame_time, text='seconds').grid(row=0, column=3, sticky='W')

        frame_n_sample = create_widget('frame', master=frame_options, row=1, column=0)
        self.widget['var']['n_sample'] = tk.IntVar()
        tk.Checkbutton(master=frame_n_sample, variable=self.widget['var']['n_sample'], highlightthickness=0, bd=0).grid(row=0, column=0, sticky='W')
        tk.Label(master=frame_n_sample, text=self.name_options['n_sample'] + ': stop when number of samples reaches').grid(row=0, column=1, sticky='W')
        self.widget['entry']['n_sample'] = create_widget('entry', master=frame_n_sample, row=0, column=2, class_type='int', 
            required=True, valid_check=lambda x: x > 0, error_msg='number of samples must be positive', pady=0)

        frame_hv_value = create_widget('frame', master=frame_options, row=2, column=0)
        self.widget['var']['hv_value'] = tk.IntVar()
        tk.Checkbutton(master=frame_hv_value, variable=self.widget['var']['hv_value'], highlightthickness=0, bd=0).grid(row=0, column=0, sticky='W')
        tk.Label(master=frame_hv_value, text=self.name_options['hv_value'] + ': stop when hypervolume reaches').grid(row=0, column=1, sticky='W')
        self.widget['entry']['hv_value'] = create_widget('entry', master=frame_hv_value, row=0, column=2, class_type='float', 
            required=True, valid_check=lambda x: x > 0, error_msg='hypervolume value must be positive', pady=0)

        frame_hv_conv = create_widget('frame', master=frame_options, row=3, column=0)
        self.widget['var']['hv_conv'] = tk.IntVar()
        tk.Checkbutton(master=frame_hv_conv, variable=self.widget['var']['hv_conv'], highlightthickness=0, bd=0).grid(row=0, column=0, sticky='W')
        tk.Label(master=frame_hv_conv, text=self.name_options['hv_conv'] + ': stop when hypervolume stops to improve over past').grid(row=0, column=1, sticky='W')
        self.widget['entry']['hv_conv'] = create_widget('entry', master=frame_hv_conv, row=0, column=2, class_type='float', 
            required=True, valid_check=lambda x: x > 0 and x < 100, error_msg='percentage must be between 0~100', pady=0)
        tk.Label(master=frame_hv_conv, text='% number of samples').grid(row=0, column=3, sticky='W')

        frame_action = create_widget('frame', master=self.window, row=1, column=0, pady=0, sticky=None)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')