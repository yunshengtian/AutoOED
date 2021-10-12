import numpy as np
import tkinter as tk

from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.excel import Excel


class EnterDesignView:

    def __init__(self, root_view, problem_cfg):
        self.root_view = root_view

        n_var, var_type = problem_cfg['n_var'], problem_cfg['type']

        var_type_map = {
            'continuous': float,
            'integer': int,
            'binary': int,
            'categorical': str,
            'mixed': object,
        }

        if var_type == 'mixed':
            dtype = []
            for var_info in problem_cfg['var'].values():
                dtype.append(var_type_map[var_info['type']])
        else:
            dtype = [var_type_map[var_type]] * n_var

        self.window = create_widget('toplevel', master=self.root_view.root, title='Enter Design Variables')

        self.widget = {}

        frame_n_row = create_widget('frame', master=self.window, row=0, column=0, sticky=None, pady=0)
        self.widget['disp_n_row'] = create_widget('labeled_entry',
            master=frame_n_row, row=0, column=0, text='Number of rows', class_type='int')
        self.widget['set_n_row'] = create_widget('button', master=frame_n_row, row=0, column=1, text='Update')

        self.widget['design_excel'] = Excel(master=self.window, rows=1, columns=n_var, width=10, 
            title=[f'x{i + 1}' for i in range(n_var)], dtype=dtype, required=[True] * n_var, required_mark=False)
        self.widget['design_excel'].grid(row=1, column=0)

        self.widget['eval_var'] = create_widget('checkbutton', master=self.window, row=2, column=0, text='Automatically evaluate')

        frame_action = create_widget('frame', master=self.window, row=3, column=0, sticky=None, pady=0)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')


class EnterDesignController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        problem_cfg = self.root_controller.get_problem_cfg()

        self.view = EnterDesignView(self.root_view, problem_cfg)

        self.view.widget['disp_n_row'].config(
            default=1, 
            valid_check=lambda x: x > 0, 
            error_msg='number of rows must be positive',
        )
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
        except:
            tk.messagebox.showinfo('Error', 'Invalid design values', parent=self.view.window)
            return

        if_eval = self.view.widget['eval_var'].get() == 1 # TODO: fail when no eval program is linked
        self.view.window.destroy()

        agent, scheduler = self.root_controller.agent, self.root_controller.scheduler

        # insert design to database
        rowids = agent.insert_design(X_next)

        # update prediction to database
        scheduler.predict(rowids)

        # call evaluation worker
        if if_eval:
            scheduler.evaluate_manual(rowids)