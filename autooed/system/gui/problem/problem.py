import tkinter as tk

from autooed.problem import get_problem_list, get_yaml_problem_list
from autooed.problem import load_yaml_problem, save_yaml_problem, remove_yaml_problem
from autooed.problem.config import complete_config
from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.utils.layout import grid_configure, center
from autooed.system.gui.widgets.listbox import Listbox
from autooed.system.gui.problem.update import UpdateProblemController
from autooed.system.params import PADY


class ProblemModel:

    def load_problem(self, name):
        return load_yaml_problem(name)

    def save_problem(self, problem_cfg):
        return save_yaml_problem(problem_cfg)

    def remove_problem(self, name):
        return remove_yaml_problem(name)


class ProblemView:

    def __init__(self, root_view):
        self.root_view = root_view
        self.master_window = self.root_view.root
        self.window = create_widget('toplevel', master=self.master_window, title='Manage Problem')
        grid_configure(self.window, 0, 0)

        self.widget = {}

        frame_list = create_widget('labeled_frame', master=self.window, row=0, column=0, text='Problem List')
        frame_list_display = create_widget('frame', master=frame_list, row=0, column=0, sticky='NS')
        frame_list_action = create_widget('frame', master=frame_list, row=1, column=0, padx=0, pady=0, sticky=None)
        frame_config = create_widget('labeled_frame', master=self.window, row=0, column=1, text='Problem Info')
        frame_config_display = create_widget('frame', master=frame_config, row=0, column=0, sticky='NS')
        frame_config_action = create_widget('frame', master=frame_config, row=1, column=0, padx=0, pady=0, sticky=None)
        grid_configure(frame_list, 0, 0)
        grid_configure(frame_config, 0, 0)

        self.widget['list'] = Listbox(master=frame_list_display)
        self.widget['list'].grid()
        self.widget['create'] = create_widget('button', master=frame_list_action, row=0, column=0, text='Create')

        self.desc = {
            'name': 'Name',
            'type': 'Variable type',
            'n_var': 'Number of variables',
            'n_obj': 'Number of objectives',
            'n_constr': 'Number of constraints',
            'obj_type': 'Type of objectives',
        }
        self.widget['info'] = {}
        for row, key in enumerate(self.desc.keys()):
            self.widget['info'][key] = create_widget('label', master=frame_config_display, row=row, column=0, text=f'{self.desc[key]}:')

        self.widget['update'] = create_widget('button', master=frame_config_action, row=0, column=0, text='Update')
        self.widget['delete'] = create_widget('button', master=frame_config_action, row=0, column=1, text='Delete')

        self.widget['update'].disable()
        self.widget['delete'].disable()

        center(self.window, self.master_window)

    def set_problem_info(self, config):
        '''
        '''
        for key, widget in self.widget['info'].items():
            if config[key] is not None:
                widget.config(text=f'{self.desc[key]}: {config[key]}')
            else:
                widget.config(text=f'{self.desc[key]}:')

    def clear_problem_info(self):
        '''
        '''
        for key, widget in self.widget['info'].items():
            widget.config(text=f'{self.desc[key]}:')


class ProblemController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.model = ProblemModel()
        self.view = ProblemView(self.root_view)
        
        self.view.widget['list'].bind_cmd(reload_cmd=get_yaml_problem_list, select_cmd=self.select_problem)
        self.view.widget['list'].reload()

        self.view.widget['create'].configure(command=self.create_problem)
        self.view.widget['update'].configure(command=self.update_problem)
        self.view.widget['delete'].configure(command=self.delete_problem)

    def _enable_buttons(self):
        self.view.widget['create'].enable()
        self.view.widget['update'].enable()
        self.view.widget['delete'].enable()

    def _disable_buttons(self):
        self.view.widget['create'].disable()
        self.view.widget['update'].disable()
        self.view.widget['delete'].disable()

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

        config = self.model.load_problem(name)
        config = complete_config(config)
        self.view.set_problem_info(config)

        self.view.widget['update'].enable()
        self.view.widget['delete'].enable()

    def create_problem(self):
        '''
        Create new problem
        '''
        self._disable_buttons()

        UpdateProblemController(self)

    def receive_created_problem(self, config):
        '''
        Receive created problem
        '''
        if config is not None:
            self.model.save_problem(config)

            self.view.widget['list'].insert(tk.END, config['name'])
            self.view.widget['list'].select_set(tk.END)
            self.view.widget['list'].select_event()
        
        selected_problem = self.view.widget['list'].curselection()
        if len(selected_problem) > 0:
            self._enable_buttons()
        else:
            self.view.widget['create'].enable()

    def update_problem(self):
        '''
        '''
        self._disable_buttons()
        
        index = int(self.view.widget['list'].curselection()[0])
        name = self.view.widget['list'].get(index)
        config = self.model.load_problem(name)
        config = complete_config(config)

        UpdateProblemController(self, config)

    def receive_updated_problem(self, config):
        '''
        Receive updated problem
        '''
        if config is not None:
            self.model.save_problem(config)
        
        selected_problem = self.view.widget['list'].curselection()
        if len(selected_problem) > 0:
            self._enable_buttons()
        else:
            self.view.widget['create'].enable()

    def delete_problem(self):
        '''
        '''
        index = int(self.view.widget['list'].curselection()[0])
        name = self.view.widget['list'].get(index)
        if_delete = tk.messagebox.askquestion('Delete Problem', f'Are you sure to delete problem "{name}"?', parent=self.view.window)
        if if_delete == 'yes':
            self.view.widget['list'].delete(index)
            listbox_size = self.view.widget['list'].size()
            if listbox_size == 0:
                self.view.clear_problem_info()
                self.view.widget['update'].disable()
                self.view.widget['delete'].disable()
            else:
                self.view.widget['list'].select_set(min(index, listbox_size - 1))
                self.view.widget['list'].select_event()
            self.model.remove_problem(name)
        else:
            return