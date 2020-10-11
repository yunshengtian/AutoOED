import tkinter as tk
from system.gui.utils.grid import grid_configure
from system.gui.widgets.factory import create_widget
from system.scientist.gui.map import algo_config_map, algo_value_map


class AlgoAdvancedView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.window = tk.Toplevel(master=self.root_view.window)
        self.window.title('Advanced Settings')
        self.window.resizable(False, False)

        self.widget = {
            'surrogate': {},
            'acquisition': {},
            'solver': {},
            'selection': {},
        }

        # parameter section
        frame_param_algo = tk.Frame(master=self.window)
        frame_param_algo.grid(row=0, column=0)
        grid_configure(frame_param_algo, 2, 0)

        # surrogate model subsection
        frame_surrogate = create_widget('labeled_frame', master=frame_param_algo, row=0, column=0, text='Surrogate Model')
        grid_configure(frame_surrogate, 3, 0)
        self.widget['surrogate']['name'] = create_widget('labeled_combobox',
            master=frame_surrogate, row=0, column=0, width=20, text=algo_config_map['surrogate']['name'], 
            values=list(algo_value_map['surrogate']['name'].values()), required=True)
        self.widget['surrogate']['nu'] = create_widget('labeled_combobox',
            master=frame_surrogate, row=1, column=0, width=5, text=algo_config_map['surrogate']['nu'], values=[1, 3, 5, -1], class_type='int')
        self.widget['surrogate']['n_spectral_pts'] = create_widget('labeled_entry',
            master=frame_surrogate, row=2, column=0, text=algo_config_map['surrogate']['n_spectral_pts'], class_type='int')
        self.widget['surrogate']['mean_sample'] = create_widget('checkbutton',
            master=frame_surrogate, row=3, column=0, text=algo_config_map['surrogate']['mean_sample'])

        # acquisition function subsection
        frame_acquisition = create_widget('labeled_frame', master=frame_param_algo, row=1, column=0, text='Acquisition Function')
        grid_configure(frame_acquisition, 0, 0)
        self.widget['acquisition']['name'] = create_widget('labeled_combobox',
            master=frame_acquisition, row=0, column=0, width=25, text=algo_config_map['acquisition']['name'], 
            values=list(algo_value_map['acquisition']['name'].values()), required=True)

        # multi-objective solver subsection
        frame_solver = create_widget('labeled_frame', master=frame_param_algo, row=2, column=0, text='Multi-Objective Solver')
        grid_configure(frame_solver, 3, 0)
        self.widget['solver']['name'] = create_widget('labeled_combobox',
            master=frame_solver, row=0, column=0, width=15, text=algo_config_map['solver']['name'], 
            values=list(algo_value_map['solver']['name'].values()), required=True)
        self.widget['solver']['n_gen'] = create_widget('labeled_entry',
            master=frame_solver, row=1, column=0, text=algo_config_map['solver']['n_gen'], class_type='int')
        self.widget['solver']['pop_size'] = create_widget('labeled_entry',
            master=frame_solver, row=2, column=0, text=algo_config_map['solver']['pop_size'], class_type='int')
        self.widget['solver']['pop_init_method'] = create_widget('labeled_combobox',
            master=frame_solver, row=3, column=0, width=25, text=algo_config_map['solver']['pop_init_method'], 
            values=list(algo_value_map['solver']['pop_init_method'].values()))

        # selection method subsection
        frame_selection = create_widget('labeled_frame', master=frame_param_algo, row=3, column=0, text='Selection Method')
        grid_configure(frame_selection, [0], [0])
        self.widget['selection']['name'] = create_widget('labeled_combobox',
            master=frame_selection, row=0, column=0, width=25, text=algo_config_map['selection']['name'], 
            values=list(algo_value_map['selection']['name'].values()), required=True)

        # action section
        frame_action = tk.Frame(master=self.window)
        frame_action.grid(row=1, column=0)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')

        self.cfg_widget = {
            'surrogate': {},
            'acquisition': {}, 
            'solver': {},
            'selection': {},
        }

        for key in self.cfg_widget.keys():
            self.cfg_widget[key] = self.widget[key]