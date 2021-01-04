from system.gui.widgets.factory import create_widget
from system.gui.utils.grid import grid_configure
from system.scientist.map import algo_config_map, algo_value_map


class SolverView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.widget = {}

        self.frame = create_widget('frame', master=self.root_view.frame_solver, row=2, column=0)
        grid_configure(self.frame, None, 0)
        
        self.widget['name'] = create_widget('labeled_combobox',
            master=self.frame, row=0, column=0, width=15, text=algo_config_map['solver']['name'], 
            values=list(algo_value_map['solver']['name'].values()), required=True)
        self.widget['n_gen'] = create_widget('labeled_entry',
            master=self.frame, row=1, column=0, text=algo_config_map['solver']['n_gen'], class_type='int',
            default=200, valid_check=lambda x: x > 0, error_msg='number of generations must be positive')
        self.widget['pop_size'] = create_widget('labeled_entry',
            master=self.frame, row=2, column=0, text=algo_config_map['solver']['pop_size'], class_type='int',
            default=100, valid_check=lambda x: x > 0, error_msg='population size must be positive')
        self.widget['pop_init_method'] = create_widget('labeled_combobox',
            master=self.frame, row=3, column=0, width=25, text=algo_config_map['solver']['pop_init_method'], 
            values=list(algo_value_map['solver']['pop_init_method'].values()),
            default='Non-Dominated Sort')

        self.create_frame_param()

        self.curr_name = None

        self.activate = {
            'NSGA-II': self.activate_nsga2,
            'MOEA/D': self.activate_moead,
            'ParEGO Solver': self.activate_parego,
            'Pareto Discovery': self.activate_discovery,
        }
        self.deactivate = {
            'NSGA-II': self.deactivate_nsga2,
            'MOEA/D': self.deactivate_moead,
            'ParEGO Solver': self.deactivate_parego,
            'Pareto Discovery': self.deactivate_discovery,
        }

    def create_frame_param(self):
        self.frame_param = create_widget('frame', master=self.frame, row=4, column=0, padx=0, pady=0, sticky='NSEW')
        grid_configure(self.frame_param, None, 0)

    def select(self, name):
        if name == self.curr_name: return
        if self.curr_name is not None:
            self.deactivate[self.curr_name]()
            self.frame_param.destroy()
            self.create_frame_param()
        self.activate[name]()
        self.curr_name = name

    def activate_nsga2(self):
        pass

    def deactivate_nsga2(self):
        pass

    def activate_moead(self):
        pass

    def deactivate_moead(self):
        pass

    def activate_parego(self):
        pass

    def deactivate_parego(self):
        pass

    def activate_discovery(self):
        # n_cell=None,
        # cell_size=None,
        # buffer_origin=None,
        # buffer_origin_constant=1e-2,
        # delta_b=0.2,
        # label_cost=0,
        # delta_p=10,
        # delta_s=0.3,
        # n_grid_sample=1000,
        # n_process=cpu_count(),
        pass

    def deactivate_discovery(self):
        pass