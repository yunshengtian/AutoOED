import numpy as np
import tkinter as tk
from .view import EnterPerformanceView


class EnterPerformanceController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        problem_cfg = self.root_controller.get_problem_cfg()
        n_obj = problem_cfg['n_obj']
        obj_lb, obj_ub = problem_cfg['obj_lb'], problem_cfg['obj_ub']
        if obj_lb is None: obj_lb = np.full(n_obj, -np.inf)
        if obj_ub is None: obj_ub = np.full(n_obj, np.inf)

        self.view = EnterPerformanceView(self.root_view, n_obj)

        self.view.widget['disp_n_row'].config(
            default=1, 
            valid_check=lambda x: x > 0,
            error_msg='number of rows must be positive',
        )
        self.view.widget['disp_n_row'].set(1)
        self.view.widget['set_n_row'].configure(command=self.update_table)

        max_n_rows = self.root_controller.table.n_rows
        self.view.widget['performance_excel'].config(
            valid_check=[lambda x: x > 0 and x <= max_n_rows] + [lambda x: x >= obj_lb[i] and x <= obj_ub[i] for i in range(n_obj)],
        )

        self.view.widget['save'].configure(command=self.add_performance)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def update_table(self):
        '''
        Update excel table of design variables to be added
        '''
        n_row = self.view.widget['disp_n_row'].get()
        self.view.widget['performance_excel'].update_n_row(n_row)

    def add_performance(self):
        '''
        Add performance values
        '''
        try:
            rowids = self.view.widget['performance_excel'].get_column(0)
            if len(np.unique(rowids)) != len(rowids):
                raise Exception('Duplicate row numbers')
        except:
            tk.messagebox.showinfo('Error', 'Invalid row numbers', parent=self.view.window)
            return

        n_obj = self.root_controller.get_problem_cfg()['n_obj']
        table = self.root_controller.table
        data_agent = self.root_controller.data_agent

        # check for overwriting
        overwrite = False
        for rowid in rowids:
            for i in range(n_obj):
                if table.get(rowid - 1, f'f{i + 1}') != 'N/A':
                    overwrite = True
        if overwrite and tk.messagebox.askquestion('Overwrite Data', 'Are you sure to overwrite evaluated data?', parent=self.view.window) == 'no': return

        try:
            Y = self.view.widget['performance_excel'].get_grid(column_start=1)
        except:
            tk.messagebox.showinfo('Error', 'Invalid performance values', parent=self.view.window)
            return
        
        self.view.window.destroy()

        # update database
        data_agent.update_batch(Y, rowids)

        # update table gui
        table.update({'Y': Y}, rowids=rowids)
    