import numpy as np
import tkinter as tk

from autooed.problem.config import is_iterable
from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.excel import Excel
from autooed.system.gui.widgets.utils.layout import center


def get_design_dtype(problem_cfg):
    '''
    Get data types of design values.
    '''
    var_type_map = {
        'continuous': float,
        'integer': int,
        'binary': int,
        'categorical': str,
        'mixed': object,
    }

    n_var, var_type = problem_cfg['n_var'], problem_cfg['type']
    if var_type == 'mixed':
        dtype = []
        for var_info in problem_cfg['var'].values():
            dtype.append(var_type_map[var_info['type']])
    else:
        dtype = [var_type_map[var_type]] * n_var
    return dtype


def check_ith_design_valid(design_i, i, problem_cfg):
    '''
    Check if the ith given design is valid in the design space.
    '''
    # assume problem_cfg is checked
    problem_type = problem_cfg['type']

    if problem_type == 'continuous':
        var_lb, var_ub = problem_cfg['var_lb'], problem_cfg['var_ub']
        return (design_i >= var_lb[i] if is_iterable(var_lb) else design_i >= var_lb) \
            and (design_i <= var_ub[i] if is_iterable(var_ub) else design_i <= var_ub)

    elif problem_type == 'integer':
        var_lb, var_ub = problem_cfg['var_lb'], problem_cfg['var_ub']
        return (design_i >= var_lb[i] if is_iterable(var_lb) else design_i >= var_lb) \
            and (design_i <= var_ub[i] if is_iterable(var_ub) else design_i <= var_ub) \
            and int(design_i) == design_i

    elif problem_type == 'binary':
        return int(design_i) == 0 or int(design_i) == 1

    elif problem_type == 'categorical':
        if 'var' in problem_cfg:
            var_info = list(problem_cfg['var'].values())[i]
            return design_i in var_info['choices']
        else:
            return design_i in problem_cfg['var_choices']

    elif problem_type == 'mixed':
        var_info = list(problem_cfg['var'].values())[i]
        var_type = var_info['type']
        if var_type == 'continuous':
            return design_i >= var_info['lb'] and design_i <= var_info['ub']
        elif var_type == 'integer':
            return design_i >= var_info['lb'] and design_i <= var_info['ub'] and int(design_i) == design_i
        elif var_type == 'binary':
            return int(design_i) == 0 or int(design_i) == 1
        elif var_type == 'categorical':
            return design_i in var_info['choices']
        else:
            raise NotImplementedError

    else:
        raise NotImplementedError


class EnterDesignView:

    def __init__(self, root_view, problem_cfg, can_eval):
        self.root_view = root_view
        self.master_window = self.root_view.root
        self.window = create_widget('toplevel', master=self.master_window, title='Enter Design Variables')

        n_var = problem_cfg['n_var']

        self.widget = {}

        frame_n_row = create_widget('frame', master=self.window, row=0, column=0, sticky=None, pady=0)
        self.widget['disp_n_row'] = create_widget('labeled_spinbox',
            master=frame_n_row, row=0, column=0, text='Number of rows', from_=1, to=int(1e10))
        self.widget['set_n_row'] = create_widget('button', master=frame_n_row, row=0, column=1, text='Update')

        self.widget['design_excel'] = Excel(master=self.window, rows=1, columns=n_var, width=10, 
            title=[f'x{i + 1}' for i in range(n_var)], dtype=get_design_dtype(problem_cfg), required=[True] * n_var, required_mark=False,
            valid_check=[lambda x, i=i: check_ith_design_valid(x, i, problem_cfg) for i in range(n_var)])
        self.widget['design_excel'].grid(row=1, column=0)

        if can_eval:
            self.widget['eval_var'] = create_widget('checkbutton', master=self.window, row=2, column=0, text='Automatically evaluate')

        frame_action = create_widget('frame', master=self.window, row=3, column=0, sticky=None, pady=0)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')

        center(self.window, self.master_window)


class EnterDesignController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        problem_cfg = self.root_controller.get_problem_cfg()
        can_eval = self.root_controller.agent.can_eval

        self.view = EnterDesignView(self.root_view, problem_cfg, can_eval)

        self.view.widget['disp_n_row'].set(1)
        self.view.widget['set_n_row'].configure(command=self.update_table)

        self.view.widget['save'].configure(command=self.add_design)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def update_table(self):
        '''
        Update excel table of design variables to be added
        '''
        n_row = self.view.widget['disp_n_row'].get()
        self.view.widget['design_excel'].update_n_row(n_row)

    def add_design(self):
        '''
        Add input design variables, then predict (and evaluate)
        '''
        try:
            X_next = np.atleast_2d(self.view.widget['design_excel'].get_all())
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return

        if 'eval_var' in self.view.widget:
            if_eval = self.view.widget['eval_var'].get() == 1 # TODO: fail when no eval program is linked
        else:
            if_eval = False
        
        self.view.window.destroy()

        agent, scheduler = self.root_controller.agent, self.root_controller.scheduler

        # insert design to database
        rowids = agent.insert_design(X_next)

        # update prediction to database
        if agent.check_initialized():
            scheduler.predict(rowids)

        # call evaluation worker
        if if_eval:
            scheduler.evaluate_manual(rowids)
