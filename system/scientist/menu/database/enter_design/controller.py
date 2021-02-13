import numpy as np
import tkinter as tk
from .view import EnterDesignView


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

        if_eval = self.view.widget['eval_var'].get() == 1 # TODO: fail when no eval script is linked
        self.view.window.destroy()

        data_agent, worker_agent = self.root_controller.data_agent, self.root_controller.worker_agent
        config = self.root_controller.get_config()

        # insert design to database
        rowids = data_agent.insert_design(X_next)

        # update prediction to database
        data_agent.predict(config, rowids)

        # call evaluation worker
        if if_eval:
            for rowid in rowids:
                worker_agent.add_eval_worker(rowid)