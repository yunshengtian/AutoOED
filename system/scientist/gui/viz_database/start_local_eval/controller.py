import tkinter as tk
from .view import StartLocalEvalView


class StartLocalEvalController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = StartLocalEvalView(self.root_view)

        self.view.widget['disp_n_row'].config(
            default=1, 
            valid_check=lambda x: x > 0, 
            error_msg='number of rows must be positive',
        )
        self.view.widget['disp_n_row'].set(1)
        self.view.widget['set_n_row'].configure(command=self.update_table)

        table = self.root_controller.table
        self.view.widget['rowid_excel'].config(
            valid_check=[lambda x: x > 0 and x <= table.n_rows]
        )
        
        self.view.widget['start'].configure(command=self.start_local_worker)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def update_table(self):
        '''
        Update excel table of rowids to be evaluated
        '''
        n_row = self.view.widget['disp_n_row'].get()
        self.view.widget['rowid_excel'].update_n_row(n_row)

    def start_local_worker(self):
        '''
        Start local evaluation workers
        '''
        try:
            rowids = self.view.widget['rowid_excel'].get_column(0)
        except:
            tk.messagebox.showinfo('Error', 'Invalid row numbers', parent=self.view.window)
            return

        n_obj = self.root_controller.get_problem_cfg()['n_obj']
        table = self.root_controller.table
        worker_agent = self.root_controller.worker_agent

        # check for overwriting
        overwrite = False
        for rowid in rowids:
            for i in range(n_obj):
                if table.get(rowid - 1, f'f{i + 1}') != 'N/A':
                    overwrite = True
        if overwrite and tk.messagebox.askquestion('Overwrite Data', 'Are you sure to overwrite evaluated data?', parent=self.view.window) == 'no': return

        self.view.window.destroy()

        for rowid in rowids:
            worker_agent.add_eval_worker(rowid)