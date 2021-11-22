import tkinter as tk
from tkinter import ttk

from autooed.mobo.algorithms import get_algorithm
from autooed.mobo.hyperparams import get_hp_name_by_class, get_hp_class_by_name, get_hp_class_names, get_hp_params
from autooed.system.gui.widgets.utils.layout import grid_configure, center
from autooed.system.gui.widgets.factory import create_widget


class ModuleView:

    def __init__(self, root_view, module):
        self.root_view = root_view.module_frames[module]
        self.module = module

        self.widget = {}
        self.label = {}

        self.frame = create_widget('frame', master=self.root_view, row=0, column=0)
        grid_configure(self.frame, None, 0)
        
        self.widget['name'] = create_widget('labeled_combobox',
            master=self.frame, row=0, column=0, width=20, text='Name', 
            values=get_hp_class_names(module), required=True)

        self._create_param_frame()

        self.curr_name = None
        self.class_map = {
            bool: None,
            int: 'int',
            float: 'float',
            str: 'string',
        }

    def _create_param_frame(self):
        self.frame_param = create_widget('frame', master=self.frame, row=1, column=0, padx=0, pady=0, sticky='NSEW')
        grid_configure(self.frame_param, None, 0)

    def select(self, name):
        if name == self.curr_name: return
        if self.curr_name is not None:
            self.deactivate(self.curr_name)
            self.frame_param.destroy()
            self._create_param_frame()
        self.activate(name)
        self.curr_name = name

    def activate(self, module_class):
        row_num = 0
        for param_name, param_dict in get_hp_params(self.module, module_class).items():
            if param_name == '__name__': continue
            assert 'dtype' in param_dict, f'Data type of parameter {param_name} is not specified'
            class_type = self.class_map[param_dict['dtype']]
            assert 'default' in param_dict, f'Default value of parameter {param_name} is not specified'
            if 'choices' in param_dict:
                self.label[param_name], self.widget[param_name] = create_widget('labeled_combobox',
                    master=self.frame_param, row=row_num, column=0, width=5, text=param_name, 
                    class_type=class_type, values=param_dict['choices'], default=param_dict['default'], return_label=True)
            elif param_dict['dtype'] == bool:
                self.label[param_name], self.widget[param_name] = create_widget('checkbutton',
                    master=self.frame_param, row=row_num, column=0, text=param_name, 
                    default=param_dict['default'], return_label=True)
            elif param_dict['dtype'] in [int, float]:
                valid_check = param_dict['constr'] if 'constr' in param_dict else None
                self.label[param_name], self.widget[param_name] = create_widget('labeled_entry',
                    master=self.frame_param, row=row_num, column=0, text=param_name, 
                    class_type=class_type, default=param_dict['default'], valid_check=valid_check, return_label=True)
            else:
                raise Exception(f'Hyperparameter setting for {param_name} is not supported')
            row_num += 1
        
    def deactivate(self, module_class):
        for param_name in get_hp_params(self.module, module_class).keys():
            if param_name == '__name__': continue
            self.label[param_name].destroy()
            self.label.pop(param_name)
            self.widget[param_name].widget.destroy()
            self.widget.pop(param_name)


class ModuleController:

    def __init__(self, root_controller, module):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.module = module
        
        self.view = ModuleView(self.root_view, module)
        self.view.widget['name'].widget.bind('<<ComboboxSelected>>', self.select)

    def select(self, event):
        '''
        Select module class.
        '''
        name = event.widget.get()
        name = get_hp_class_by_name(self.module, name)
        self.view.select(name)
        self.root_view._update_height(self.module)


