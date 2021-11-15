import tkinter as tk

from autooed.system.stop_criterion import get_stop_criterion, get_name
from autooed.system.gui.widgets.factory import create_widget


class StopCriterionView:

    def __init__(self, root_view, n_obj):
        self.root_view = root_view

        self.window = create_widget('toplevel', master=self.root_view.root_view.root, title='Stopping Criterion')

        self.widget = {
            'var': {},
            'entry': {},
        }

        frame_options = create_widget('frame', master=self.window, row=0, column=0, padx=0, pady=0)
        self.name_options = {'time': 'Time', 'n_iter': 'Number of iterations', 'n_sample': 'Number of samples'}
        if n_obj == 1:
            self.name_options.update({'opt': 'Optimum value', 'opt_conv': 'Optimum convergence'})
        else:
            self.name_options.update({'hv': 'Hypervolume value', 'hv_conv': 'Hypervolume convergence'})

        def check(var, entry):
            if var.get() == 1:
                entry.enable()
            else:
                entry.disable()

        frame_time = create_widget('frame', master=frame_options, row=0, column=0)
        self.widget['var']['time'] = tk.IntVar()
        cb_time = tk.Checkbutton(master=frame_time, variable=self.widget['var']['time'], highlightthickness=0, bd=0)
        cb_time.grid(row=0, column=0, sticky='W')
        tk.Label(master=frame_time, text=self.name_options['time'] + ': stop after').grid(row=0, column=1, sticky='W')
        self.widget['entry']['time'] = create_widget('entry', master=frame_time, row=0, column=2, class_type='float', 
            required=True, valid_check=lambda x: x > 0, error_msg='time limit must be positive', pady=0)
        tk.Label(master=frame_time, text='seconds').grid(row=0, column=3, sticky='W')
        cb_time.configure(command=lambda: check(self.widget['var']['time'], self.widget['entry']['time']))

        frame_n_iter = create_widget('frame', master=frame_options, row=1, column=0)
        self.widget['var']['n_iter'] = tk.IntVar()
        cb_n_iter = tk.Checkbutton(master=frame_n_iter, variable=self.widget['var']['n_iter'], highlightthickness=0, bd=0)
        cb_n_iter.grid(row=0, column=0, sticky='W')
        tk.Label(master=frame_n_iter, text=self.name_options['n_iter'] + ': stop after').grid(row=0, column=1, sticky='W')
        self.widget['entry']['n_iter'] = create_widget('entry', master=frame_n_iter, row=0, column=2, class_type='int', 
            required=True, valid_check=lambda x: x > 0, error_msg='number of iterations must be positive', pady=0)
        tk.Label(master=frame_n_iter, text='iterations').grid(row=0, column=3, sticky='W')
        cb_n_iter.configure(command=lambda: check(self.widget['var']['n_iter'], self.widget['entry']['n_iter']))

        frame_n_sample = create_widget('frame', master=frame_options, row=2, column=0)
        self.widget['var']['n_sample'] = tk.IntVar()
        cb_n_sample = tk.Checkbutton(master=frame_n_sample, variable=self.widget['var']['n_sample'], highlightthickness=0, bd=0)
        cb_n_sample.grid(row=0, column=0, sticky='W')
        tk.Label(master=frame_n_sample, text=self.name_options['n_sample'] + ': stop when number of samples reaches').grid(row=0, column=1, sticky='W')
        self.widget['entry']['n_sample'] = create_widget('entry', master=frame_n_sample, row=0, column=2, class_type='int', 
            required=True, valid_check=lambda x: x > 0, error_msg='number of samples must be positive', pady=0)
        cb_n_sample.configure(command=lambda: check(self.widget['var']['n_sample'], self.widget['entry']['n_sample']))

        if n_obj == 1:

            frame_opt = create_widget('frame', master=frame_options, row=3, column=0)
            self.widget['var']['opt'] = tk.IntVar()
            cb_opt = tk.Checkbutton(master=frame_opt, variable=self.widget['var']['opt'], highlightthickness=0, bd=0)
            cb_opt.grid(row=0, column=0, sticky='W')
            tk.Label(master=frame_opt, text=self.name_options['opt'] + ': stop when optimum reaches').grid(row=0, column=1, sticky='W')
            self.widget['entry']['opt'] = create_widget('entry', master=frame_opt, row=0, column=2, class_type='float', 
                required=True, valid_check=lambda x: x > 0, error_msg='optimum value must be positive', pady=0)
            cb_opt.configure(command=lambda: check(self.widget['var']['opt'], self.widget['entry']['opt']))

            frame_opt_conv = create_widget('frame', master=frame_options, row=4, column=0)
            self.widget['var']['opt_conv'] = tk.IntVar()
            cb_opt_conv = tk.Checkbutton(master=frame_opt_conv, variable=self.widget['var']['opt_conv'], highlightthickness=0, bd=0)
            cb_opt_conv.grid(row=0, column=0, sticky='W')
            tk.Label(master=frame_opt_conv, text=self.name_options['opt_conv'] + ': stop when optimum stops to improve over past').grid(row=0, column=1, sticky='W')
            self.widget['entry']['opt_conv'] = create_widget('entry', master=frame_opt_conv, row=0, column=2, class_type='int', 
                required=True, valid_check=lambda x: x > 0, error_msg='number of iterations for determining optimum convergence must be positive', pady=0)
            tk.Label(master=frame_opt_conv, text='iterations').grid(row=0, column=3, sticky='W')
            cb_opt_conv.configure(command=lambda: check(self.widget['var']['opt_conv'], self.widget['entry']['opt_conv']))

        else:

            frame_hv = create_widget('frame', master=frame_options, row=3, column=0)
            self.widget['var']['hv'] = tk.IntVar()
            cb_hv = tk.Checkbutton(master=frame_hv, variable=self.widget['var']['hv'], highlightthickness=0, bd=0)
            cb_hv.grid(row=0, column=0, sticky='W')
            tk.Label(master=frame_hv, text=self.name_options['hv'] + ': stop when hypervolume reaches').grid(row=0, column=1, sticky='W')
            self.widget['entry']['hv'] = create_widget('entry', master=frame_hv, row=0, column=2, class_type='float', 
                required=True, valid_check=lambda x: x > 0, error_msg='hypervolume value must be positive', pady=0)
            cb_hv.configure(command=lambda: check(self.widget['var']['hv'], self.widget['entry']['hv']))

            frame_hv_conv = create_widget('frame', master=frame_options, row=4, column=0)
            self.widget['var']['hv_conv'] = tk.IntVar()
            cb_hv_conv = tk.Checkbutton(master=frame_hv_conv, variable=self.widget['var']['hv_conv'], highlightthickness=0, bd=0)
            cb_hv_conv.grid(row=0, column=0, sticky='W')
            tk.Label(master=frame_hv_conv, text=self.name_options['hv_conv'] + ': stop when hypervolume stops to improve over past').grid(row=0, column=1, sticky='W')
            self.widget['entry']['hv_conv'] = create_widget('entry', master=frame_hv_conv, row=0, column=2, class_type='int', 
                required=True, valid_check=lambda x: x > 0, error_msg='number of iterations for determining hypervolume convergence must be positive', pady=0)
            tk.Label(master=frame_hv_conv, text='iterations').grid(row=0, column=3, sticky='W')
            cb_hv_conv.configure(command=lambda: check(self.widget['var']['hv_conv'], self.widget['entry']['hv_conv']))

        for key in self.name_options:
            self.widget['entry'][key].disable()

        frame_action = create_widget('frame', master=self.window, row=1, column=0, pady=0, sticky=None)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')


class StopCriterionController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.agent = self.root_controller.agent
        self.n_obj = self.agent.problem_cfg['n_obj']
        self.view = StopCriterionView(self.root_view, n_obj)

        self.view.widget['save'].configure(command=self.save_stop_criterion)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

        self.load_stop_criterion()

    def save_stop_criterion(self):
        '''
        Save stopping criterion
        '''
        self.root_controller.stop_criterion.clear()

        for key in self.view.name_options.keys():
            if self.view.widget['var'][key].get() == 1:
                try:
                    value = self.view.widget['entry'][key].get()
                except Exception as e:
                    tk.messagebox.showinfo('Error', e, parent=self.view.window)
                    return
                stop_criterion = get_stop_criterion(key)(self.agent, value)
                self.root_controller.stop_criterion.append(stop_criterion)

        self.view.window.destroy()

    def load_stop_criterion(self):
        '''
        Load stopping criterion
        '''
        for stop_criterion in self.root_controller.stop_criterion:
            if not stop_criterion.check():
                key = get_name(type(stop_criterion))
                self.view.widget['var'][key].set(1)
                self.view.widget['entry'][key].enable()
                self.view.widget['entry'][key].set(stop_criterion.load())
