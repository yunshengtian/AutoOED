import tkinter as tk
from system.scientist.gui.map import config_map
from .view import PanelControlView

from .stop_criterion import StopCriterionController


class PanelControlController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.worker_agent = self.root_controller.worker_agent
        self.stop_criterion = {}

        self.view = PanelControlView(self.root_view)

        self.view.widget['batch_size'].config(
            valid_check=lambda x: x > 0, 
            error_msg='number of batch size must be positive',
        )
        self.view.widget['n_iter'].config(
            valid_check=lambda x: x > 0, 
            error_msg='number of optimization iteration must be positive',
        )

        self.view.widget['set_stop_cri'].configure(command=self.set_stop_criterion)

        self.view.widget['optimize'].configure(command=self.optimize)
        self.view.widget['stop'].configure(command=self.stop_optimize)

    def get_config(self):
        return self.root_controller.get_config()

    def get_config_id(self):
        return self.root_controller.get_config_id()

    def set_config(self, *args, **kwargs):
        return self.root_controller.set_config(*args, **kwargs)

    def get_timestamp(self):
        return self.root_controller.get_timestamp()

    def set_timestamp(self):
        return self.root_controller.set_timestamp()

    def set_stop_criterion(self):
        '''
        Set stopping criterion for optimization
        '''
        StopCriterionController(self)

    def optimize(self):
        '''
        Execute optimization
        '''
        config = self.get_config().copy()
        for key in ['batch_size', 'n_iter']:
            try:
                config['general'][key] = self.view.cfg_widget[key].get()
            except:
                error_msg = self.view.cfg_widget[key].get_error_msg()
                error_msg = '' if error_msg is None else ': ' + error_msg
                tk.messagebox.showinfo('Error', 'Invalid value for "' + config_map['general'][key] + '"' + error_msg, parent=self.root_view.root)
                return

        self.set_config(config)

        self.root_view.menu_config.entryconfig(0, state=tk.DISABLED)
        self.root_view.menu_config.entryconfig(2, state=tk.DISABLED)
        self.view.widget['mode'].disable()
        if self.view.widget['mode'].get() == 'auto':
            self.view.widget['optimize'].disable()
        self.view.widget['stop'].enable()

        mode = self.view.widget['mode'].get()
        config, config_id = self.get_config(), self.get_config_id()
        self.worker_agent.configure(mode=mode, config=config, config_id=config_id)
        self.worker_agent.add_opt_worker()

    def stop_optimize(self):
        '''
        Stop optimization (TODO: support stopping individual process)
        '''
        self.worker_agent.stop_worker()
        self.view.widget['mode'].enable()
        self.view.widget['stop'].disable()