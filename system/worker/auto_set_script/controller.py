import tkinter as tk
from tkinter import messagebox
from problem.utils import import_obj_func, import_constr_func
from .view import AutoSetScriptView


class AutoSetScriptController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = AutoSetScriptView(self.root_view)

        self.view.widget['browse_obj_func'].configure(command=self.set_objective_script)
        self.view.widget['disp_obj_func'].config(
            valid_check=self.eval_script_valid_check, 
            error_msg="performance evaluation script doesn't exist or file format is invalid",
        )

        self.view.widget['disp_obj_func'].config(required=True)

        p_path = self.root_controller.load_eval_script()
        if p_path is not None:
            self.view.widget['disp_obj_func'].set(p_path)

        self.view.widget['save'].config(command=self.save_script)
        self.view.widget['cancel'].config(command=self.view.window.destroy)

    def eval_script_valid_check(self, path):
        '''
        '''
        if path is None:
            return False

        problem_info = self.root_controller.problem_info
        n_var, n_obj = problem_info['n_var'], problem_info['n_obj']

        try:
            import_obj_func(path, n_var, n_obj)
        except:
            return False
        return True

    def set_objective_script(self):
        '''
        Set path of performance evaluation script
        '''
        filename = tk.filedialog.askopenfilename(parent=self.view.window)
        if not isinstance(filename, str) or filename == '': return
        self.view.widget['disp_obj_func'].set(filename)

    def save_script(self):
        '''
        '''
        try:
            path = self.view.widget['disp_obj_func'].get()
        except:
            error_msg = self.view.widget['disp_obj_func'].get_error_msg()
            messagebox.showinfo('Error', error_msg, parent=self.view.window)

        self.root_controller.set_eval_script(script_path=path)
        
        messagebox.showinfo('Success', 'Evaluation script set', parent=self.view.window)
        self.view.window.destroy()