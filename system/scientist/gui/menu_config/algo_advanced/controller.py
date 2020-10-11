from system.gui.widgets.factory import show_widget_error
from system.scientist.gui.map import algo_config_map, algo_value_map, algo_value_inv_map
from .view import AlgoAdvancedView


class AlgoAdvancedController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.algo_cfg = {}
        self.surrogate_ts_visible = False # TODO: clean

        self.view = AlgoAdvancedView(self.root_view)

        self.view.widget['surrogate']['name'].widget.bind('<<ComboboxSelected>>', self.select_surrogate)
        self.view.widget['surrogate']['nu'].config(
            default=5,
        )
        self.view.widget['surrogate']['n_spectral_pts'].config(
            default=100,
            valid_check=lambda x: x > 0, 
            error_msg='number of spectral sampling points must be positive'
        )
        
        self.view.widget['solver']['n_gen'].config(
            default=200,
            valid_check=lambda x: x > 0, 
            error_msg='number of generations must be positive',
        )
        self.view.widget['solver']['pop_size'].config(
            default=100,
            valid_check=lambda x: x > 0, 
            error_msg='population size must be positive',
        )
        self.view.widget['solver']['pop_init_method'].config(
            default='Non-Dominated Sort',
        )

        self.view.widget['save'].configure(command=self.save_config_algo)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

        # load current config values to entry if not first time setting config
        curr_config = self.get_config()
        if not self.root_view.first_time and self.view.widget['algorithm']['name'].get() == curr_config['algorithm']['name']:
            self.load_curr_config_algo()

    def get_config(self):
        return self.root_controller.get_config()

    def select_surrogate(self, event):
        '''
        Select surrogate model type
        '''
        name = event.widget.get()
        if name == 'Gaussian Process' or name == 'Neural Network': # TODO
            if self.surrogate_ts_visible:
                self.view.widget['surrogate']['n_spectral_pts'].widget.master.grid_remove()
                self.view.widget['surrogate']['mean_sample'].master.grid_remove()
                self.surrogate_ts_visible = False
        elif name == 'Thompson Sampling':
            if not self.surrogate_ts_visible:
                self.view.widget['surrogate']['n_spectral_pts'].widget.master.grid()
                self.view.widget['surrogate']['mean_sample'].master.grid()
                self.surrogate_ts_visible = True
        else:
            raise NotImplementedError

    def load_curr_config_algo(self):
        '''
        Load advanced settings of algorithm
        '''
        if self.algo_cfg == {}:
            curr_config = self.get_config()
            self.algo_cfg.update(curr_config['algorithm'])
            self.algo_cfg.pop('name')
            self.algo_cfg.pop('n_process')
        for cfg_type, val_map in self.view.cfg_widget.items():
            for cfg_name, widget in val_map.items():
                if cfg_name not in self.algo_cfg[cfg_type]: continue
                val = self.algo_cfg[cfg_type][cfg_name]
                if cfg_name in algo_value_map[cfg_type]:
                    widget.set(algo_value_map[cfg_type][cfg_name][val])
                else:
                    widget.set(val)
                widget.select()
        
        self.view.widget['surrogate']['name'].select()

    def save_config_algo(self):
        '''
        Save advanced settings of algorithm
        '''
        temp_cfg = {}
        for cfg_type, val_map in self.view.cfg_widget.items():
            temp_cfg[cfg_type] = {}
            for cfg_name, widget in val_map.items():
                try:
                    val = widget.get()
                except:
                    show_widget_error(master=self.view.window, widget=widget, name=algo_config_map[cfg_type][cfg_name])
                    return
                if cfg_name in algo_value_inv_map[cfg_type]:
                    val = algo_value_inv_map[cfg_type][cfg_name][val]
                temp_cfg[cfg_type][cfg_name] = val

        self.view.window.destroy()

        for key, val in temp_cfg.items():
            self.algo_cfg[key] = val