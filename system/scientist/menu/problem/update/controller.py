import tkinter as tk
from tkinter import messagebox
from problem.config import complete_config
from .view import UpdateProblemView


class UpdateProblemController:

    def __init__(self, root_controller, curr_config=None):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view
        
        self.curr_config = curr_config.copy() if curr_config is not None else None
        self.config = {}

        self.view = UpdateProblemView(self.root_view)
        self.view.widget['cancel'].configure(command=self.cancel)
        self.view.window.protocol('WM_DELETE_WINDOW', self.cancel)

        self.set_general(forward=True)

    def set_general(self, forward):
        '''
        '''
        # reset button
        self.view.widget['back'].grid_remove()
        if forward: self.view.widget['next'].grid()
        if forward: self.view.widget['finish'].grid_remove()
        self.view.widget['next'].enable()
        self.view.widget['next'].configure(command=lambda: self.set_design(forward=True))

        # reset frame
        if not forward:
            if self.config['type'] == 'mixed':
                self.view.frame['design_mixed'].grid_remove()
            else:
                self.view.frame['design_unified'].grid_remove()
        self.view.frame['general'].grid()

        # create widget
        if forward:
            self.view.create_general_widget()
            if self.curr_config is not None:
                self.view.load_general_widget_values(self.curr_config)

    def set_design(self, forward):
        '''
        '''
        # check previous page
        if forward:
            try:
                self.config['name'] = self.view.widget['general']['name'].get()
            except:
                error_msg = self.view.widget['general']['name'].get_error_msg()
                messagebox.showinfo('Error', f'Invalid problem name: {error_msg}', parent=self.view.window)
                return
            try:
                self.config['type'] = self.view.widget['general']['type'].get()
            except:
                error_msg = self.view.widget['general']['type'].get_error_msg()
                messagebox.showinfo('Error', f'Invalid problem type: {error_msg}', parent=self.view.window)
                return
        
        # reset button
        if forward: self.view.widget['back'].grid()
        if not forward: self.view.widget['next'].enable()
        self.view.widget['back'].configure(command=lambda: self.set_general(forward=False))
        self.view.widget['next'].configure(command=lambda: self.set_performance(forward=True))

        # reset frame
        if forward: self.view.frame['general'].grid_remove()
        if not forward: self.view.frame['performance'].grid_remove()
        if self.config['type'] == 'mixed':
            self.view.frame['design_mixed'].grid()
        else:
            self.view.frame['design_unified'].grid()

        # create widget
        if forward:
            if self.config['type'] == 'mixed':
                self.view.create_mixed_design_widget()
                if self.curr_config is not None:
                    self.view.load_mixed_design_widget_values(self.curr_config)
            else:
                self.view.create_unified_design_widget(self.config['type'])
                if self.curr_config is not None:
                    self.view.load_unified_design_widget_values(self.curr_config)

    def set_performance(self, forward):
        '''
        '''
        # check previous page
        if forward:
            if self.config['type'] == 'mixed':
                if len(self.view.var_cfg) == 0:
                    messagebox.showinfo('Error', 'Please add design variables', parent=self.view.window)
                    return
                self.config['var'] = self.view.var_cfg.copy()
            else:
                n_var, success = self.view._try_get_val(self.view.widget['design_unified']['disp_n_var'], 'Number of variables')
                if not success: return

                if self.config['type'] == 'continuous' or self.config['type'] == 'integer':
                    try:
                        var_name = self.view.widget['design_unified']['excel'].get_column(0)
                    except Exception as e:
                        messagebox.showinfo('Error', e, parent=self.view.window)
                        return

                    try:
                        var_lb = self.view.widget['design_unified']['excel'].get_column(1)
                    except Exception as e:
                        messagebox.showinfo('Error', e, parent=self.view.window)
                        return

                    try:
                        var_ub = self.view.widget['design_unified']['excel'].get_column(2)
                    except Exception as e:
                        messagebox.showinfo('Error', e, parent=self.view.window)
                        return

                    for lb, ub in zip(var_lb, var_ub):
                        if lb >= ub:
                            messagebox.showinfo('Error', 'Lower bound is no less than upper bound', parent=self.view.window)
                            return

                    self.config['n_var'] = n_var
                    self.config['var_name'] = var_name
                    self.config['var_lb'] = var_lb
                    self.config['var_ub'] = var_ub

                elif self.config['type'] == 'binary':
                    try:
                        var_name = self.view.widget['design_unified']['excel'].get_column(0)
                    except Exception as e:
                        messagebox.showinfo('Error', e, parent=self.view.window)
                        return
                    
                    self.config['n_var'] = n_var
                    self.config['var_name'] = var_name

                elif self.config['type'] == 'categorical':
                    try:
                        var_name = self.view.widget['design_unified']['excel'].get_column(0)
                    except Exception as e:
                        messagebox.showinfo('Error', e, parent=self.view.window)
                        return

                    try:
                        var_choices = self.view.widget['design_unified']['excel'].get_column(1)
                    except Exception as e:
                        messagebox.showinfo('Error', e, parent=self.view.window)
                        return

                    self.config['n_var'] = n_var
                    self.config['var'] = {}
                    for name, choices in zip(var_name, var_choices):
                        self.config['var'][name] = {}
                        self.config['var'][name]['type'] = 'categorical'
                        self.config['var'][name]['choices'] = [c.strip() for c in choices.split(',')]

                else:
                    raise Exception(f'invalid problem type {self.config["type"]}')

        # reset button
        if not forward:
            self.view.widget['finish'].grid_remove()
            self.view.widget['next'].grid()
        self.view.widget['back'].configure(command=lambda: self.set_design(forward=False))
        self.view.widget['next'].configure(command=self.set_constraint)

        # reset frame
        if forward:
            if self.config['type'] == 'mixed':
                self.view.frame['design_mixed'].grid_remove()
            else:
                self.view.frame['design_unified'].grid_remove()
        if not forward: self.view.frame['constraint'].grid_remove()
        self.view.frame['performance'].grid()

        # create widget
        if forward:
            self.view.create_performance_widget()
            if self.curr_config is not None:
                self.view.load_performance_widget_values(self.curr_config)

    def set_constraint(self):
        '''
        '''
        # check previous page
        n_obj, success = self.view._try_get_val(self.view.widget['performance']['disp_n_obj'], 'Number of objectives')
        if not success: return
        
        try:
            obj_name = self.view.widget['performance']['excel'].get_column(0)
        except Exception as e:
            messagebox.showinfo('Error', e, parent=self.view.window)
            return

        try:
            obj_type = self.view.widget['performance']['excel'].get_column(1)
        except Exception as e:
            messagebox.showinfo('Error', e, parent=self.view.window)
            return

        try:
            ref_point = self.view.widget['performance']['excel'].get_column(2)
        except Exception as e:
            messagebox.showinfo('Error', e, parent=self.view.window)
            return

        obj_func, success = self.view._try_get_val(self.view.widget['performance']['disp_obj_func'], 'Path to objective function')
        if not success: return

        self.config['n_obj'] = n_obj
        self.config['obj_name'] = obj_name
        self.config['obj_type'] = obj_type
        self.config['ref_point'] = ref_point
        self.config['obj_func'] = obj_func

        # reset button
        self.view.widget['next'].grid_remove()
        self.view.widget['finish'].grid()
        self.view.widget['back'].configure(command=lambda: self.set_performance(forward=False))
        self.view.widget['finish'].configure(command=self.finish)

        # reset frame
        self.view.frame['performance'].grid_remove()
        self.view.frame['constraint'].grid()

        # create widget
        self.view.create_constraint_widget()
        if self.curr_config is not None:
            self.view.load_constraint_widget_values(self.curr_config)

    def finish(self):
        '''
        '''
        # check previous page
        n_constr, success = self.view._try_get_val(self.view.widget['constraint']['n_constr'], 'Number of constraints')
        if not success: return

        constr_func, success = self.view._try_get_val(self.view.widget['constraint']['disp_constr_func'], 'Path to constraint function')
        if not success: return

        self.config['n_constr'] = n_constr
        self.config['constr_func'] = constr_func

        self.config = complete_config(self.config, check=True)

        self.view.window.destroy()
        if self.curr_config is None:
            self.root_controller.receive_created_problem(self.config)
        else:
            self.root_controller.receive_updated_problem(self.config)

    def cancel(self):
        '''
        '''
        self.view.window.destroy()
        if self.curr_config is None:
            self.root_controller.receive_created_problem(None)
        else:
            self.root_controller.receive_updated_problem(None)