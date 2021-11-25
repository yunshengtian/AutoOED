import tkinter as tk
from tkinter import messagebox

from autooed.problem.config import complete_config
from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.utils.layout import grid_configure, center
from autooed.system.gui.widgets.listbox import Listbox
from autooed.system.gui.widgets.excel import Excel


class UpdateProblemView:
    
    def __init__(self, root_view):
        self.root_view = root_view
        self.master_window = self.root_view.window
        self.window = create_widget('toplevel', master=self.master_window, title='Create Problem')
        grid_configure(self.window, 0, 0)

        self.frame = {}

        for config_type, config_text in zip(
            ['general', 'design_mixed', 'design_unified', 'performance', 'constraint'],
            ['General Config', 'Design Config', 'Design Config', 'Performance Config', 'Constraint Config']):
            self.frame[config_type] = create_widget('labeled_frame', master=self.window, row=0, column=0, text=config_text, sticky='NSEW')
            self.frame[config_type].grid_remove()
            grid_configure(self.frame[config_type], 0, 0)

        self.curr_frame = 0
        self.max_frame = len(self.frame)

        self.in_creating_var = False
        self.var_cfg = {}

        self.widget = {
            'general': {},
            'design_mixed': {},
            'design_unified': {},
            'performance': {},
            'constraint': {},
        }

        frame_control = create_widget('frame', master=self.window, row=1, column=0, sticky='WE', padx=0, pady=0)
        grid_configure(frame_control, 0, 0)
        self.widget['cancel'] = create_widget('button', master=frame_control, row=0, column=0, text='Cancel', sticky='W')
        self.widget['back'] = create_widget('button', master=frame_control, row=0, column=1, text='Back', sticky='E')
        self.widget['next'] = create_widget('button', master=frame_control, row=0, column=2, text='Next', sticky='E')
        self.widget['finish'] = create_widget('button', master=frame_control, row=0, column=2, text='Finish', sticky='E')

        center(self.window, self.master_window)

    def _try_get_val(self, widget, name):
        '''
        '''
        try:
            val = widget.get()
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.window)
            return None, False
        return val, True

    def create_general_widget(self):
        '''
        '''
        self.widget['general']['name'] = create_widget('labeled_entry', master=self.frame['general'], row=0, column=0, text='Problem name', 
            class_type='string', width=10, required=True, valid_check=lambda x: not x.startswith('"'), error_msg='problem name cannot start with "')
        self.widget['general']['type'] = create_widget('labeled_combobox', master=self.frame['general'], row=1, column=0, text='Problem type', 
            values=['continuous', 'integer', 'binary', 'categorical', 'mixed'], required=True)

    def load_general_widget_values(self, config):
        '''
        '''
        self.widget['general']['name'].set(config['name'])
        self.widget['general']['type'].set(config['type'])

    def create_mixed_design_widget(self):
        '''
        '''
        frame_list = create_widget('labeled_frame', master=self.frame['design_mixed'], row=0, column=0, text='Variable list')
        frame_list_display = create_widget('frame', master=frame_list, row=0, column=0, sticky='N')
        frame_list_action = create_widget('frame', master=frame_list, row=1, column=0, padx=0, pady=0, sticky=None)
        frame_config = create_widget('labeled_frame', master=self.frame['design_mixed'], row=0, column=1, text='Variable Config')
        frame_config_display = create_widget('frame', master=frame_config, row=0, column=0, padx=0, pady=0, sticky='N')
        frame_config_action = create_widget('frame', master=frame_config, row=1, column=0, padx=0, pady=0, sticky=None)
        grid_configure(frame_list, 0, 0)
        grid_configure(frame_config, 0, 0)

        self.widget['design_mixed']['list'] = Listbox(master=frame_list_display)
        self.widget['design_mixed']['list'].grid()
        self.widget['design_mixed']['create'] = create_widget('button', master=frame_list_action, row=0, column=0, text='Create')
        self.widget['design_mixed']['delete'] = create_widget('button', master=frame_list_action, row=0, column=1, text='Delete')

        self.widget['design_mixed']['name'] = create_widget('labeled_entry', master=frame_config_display, row=0, column=0, text='Variable name',
            class_type='string', required=True)
        self.widget['design_mixed']['type'] = create_widget('labeled_combobox', master=frame_config_display, row=1, column=0, text='Variable type', 
            values=['continuous', 'integer', 'binary', 'categorical'], required=True)

        frame_config_display_type = {}
        for key in ['continuous', 'integer', 'categorical']:
            frame_config_display_type[key] = create_widget('frame', master=frame_config_display, row=2, column=0, padx=0, pady=0, sticky=None)
            frame_config_display_type[key].grid_remove()

        self.widget['design_mixed']['lb_float'] = create_widget('labeled_entry', master=frame_config_display_type['continuous'], row=0, column=0, text='Lower bound',
            class_type='float', required=True)
        self.widget['design_mixed']['ub_float'] = create_widget('labeled_entry', master=frame_config_display_type['continuous'], row=1, column=0, text='Upper bound',
            class_type='float', required=True)
        self.widget['design_mixed']['lb_int'] = create_widget('labeled_entry', master=frame_config_display_type['integer'], row=0, column=0, text='Lower bound',
            class_type='int', required=True)
        self.widget['design_mixed']['ub_int'] = create_widget('labeled_entry', master=frame_config_display_type['integer'], row=1, column=0, text='Upper bound',
            class_type='int', required=True)
        self.widget['design_mixed']['choices'] = create_widget('labeled_entry', master=frame_config_display_type['categorical'], row=0, column=0, text='Choices',
            class_type='stringlist', required=True)

        def _clear_type_frame(var_type):
            '''
            '''
            if var_type == 'continuous':
                self.widget['design_mixed']['lb_float'].set(None)
                self.widget['design_mixed']['ub_float'].set(None)
            elif var_type == 'integer':
                self.widget['design_mixed']['lb_int'].set(None)
                self.widget['design_mixed']['ub_int'].set(None)
            elif var_type == 'categorical':
                self.widget['design_mixed']['choices'].set(None)

        def _enable_config_type_frame(var_type):
            '''
            '''
            for key in frame_config_display_type.keys():
                if key == var_type:
                    frame_config_display_type[key].grid()
                else:
                    frame_config_display_type[key].grid_remove()
                _clear_type_frame(key)

        def _disable_config_type_frame():
            '''
            '''
            for key in frame_config_display_type.keys():
                frame_config_display_type[key].grid_remove()
                _clear_type_frame(key)

        def _select_var_type(event):
            '''
            '''
            var_type = event.widget.get()
            _enable_config_type_frame(var_type)

        self.widget['design_mixed']['type'].widget.bind('<<ComboboxSelected>>', _select_var_type)

        def _enable_config_widgets():
            '''
            '''
            for key in ['save', 'cancel', 'name', 'type']:
                self.widget['design_mixed'][key].enable()
            for key in ['name', 'type']:
                self.widget['design_mixed'][key].set(None)

            _disable_config_type_frame()

        def _disable_config_widgets():
            '''
            '''
            for key in ['name', 'type']:
                self.widget['design_mixed'][key].set(None)
            for key in ['save', 'cancel', 'name', 'type']:
                self.widget['design_mixed'][key].disable()
            
            _disable_config_type_frame()

        def _load_widget_values(var_name, config):
            '''
            '''
            self.widget['design_mixed']['name'].set(var_name)
            self.widget['design_mixed']['type'].set(config['type'])
            self.widget['design_mixed']['type'].select()
            if config['type'] == 'continuous':
                self.widget['design_mixed']['lb_float'].set(config['lb'])
                self.widget['design_mixed']['ub_float'].set(config['ub'])
            elif config['type'] == 'integer':
                self.widget['design_mixed']['lb_int'].set(config['lb'])
                self.widget['design_mixed']['ub_int'].set(config['ub'])
            elif config['type'] == 'binary':
                pass
            elif config['type'] == 'categorical':
                self.widget['design_mixed']['choices'].set(config['choices'])
            else:
                raise Exception(f'invalid variable type {config["type"]}')

        def _create_var():
            '''
            '''
            self.in_creating_var = True
            
            self.widget['design_mixed']['list'].insert(tk.END, '')
            self.widget['design_mixed']['list'].select_clear(0, tk.END)
            self.widget['design_mixed']['list'].select_set(tk.END)

            _enable_config_widgets()
            self.widget['design_mixed']['create'].disable()
            self.widget['design_mixed']['delete'].disable()

        def _exit_creating_var():
            '''
            '''
            self.in_creating_var = False

            self.widget['design_mixed']['create'].enable()
            self.widget['design_mixed']['list'].delete(tk.END)

        def _select_var(event):
            '''
            '''
            try:
                index = int(event.widget.curselection()[0])
            except:
                return
            var_name = event.widget.get(index)
            if var_name == '':
                return
            elif self.in_creating_var:
                _exit_creating_var()

            _enable_config_widgets()
            _load_widget_values(var_name, self.var_cfg[var_name])

            self.widget['design_mixed']['delete'].enable()

        def _delete_var():
            '''
            '''
            index = int(self.widget['design_mixed']['list'].curselection()[0])
            var_name = self.widget['design_mixed']['list'].get(index)
            if_delete = tk.messagebox.askquestion('Delete Variable', f'Are you sure to delete variable "{var_name}"?', parent=self.window)
            if if_delete == 'yes':
                self.widget['design_mixed']['list'].delete(index)
                listbox_size = self.widget['design_mixed']['list'].size()
                if listbox_size == 0:
                    self.widget['design_mixed']['delete'].disable()
                    _disable_config_widgets()
                else:
                    self.widget['design_mixed']['list'].select_set(min(index, listbox_size - 1))
                    self.widget['design_mixed']['list'].select_event()
                self.var_cfg.pop(var_name)
            else:
                return

        def _save_var():
            '''
            '''
            var_name, success = self._try_get_val(self.widget['design_mixed']['name'], 'Variable name')
            if not success: return

            var_type, success = self._try_get_val(self.widget['design_mixed']['type'], 'Variable type')
            if not success: return
            
            if var_type == 'continuous':
                var_lb, success = self._try_get_val(self.widget['design_mixed']['lb_float'], 'Lower bound')
                if not success: return

                var_ub, success = self._try_get_val(self.widget['design_mixed']['ub_float'], 'Upper bound')
                if not success: return

                if var_lb >= var_ub:
                    tk.messagebox.showinfo('Error', 'Lower bound is no less than upper bound', parent=self.window)
                    return

                self.var_cfg[var_name] = {'type': var_type, 'lb': float(var_lb), 'ub': float(var_ub)}

            elif var_type == 'integer':
                var_lb, success = self._try_get_val(self.widget['design_mixed']['lb_int'], 'Lower bound')
                if not success: return

                var_ub, success = self._try_get_val(self.widget['design_mixed']['ub_int'], 'Upper bound')
                if not success: return

                if var_lb >= var_ub:
                    tk.messagebox.showinfo('Error', 'Lower bound is no less than upper bound', parent=self.window)
                    return

                self.var_cfg[var_name] = {'type': var_type, 'lb': int(var_lb), 'ub': int(var_ub)}

            elif var_type == 'binary':
                self.var_cfg[var_name] = {'type': var_type}
            
            elif var_type == 'categorical':
                var_choices, success = self._try_get_val(self.widget['design_mixed']['choices'], 'Choices')
                if not success: return

                self.var_cfg[var_name] = {'type': var_type, 'choices': list(var_choices)}

            else:
                raise Exception(f'invalid variable type {var_type}')

            tk.messagebox.showinfo('Success', f'Variable {var_name} saved', parent=self.window)

            if self.in_creating_var:
                _exit_creating_var()
            
            self.widget['design_mixed']['list'].reload()
            self.widget['design_mixed']['list'].select(var_name)

        def _cancel_var():
            '''
            '''
            if self.in_creating_var:
                _exit_creating_var()
                _disable_config_widgets()
            self.widget['design_mixed']['list'].select_event()

        def _reload_var():
            '''
            '''
            var_list = list(self.var_cfg.keys())
            if len(var_list) == 0:
                self.widget['design_mixed']['delete'].disable()
            else:
                self.widget['design_mixed']['delete'].enable()
            return var_list

        self.widget['design_mixed']['list'].bind_cmd(reload_cmd=_reload_var, select_cmd=_select_var)
        self.widget['design_mixed']['list'].reload()

        self.widget['design_mixed']['create'].configure(command=_create_var)
        self.widget['design_mixed']['delete'].configure(command=_delete_var)
        
        self.widget['design_mixed']['save'] = create_widget('button', master=frame_config_action, row=0, column=0, text='Save')
        self.widget['design_mixed']['cancel'] = create_widget('button', master=frame_config_action, row=0, column=1, text='Cancel')
        self.widget['design_mixed']['save'].configure(command=_save_var)
        self.widget['design_mixed']['cancel'].configure(command=_cancel_var)

        _disable_config_widgets()

    def load_mixed_design_widget_values(self, config):
        '''
        '''
        self.var_cfg = config['var'].copy()
        self.widget['design_mixed']['list'].reload()

    def create_unified_design_widget(self, problem_type):
        '''
        '''
        frame_n_var = create_widget('frame', master=self.frame['design_unified'], row=0, column=0, padx=0, pady=0, sticky=None)
        frame_excel = create_widget('frame', master=self.frame['design_unified'], row=1, column=0)

        self.widget['design_unified']['disp_n_var'] = create_widget('labeled_spinbox', master=frame_n_var, row=0, column=0, text='Number of variables',
            from_=1, to=int(1e10), required=True)
        self.widget['design_unified']['set_n_var'] = create_widget('button', master=frame_n_var, row=0, column=1, text='Set')

        def _set_n_var():
            '''
            '''
            n_var, success = self._try_get_val(self.widget['design_unified']['disp_n_var'], 'Number of variables')
            if not success: return

            if 'excel' in self.widget['design_unified']:
                self.widget['design_unified']['excel'].grid_remove()

            valid_naming_cond = lambda x: not (x.startswith('_') or x.startswith('"'))

            if problem_type == 'continuous':
                self.widget['design_unified']['excel'] = Excel(master=frame_excel, rows=n_var, columns=3, width=15,
                    title=['Name', 'Lower bound', 'Upper bound'], dtype=[str, float, float], required=[True] * 3,
                    valid_check=[valid_naming_cond, None, None])

            elif problem_type == 'integer':
                self.widget['design_unified']['excel'] = Excel(master=frame_excel, rows=n_var, columns=3, width=15,
                    title=['Name', 'Lower bound', 'Upper bound'], dtype=[str, int, int], required=[True] * 3,
                    valid_check=[valid_naming_cond, None, None])

            elif problem_type == 'binary':
                self.widget['design_unified']['excel'] = Excel(master=frame_excel, rows=n_var, columns=1, width=15,
                    title=['Name'], dtype=[str], required=[True],
                    valid_check=[valid_naming_cond])

            elif problem_type == 'categorical':
                self.widget['design_unified']['excel'] = Excel(master=frame_excel, rows=n_var, columns=2, width=15,
                    title=['Name', 'Choices'], dtype=[str, str], required=[True] * 2,
                    valid_check=[valid_naming_cond, None])

            else:
                raise Exception(f'invalid problem type {problem_type}')

            self.widget['design_unified']['excel'].grid(row=1, column=0)
            self.widget['design_unified']['excel'].set_column(0, [f'x{i}' for i in range(1, n_var + 1)])
            self.widget['next'].enable()

        self.widget['design_unified']['set_n_var'].configure(command=_set_n_var)
        self.widget['next'].disable()

    def load_unified_design_widget_values(self, config):
        '''
        '''
        self.widget['design_unified']['disp_n_var'].set(config['n_var'])
        self.widget['design_unified']['set_n_var'].invoke()

        problem_type = config['type']
        if problem_type == 'continuous' or problem_type == 'integer':
            self.widget['design_unified']['excel'].set_column(0, config['var_name'])
            self.widget['design_unified']['excel'].set_column(1, config['var_lb'])
            self.widget['design_unified']['excel'].set_column(2, config['var_ub'])

        elif problem_type == 'binary':
            self.widget['design_unified']['excel'].set_column(0, config['var_name'])

        elif problem_type == 'categorical':
            self.widget['design_unified']['excel'].set_column(0, config['var_name'])
            var_choices = []
            for var_info in config['var'].values():
                var_choices.append(','.join(var_info['choices']))
            self.widget['design_unified']['excel'].set_column(1, var_choices)

        else:
            raise Exception(f'invalid problem type {problem_type}')

    def create_performance_widget(self):
        '''
        '''
        frame_n_obj = create_widget('frame', master=self.frame['performance'], row=0, column=0)
        frame_excel = create_widget('frame', master=self.frame['performance'], row=1, column=0)
        frame_obj_func = create_widget('frame', master=self.frame['performance'], row=2, column=0)

        self.widget['performance']['disp_n_obj'] = create_widget('labeled_spinbox', master=frame_n_obj, row=0, column=0, text='Number of objectives',
            from_=1, to=int(1e10), required=True)
        self.widget['performance']['set_n_obj'] = create_widget('button', master=frame_n_obj, row=0, column=1, text='Set')
        self.widget['performance']['browse_obj_func'], self.widget['performance']['disp_obj_func'] = create_widget('labeled_button_entry',
            master=frame_obj_func, row=0, column=0, label_text='Path to objective function', button_text='Browse', width=30)

        def _set_n_obj():
            '''
            '''
            n_obj, success = self._try_get_val(self.widget['performance']['disp_n_obj'], 'Number of objectives')
            if not success: return

            if 'excel' in self.widget['performance']:
                self.widget['performance']['excel'].grid_remove()

            self.widget['performance']['excel'] = Excel(master=frame_excel, rows=n_obj, columns=2, width=15,
                title=['Name', 'Type'], dtype=[str, str], required=[True, True], 
                valid_check=[lambda x: not (x.startswith('_') or x.startswith('"')), lambda x: x in ['min', 'max']])
            self.widget['performance']['excel'].grid(row=0, column=0)
            self.widget['performance']['excel'].set_column(0, [f'f{i}' for i in range(1, n_obj + 1)])
            self.widget['performance']['excel'].set_column(1, ['min'] * n_obj)
            self.widget['next'].enable()

        def _set_obj_func():
            '''
            '''
            filename = tk.filedialog.askopenfilename(parent=self.window)
            if not isinstance(filename, str) or filename == '': return
            self.widget['performance']['disp_obj_func'].set(filename)
            self.widget['performance']['disp_obj_func'].widget.xview_moveto(1)

        self.widget['performance']['set_n_obj'].configure(command=_set_n_obj)
        self.widget['performance']['browse_obj_func'].configure(command=_set_obj_func)
        self.widget['next'].disable()

    def load_performance_widget_values(self, config):
        '''
        '''
        self.widget['performance']['disp_n_obj'].set(config['n_obj'])
        self.widget['performance']['set_n_obj'].invoke()

        self.widget['performance']['excel'].set_column(0, config['obj_name'])
        self.widget['performance']['excel'].set_column(1, config['obj_type'])

        self.widget['performance']['disp_obj_func'].set(config['obj_func'])

    def create_constraint_widget(self):
        '''
        '''
        self.widget['constraint']['n_constr'] = create_widget('labeled_spinbox', master=self.frame['constraint'], row=0, column=0, text='Number of constraints',
            from_=0, to=int(1e10))
        self.widget['constraint']['browse_constr_func'], self.widget['constraint']['disp_constr_func'] = create_widget('labeled_button_entry',
            master=self.frame['constraint'], row=1, column=0, label_text='Path to constraint function', button_text='Browse', width=30)

        def _set_constr_func():
            '''
            '''
            filename = tk.filedialog.askopenfilename(parent=self.window)
            if not isinstance(filename, str) or filename == '': return
            self.widget['constraint']['disp_constr_func'].set(filename)
            self.widget['constraint']['disp_constr_func'].widget.xview_moveto(1)

        self.widget['constraint']['browse_constr_func'].configure(command=_set_constr_func)

    def load_constraint_widget_values(self, config):
        '''
        '''
        self.widget['constraint']['n_constr'].set(config['n_constr'])
        self.widget['constraint']['disp_constr_func'].set(config['constr_func'])


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
            except Exception as e:
                messagebox.showinfo('Error', e, parent=self.view.window)
                return
            try:
                self.config['type'] = self.view.widget['general']['type'].get()
            except Exception as e:
                messagebox.showinfo('Error', e, parent=self.view.window)
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

        obj_func, success = self.view._try_get_val(self.view.widget['performance']['disp_obj_func'], 'Path to objective function')
        if not success: return

        self.config['n_obj'] = n_obj
        self.config['obj_name'] = obj_name
        self.config['obj_type'] = obj_type
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

        if n_constr > 0 and constr_func is None:
            messagebox.showinfo('Error', 'Constraint function must be provided', parent=self.view.window)
            return

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