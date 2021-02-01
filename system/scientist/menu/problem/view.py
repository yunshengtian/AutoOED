import tkinter as tk
from system.gui.widgets.factory import create_widget
from system.gui.utils.grid import grid_configure
from system.gui.widgets.listbox import Listbox
from system.gui.widgets_modular import ProblemInfoWidget


class MenuProblemView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.window = tk.Toplevel(master=self.root_view.root)
        self.window.title('Manage Problem')
        self.window.resizable(False, False)
        grid_configure(self.window, 0, 0)

        self.widget = {}

        frame_list = create_widget('labeled_frame', master=self.window, row=0, column=0, text='Problem list')
        frame_list_display = create_widget('frame', master=frame_list, row=0, column=0, padx=5, pady=5, sticky='N')
        frame_list_action = create_widget('frame', master=frame_list, row=1, column=0, padx=0, pady=0, sticky=None)
        frame_config = create_widget('frame', master=self.window, row=0, column=1, sticky=None, padx=0, pady=0)
        frame_config_display = create_widget('frame', master=frame_config, row=0, column=0, padx=0, pady=0, sticky='N')
        frame_config_action = create_widget('frame', master=frame_config, row=1, column=0, padx=0, pady=0, sticky=None)
        grid_configure(frame_list, 0, 0)
        grid_configure(frame_config, 0, 0)

        self.widget['list'] = Listbox(master=frame_list_display)
        self.widget['list'].grid()
        self.widget['create'] = create_widget('button', master=frame_list_action, row=0, column=0, text='Create')

        self.widget['info'] = ProblemInfoWidget(master=frame_config_display, row=0, column=0)
        self.widget['update'] = create_widget('button', master=frame_config_action, row=0, column=0, text='Update')
        self.widget['delete'] = create_widget('button', master=frame_config_action, row=0, column=1, text='Delete')

        self.widget['update'].disable()
        self.widget['delete'].disable()

    def set_problem_info(self, config):
        '''
        '''
        problem_info = {
            'name': config['name'],
            'var_type': config['type'],
            'n_var': config['n_var'],
            'n_obj': config['n_obj'],
            'n_constr': config['n_constr'],
            'obj_type': config['obj_type'],
        }
        self.widget['info'].set_info(problem_info)

    def clear_problem_info(self):
        '''
        '''
        self.widget['info'].clear_info()