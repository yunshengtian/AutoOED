import tkinter as tk
from system.scientist.map import config_map
from .view import PanelControlView

from .stop_criterion import StopCriterionController


class PanelControlController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.agent = self.root_controller.agent
        self.scheduler = self.root_controller.scheduler
        self.stop_criterion = []

        self.view = PanelControlView(self.root_view)

        self.view.widget['batch_size'].config(
            valid_check=lambda x: x > 0, 
            error_msg='number of batch size must be positive',
        )
        self.view.widget['set_stop_cri'].configure(command=self.set_stop_criterion)

        self.view.widget['optimize_manual'].configure(command=self.optimize_manual)
        self.view.widget['optimize_auto'].configure(command=self.optimize_auto)
        self.view.widget['stop_manual'].configure(command=self.stop_manual)
        self.view.widget['stop_auto'].configure(command=self.stop_auto)

    def get_config(self):
        return self.root_controller.get_config()

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

    def _set_optimize_config(self):
        '''
        '''
        config = self.get_config()
        try:
            config['experiment']['batch_size'] = self.view.widget['batch_size'].get()
        except:
            error_msg = self.view.widget['batch_size'].get_error_msg()
            error_msg = '' if error_msg is None else ': ' + error_msg
            tk.messagebox.showinfo('Error', 'Invalid value for "' + config_map['experiment']['batch_size'] + '"' + error_msg, parent=self.root_view.root)
            return
        self.set_config(config)

    def enable_manual(self):
        if self.root_view.menu_config.entrycget(0, 'state') != tk.NORMAL:
            self.root_view.menu_config.entryconfig(0, state=tk.NORMAL)
        if self.root_view.menu_config.entrycget(2, 'state') != tk.NORMAL:
            self.root_view.menu_config.entryconfig(2, state=tk.NORMAL)
        self.view.widget['mode'].enable()
        self.view.widget['optimize_manual'].enable()
        self.view.widget['stop_manual'].disable()

    def enable_auto(self):
        if self.root_view.menu_config.entrycget(0, 'state') != tk.NORMAL:
            self.root_view.menu_config.entryconfig(0, state=tk.NORMAL)
        if self.root_view.menu_config.entrycget(2, 'state') != tk.NORMAL:
            self.root_view.menu_config.entryconfig(2, state=tk.NORMAL)
        self.view.widget['mode'].enable()
        self.view.widget['set_stop_cri'].enable()
        self.view.widget['optimize_auto'].enable()
        self.view.widget['stop_auto'].disable()

    def disable_manual(self):
        if self.root_view.menu_config.entrycget(0, 'state') != tk.DISABLED:
            self.root_view.menu_config.entryconfig(0, state=tk.DISABLED)
        if self.root_view.menu_config.entrycget(2, 'state') != tk.DISABLED:
            self.root_view.menu_config.entryconfig(2, state=tk.DISABLED)
        self.view.widget['mode'].disable()
        self.view.widget['optimize_manual'].disable()
        self.view.widget['stop_manual'].enable()

    def disable_auto(self):
        if self.root_view.menu_config.entrycget(0, 'state') != tk.DISABLED:
            self.root_view.menu_config.entryconfig(0, state=tk.DISABLED)
        if self.root_view.menu_config.entrycget(2, 'state') != tk.DISABLED:
            self.root_view.menu_config.entryconfig(2, state=tk.DISABLED)
        self.view.widget['mode'].disable()
        self.view.widget['set_stop_cri'].disable()
        self.view.widget['optimize_auto'].disable()
        self.view.widget['stop_auto'].enable()

    def optimize_manual(self):
        '''
        Execute manual optimization
        '''
        self.disable_manual()
        self._set_optimize_config()
        self.scheduler.optimize_manual()

    def optimize_auto(self):
        '''
        Execute auto optimization
        '''
        self.disable_auto()
        self._set_optimize_config()
        self.scheduler.optimize_auto(stop_criterion=self.stop_criterion)

    def stop_manual(self):
        '''
        Stop manual optimization (TODO: support stopping individual process)
        '''
        self.scheduler.stop_optimize()
        self.enable_manual()

    def stop_auto(self):
        '''
        Stop auto optimization (TODO: support stopping individual process)
        '''
        self.scheduler.stop_optimize()
        self.enable_auto()
        self.stop_criterion.clear()