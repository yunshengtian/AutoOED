import tkinter as tk
from problem.common import get_problem_list, get_yaml_problem_list
from problem.config import complete_config

from .view import MenuProblemView
from .model import MenuProblemModel
from .update import UpdateProblemController


class MenuProblemController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.model = MenuProblemModel()
        self.view = None

    def manage_problem(self):
        '''
        '''
        self.view = MenuProblemView(self.root_view)
        
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
        
        self._enable_buttons()

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
        
        self._enable_buttons()

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