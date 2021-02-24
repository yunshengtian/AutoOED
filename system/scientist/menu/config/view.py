import tkinter as tk
from problem.common import get_problem_list
from algorithm.utils import get_algorithm_list
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
        if self.first_time:
            grid_configure(frame_problem, 4, 0)
        else:
            grid_configure(frame_problem, 2, 0)

        self.widget['problem_name'] = create_widget('labeled_combobox', 
            master=frame_problem, row=0, column=0, text=config_map['problem']['name'], values=get_problem_list(), width=15, required=True)
        self.widget['ref_point'] = create_widget('labeled_entry', 
            master=frame_problem, row=1, column=0, text=config_map['problem']['ref_point'], class_type='floatlist', width=10)
        
        # initial samples related
        if self.first_time:
            self.widget['n_init'] = create_widget('labeled_entry', 
                master=frame_problem, row=2, column=0, text=config_map['problem']['n_random_sample'], class_type='int')
            self.widget['set_x_init'], self.widget['disp_x_init'] = create_widget('labeled_button_entry',
                master=frame_problem, row=3, column=0, label_text='Path of provided initial design variables', button_text='Browse', width=30)
            self.widget['set_y_init'], self.widget['disp_y_init'] = create_widget('labeled_button_entry',
                master=frame_problem, row=4, column=0, label_text='Path of provided initial performance values', button_text='Browse', width=30)

        # algorithm subsection
        frame_algorithm = create_widget('labeled_frame', master=frame_param, row=1, column=0, text='Algorithm')
        grid_configure(frame_algorithm, 0, 0)
        self.widget['algo_name'] = create_widget('labeled_combobox', 
            master=frame_algorithm, row=0, column=0, text=config_map['algorithm']['name'], values=get_algorithm_list(), required=True)
        self.widget['n_process'] = create_widget('labeled_entry', 
            master=frame_algorithm, row=1, column=0, text=config_map['algorithm']['n_process'], class_type='int', default=1)
        self.widget['set_advanced'] = create_widget('button', master=frame_algorithm, row=2, column=0, text='Advanced Settings', sticky=None)

        # evaluation subsection
        frame_experiment = create_widget('labeled_frame', master=frame_param, row=2, column=0, text='Experiment')
        grid_configure(frame_experiment, 0, 0)
        self.widget['batch_size'] = create_widget('labeled_entry',
            master=frame_experiment, row=0, column=0, text=config_map['experiment']['batch_size'], class_type='int', required=True)
        self.widget['n_worker'] = create_widget('labeled_entry',
            master=frame_experiment, row=1, column=0, text=config_map['experiment']['n_worker'], class_type='int')

        # action section
        frame_action = tk.Frame(master=self.window)
        frame_action.grid(row=1, column=0, columnspan=3)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')

        self.cfg_widget = {
            'problem': {
                'name': self.widget['problem_name'],
                'ref_point': self.widget['ref_point'],
            },
            'algorithm': {
                'name': self.widget['algo_name'],
                'n_process': self.widget['n_process'],
            },
            'experiment': {
                'batch_size': self.widget['batch_size'],
                'n_worker': self.widget['n_worker'],
            }
        }
