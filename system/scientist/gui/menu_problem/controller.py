import tkinter as tk
from problem.common import get_problem_list, get_yaml_problem_list
from system.scientist.gui.map import config_map
from .model import MenuProblemModel
from .view import MenuProblemView

from .design_space import DesignSpaceController
from .performance_space import PerformanceSpaceController


class MenuProblemController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.problem_cfg = {}

        self.model = MenuProblemModel()
        self.view = None

        self.in_creating_problem = False

    def manage_problem(self):
        self.view = MenuProblemView(self.root_view)

        self.view.widget['problem_list'].bind_cmd(reload_cmd=get_yaml_problem_list, select_cmd=self.select_problem)
        self.view.widget['problem_list'].reload()

        self.view.widget['create'].configure(command=self.create_problem)
        self.view.widget['delete'].configure(command=self.delete_problem)

        self.view.widget['n_var'].config(
            valid_check=lambda x: x > 0, 
            error_msg='number of design variables must be positive',
        )
        self.view.widget['n_obj'].config(
            valid_check=lambda x: x > 1, 
            error_msg='number of objectives must be greater than 1',
        )
        self.view.widget['n_constr'].config(
            default=0, 
            valid_check=lambda x: x >= 0, 
            error_msg='number of constraints must be positive',
        )

        self.view.widget['set_design'].configure(command=self.set_design_space)
        self.view.widget['set_performance'].configure(command=self.set_performance_space)

        self.view.widget['browse_p_eval'].configure(command=self.set_performance_script)
        self.view.widget['disp_p_eval'].config(
            valid_check=self.eval_script_valid_check, 
            error_msg="performance evaluation script doesn't exist or file format is invalid",
        )
        self.view.widget['browse_c_eval'].config(command=self.set_constraint_script)
        self.view.widget['disp_c_eval'].config(
            valid_check=self.eval_script_valid_check, 
            error_msg="constraint evaluation script doesn't exist or file format is invalid",
        )

        self.view.widget['save'].configure(command=self.save_change)
        self.view.widget['cancel'].configure(command=self.cancel_change)
        
        self.view.widget['delete'].disable()
        self.view.disable_config_widgets()

    def set_design_space(self):
        '''
        Set design space parameters
        '''
        # validity check
        try:
            n_var = self.view.widget['n_var'].get()
        except:
            error_msg = self.view.widget['n_var'].get_error_msg()
            error_msg = '' if error_msg is None else ': ' + error_msg
            tk.messagebox.showinfo('Error', 'Invalid value for "' + config_map['problem']['n_var'] + '"' + error_msg, parent=self.view.window)
            return

        DesignSpaceController(self, n_var)

    def set_performance_space(self):
        '''
        Set performance space parameters
        '''
        # validity check
        try:
            n_obj = self.view.widget['n_obj'].get()
        except:
            error_msg = self.view.widget['n_obj'].get_error_msg()
            error_msg = '' if error_msg is None else ': ' + error_msg
            tk.messagebox.showinfo('Error', 'Invalid value for "' + config_map['problem']['n_obj'] + '"' + error_msg, parent=self.view.window)
            return

        PerformanceSpaceController(self, n_obj)

    def eval_script_valid_check(self, path):
        '''
        Check validity of evaluation script located at path
        '''
        if path is None:
            return False
        ftype = path.split('.')[-1]
        return ftype in ['py', 'c', 'cpp']

    def set_performance_script(self):
        '''
        Set path of performance evaluation script
        '''
        filename = tk.filedialog.askopenfilename(parent=self.view.window)
        if not isinstance(filename, str) or filename == '': return
        self.view.widget['disp_p_eval'].set(filename)

    def set_constraint_script(self):
        '''
        Set path of constraint evaluation script
        '''
        filename = tk.filedialog.askopenfilename(parent=self.view.window)
        if not isinstance(filename, str) or filename == '': return
        self.view.widget['disp_c_eval'].set(filename)

    def exit_creating_problem(self):
        '''
        Exit creating problem status
        '''
        self.in_creating_problem = False
        self.view.widget['create'].enable()
        self.view.widget['problem_list'].delete(tk.END)
        self.problem_cfg.clear()

    def save_change(self):
        '''
        Save changes to problem
        '''
        if self.in_creating_problem:
            # try to save changes
            try:
                name = self.view.widget['name'].get()
            except:
                error_msg = self.view.widget['name'].get_error_msg()
                error_msg = '' if error_msg is None else ': ' + error_msg
                tk.messagebox.showinfo('Error', 'Invalid value for "' + config_map['problem']['name'] + '"' + error_msg, parent=self.view.window)
                return

            if name in get_problem_list():
                tk.messagebox.showinfo('Error', f'Problem {name} already exists', parent=self.view.window)
                return
            try:
                self.view.save_widget_values(self.problem_cfg)
            except:
                return
            self.model.save_problem(self.problem_cfg)
            tk.messagebox.showinfo('Success', f'Problem {name} saved', parent=self.view.window)
            
            # reload
            self.exit_creating_problem()
            self.view.widget['problem_list'].reload()
            self.view.widget['problem_list'].select(name)
        else:
            curr_idx = self.view.widget['problem_list'].curselection()[0]
            old_name = self.view.widget['problem_list'].get(curr_idx)
            if_save = tk.messagebox.askquestion('Save Changes', f'Are you sure to save the changes for problem "{old_name}"?', parent=self.view.window)

            if if_save == 'yes':
                # try to save changes
                new_name = self.view.widget['name'].get()
                if old_name != new_name: # problem name changed
                    if new_name in get_problem_list():
                        tk.messagebox.showinfo('Error', f'Problem {new_name} already exists', parent=self.view.window)
                        return
                try:
                    self.view.save_widget_values(self.problem_cfg)
                except:
                    return
                if old_name != new_name:
                    self.model.remove_problem(old_name)
                self.model.save_problem(self.problem_cfg)
                tk.messagebox.showinfo('Success', f'Problem {self.problem_cfg["name"]} saved', parent=self.view.window)

                # reload
                self.view.widget['problem_list'].reload()
                self.view.widget['problem_list'].select(new_name)
            else:
                # cancel changes
                return

    def cancel_change(self):
        '''
        Cancel changes to problem
        '''
        if self.in_creating_problem:
            self.exit_creating_problem()
            self.view.disable_config_widgets()
        self.view.widget['problem_list'].select_event()
        self.problem_cfg.clear()

    def create_problem(self):
        '''
        Create new problem
        '''
        self.in_creating_problem = True
        
        self.view.widget['problem_list'].insert(tk.END, '')
        self.view.widget['problem_list'].select_clear(0, tk.END)
        self.view.widget['problem_list'].select_set(tk.END)

        self.view.enable_config_widgets()
        self.view.widget['create'].disable()
        self.view.widget['delete'].disable()
        self.problem_cfg.clear()

    def delete_problem(self):
        '''
        Delete selected problem
        '''
        index = int(self.view.widget['problem_list'].curselection()[0])
        name = self.view.widget['problem_list'].get(index)
        if_delete = tk.messagebox.askquestion('Delete Problem', f'Are you sure to delete problem "{name}"?', parent=self.view.window)
        if if_delete == 'yes':
            self.view.widget['problem_list'].delete(index)
            listbox_size = self.view.widget['problem_list'].size()
            if listbox_size == 0:
                self.view.widget['delete'].disable()
                self.view.disable_config_widgets()
            else:
                self.view.widget['problem_list'].select_set(min(index, listbox_size - 1))
                self.view.widget['problem_list'].select_event()
            self.model.remove_problem(name)
        else:
            return
        self.problem_cfg.clear()

    def select_problem(self, event):
        '''
        Select problem, load problem config
        '''
        try:
            index = int(event.widget.curselection()[0])
        except:
            return
        name = event.widget.get(index)
        if name == '':
            return
        elif self.in_creating_problem:
            self.exit_creating_problem()

        self.view.enable_config_widgets()
        config = self.model.load_problem(name)
        self.view.load_widget_values(config)

        self.view.widget['delete'].enable()
        self.problem_cfg.clear()
        self.problem_cfg.update(config)