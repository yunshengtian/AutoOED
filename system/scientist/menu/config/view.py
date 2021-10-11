import os
import tkinter as tk
from multiprocessing import cpu_count
from autooed.problem.common import get_problem_list
from autooed import get_algorithm_list
from system.gui.utils.grid import grid_configure
from system.gui.widgets.factory import create_widget
from system.scientist.map import config_map


class MenuConfigView:

    def __init__(self, root_view, first_time):
        self.root_view = root_view
        self.first_time = first_time

        title = 'Create Configurations' if self.first_time else 'Change Configurations'
        self.window = create_widget('toplevel', master=self.root_view.root, title=title)

        self.widget = {}

        # parameter section
        frame_param = tk.Frame(master=self.window)
        frame_param.grid(row=0, column=0)
        grid_configure(frame_param, 2, 0)

        # problem subsection
        frame_problem = create_widget('labeled_frame', master=frame_param, row=0, column=0, text='Problem')
        grid_configure(frame_problem, 0, 0)

        self.widget['problem_name'] = create_widget('labeled_combobox', 
            master=frame_problem, row=0, column=0, text=config_map['problem']['name'], values=get_problem_list(), width=15, required=True)
        self.widget['set_ref_point'] = create_widget('button',
            master=frame_problem, row=1, column=0, text='Set Reference Point', sticky=None)
        self.widget['set_ref_point'].disable()

        # algorithm subsection
        frame_algorithm = create_widget('labeled_frame', master=frame_param, row=1, column=0, text='Algorithm')
        grid_configure(frame_algorithm, 0, 0)
        self.widget['algo_name'] = create_widget('labeled_combobox', 
            master=frame_algorithm, row=0, column=0, text=config_map['algorithm']['name'], values=get_algorithm_list(), required=True)
        self.widget['n_process'] = create_widget('labeled_entry', 
            master=frame_algorithm, row=1, column=0, text=config_map['algorithm']['n_process'], class_type='int', default=cpu_count(),
            valid_check=lambda x: x > 0, error_msg='number of processes to use must be positive')
        self.widget['set_advanced'] = create_widget('button', master=frame_algorithm, row=2, column=0, text='Advanced Settings', sticky=None)
        
        # initialization subsection
        if self.first_time:
            frame_init = create_widget('labeled_frame', master=frame_param, row=2, column=0, text='Initialization')
            grid_configure(frame_init, 1, 0)

            self.widget['init_type'] = create_widget('radiobutton',
                master=frame_init, row=0, column=0, text_list=['Random', 'Provided'], default='Random')

            frame_random_init = create_widget('frame', master=frame_init, row=1, column=0, padx=0, pady=0)
            frame_provided_init = create_widget('frame', master=frame_init, row=1, column=0, padx=0, pady=0)

            self.widget['n_init'] = create_widget('labeled_entry', 
                master=frame_random_init, row=0, column=0, text=config_map['experiment']['n_random_sample'], class_type='int', required=True,
                valid_check=lambda x: x > 0, error_msg='number of random initial samples must be positive')

            self.widget['set_x_init'], self.widget['disp_x_init'] = create_widget('labeled_button_entry',
                master=frame_provided_init, row=0, column=0, label_text='Path of initial design variables', button_text='Browse', width=30, required=True,
                valid_check=lambda x: os.path.exists(x), error_msg='file does not exist')
            self.widget['set_y_init'], self.widget['disp_y_init'] = create_widget('labeled_button_entry',
                master=frame_provided_init, row=1, column=0, label_text='Path of initial performance values', button_text='Browse', width=30,
                valid_check=lambda x: os.path.exists(x), error_msg='file does not exist')

            def set_random_init():
                frame_provided_init.grid_remove()
                frame_random_init.grid()

            def set_provided_init():
                frame_random_init.grid_remove()
                frame_provided_init.grid()

            for text, button in self.widget['init_type'].widget.items():
                if text == 'Random':
                    button.configure(command=set_random_init)
                elif text == 'Provided':
                    button.configure(command=set_provided_init)
                else:
                    raise Exception()

            set_random_init()

        # evaluation subsection
        frame_experiment = create_widget('labeled_frame', master=frame_param, row=3 if self.first_time else 2, column=0, text='Experiment')
        grid_configure(frame_experiment, 0, 0)
        self.widget['n_worker'] = create_widget('labeled_entry',
            master=frame_experiment, row=0, column=0, text=config_map['experiment']['n_worker'], class_type='int', default=1,
            valid_check=lambda x: x > 0, error_msg='max number of evaluation workers must be positive')

        # action section
        frame_action = tk.Frame(master=self.window)
        frame_action.grid(row=1, column=0, columnspan=3)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')

        self.cfg_widget = {
            'problem': {
                'name': self.widget['problem_name'],
            },
            'algorithm': {
                'name': self.widget['algo_name'],
                'n_process': self.widget['n_process'],
            },
            'experiment': {
                'n_worker': self.widget['n_worker'],
            }
        }