class HyperparamView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.master_window = self.root_view.window
        self.window = create_widget('toplevel', master=self.master_window, title='Advanced Settings')

        self.widget = {}
        self.cfg_widget = {}

        # parameter section
        frame_param_algo = create_widget('frame', master=self.window, row=0, column=0)
        self.nb_param = ttk.Notebook(master=frame_param_algo)
        self.nb_param.grid(row=0, column=0, sticky='NSEW')
        self.module_frames = {}
        for module in ['surrogate', 'acquisition', 'solver', 'selection']:
            frame = tk.Frame(master=self.nb_param)
            self.nb_param.add(child=frame, text=module.capitalize())
            grid_configure(frame, None, 0)
            self.module_frames[module] = frame
        self.nb_param.bind("<<NotebookTabChanged>>", self._change_tab)

        # action section
        frame_action = tk.Frame(master=self.window)
        frame_action.grid(row=1, column=0)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')

        center(self.window, self.master_window)

    def _update_height(self, module):
        self.nb_param.update_idletasks()
        self.nb_param.configure(height=self.module_frames[module].winfo_reqheight())

    def _change_tab(self, event):
        event.widget.update_idletasks()
        tab = event.widget.nametowidget(event.widget.select())
        event.widget.configure(height=tab.winfo_reqheight())


class HyperparamController:

    def __init__(self, root_controller, first_time):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.algo_cfg = self.root_controller.algo_cfg

        self.view = HyperparamView(self.root_view)

        self.controllers = {}
        for module in ['surrogate', 'acquisition', 'solver', 'selection']:
            self.controllers[module] = ModuleController(self, module)
            self.view.cfg_widget[module] = self.controllers[module].view.widget

        self.view.widget['save'].configure(command=self.save_algo_config)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)
        
        algo_selected = self.root_controller.algo_selected
        if first_time:
            self.load_default_algo_config(algo_selected) # first time
        elif algo_selected == self.get_config()['algorithm']['name']:
            self.load_existing_algo_config(algo_selected) # non-first time, select same algo
        else:
            self.load_default_algo_config(algo_selected) # non-first time, select different algo

    def get_config(self):
        return self.root_controller.get_config()

    def load_default_algo_config(self, algo_name):
        '''
        Load default algorithm configuration.
        '''
        spec = get_algorithm(algo_name).spec
        for module_type, module_widgets in self.view.cfg_widget.items():
            # set names
            module_class = spec[module_type]
            module_widgets['name'].set(get_hp_name_by_class(module_type, module_class))
            module_widgets['name'].select()
            # set params
            for param_name, widget in module_widgets.items():
                if param_name not in spec[module_type] or param_name == 'name': continue
                widget.set(spec[module_type][param_name])
                if hasattr(widget, 'select'):
                    widget.select()

    def load_existing_algo_config(self, algo_name):
        '''
        Load existing algorithm configuration.
        '''
        default_spec = get_algorithm(algo_name).spec
        for module_type, module_widgets in self.view.cfg_widget.items():
            # set names
            if 'name' in self.algo_cfg[module_type]:
                module_class = self.algo_cfg[module_type]['name']
            else:
                module_class = default_spec[module_type]
            module_widgets['name'].set(get_hp_name_by_class(module_type, module_class))
            module_widgets['name'].select()
            # set params
            for param_name, widget in module_widgets.items():
                if param_name not in self.algo_cfg[module_type] or param_name == 'name': continue
                widget.set(self.algo_cfg[module_type][param_name])
                if hasattr(widget, 'select'):
                    widget.select()

    def save_algo_config(self):
        '''
        Save algorithm configuration.
        '''
        temp_cfg = {}
        for module_type, module_widgets in self.view.cfg_widget.items():
            temp_cfg[module_type] = {}
            for param_name, widget in module_widgets.items():
                try:
                    val = widget.get()
                except Exception as e:
                    tk.messagebox.showinfo('Error', e, parent=self.view.window)
                    return
                if param_name == 'name':
                    temp_cfg[module_type][param_name] = get_hp_class_by_name(module_type, val)
                else:
                    temp_cfg[module_type][param_name] = val

        self.view.window.destroy()

        for key, val in temp_cfg.items():
            self.algo_cfg[key] = val
