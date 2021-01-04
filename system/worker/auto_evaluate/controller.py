import tkinter as tk
from problem.utils import import_performance_eval_func
from .view import AutoEvaluateView


class AutoEvaluateController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = AutoEvaluateView(self.root_view)

        self.view.widget['disp_n_row'].config(
            default=1, 
            valid_check=lambda x: x > 0, 
            error_msg='number of rows must be positive',
        )
        self.view.widget['disp_n_row'].set(1)
        self.view.widget['set_n_row'].configure(command=self.update_table)

        table = self.root_controller.view.widget['db_table']
        self.view.widget['rowid_excel'].config(
            valid_check=[lambda x: x > 0 and x <= table.n_rows]
        )
        
        self.view.widget['start'].configure(command=self.start_evaluate)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def update_table(self):
        '''
        Update excel table of rowids to be evaluated
        '''
        n_row = self.view.widget['disp_n_row'].get()
        self.view.widget['rowid_excel'].update_n_row(n_row)

    def start_evaluate(self):
        '''
        Start evaluation script
        '''
        try:
            rowids = self.view.widget['rowid_excel'].get_column(0)
        except:
            tk.messagebox.showinfo('Error', 'Invalid row numbers', parent=self.view.window)
            return

        # check if locked
        locked_rows = []
        for rowid in rowids:
            locked = self.root_controller.check_entry(rowid)
            if locked:
                locked_rows.append(rowid)
        if len(locked_rows) > 0:
            tk.messagebox.showinfo('Locked', f'Rows {locked_rows} are locked, cannot proceed')
            return

        n_var = self.root_controller.problem_info['n_var']
        n_obj = self.root_controller.problem_info['n_obj']
        table = self.root_controller.view.widget['db_table']

        # check for overwriting
        overwrite = False
        for rowid in rowids:
            for i in range(n_obj):
                if table.get(rowid - 1, f'f{i + 1}') != 'N/A':
                    overwrite = True
        if overwrite and tk.messagebox.askquestion('Overwrite Data', 'Are you sure to overwrite evaluated data?', parent=self.view.window) == 'no': return

        eval_script_path = self.root_controller.load_eval_script()
        try:
            eval_func = import_performance_eval_func(eval_script_path, n_var, n_obj)
        except:
            tk.messagebox.showinfo('Error', f'Failed to load evaluation script at {eval_script_path}', parent=self.view.window)
            self.view.window.destroy()
            return

        self.view.window.destroy()

        self.root_controller.evaluate(eval_func, rowids)