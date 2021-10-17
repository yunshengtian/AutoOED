import tkinter as tk

from autooed.system.gui.panel.control.stop_criterion import StopCriterionController
from autooed.system.gui.widgets.button import Button
from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.utils.grid import grid_configure


class PanelControlView:

    def __init__(self, root_view):
        self.root_view = root_view

        # control overall frame
        frame_control = create_widget('labeled_frame', master=self.root_view.root, row=1, column=1, text='Control')
        grid_configure(frame_control, 2, 0)

        self.widget = {}
        self.widget['mode'] = create_widget('radiobutton',
            master=frame_control, row=0, column=0, text_list=['Manual', 'Auto'], default='Manual')
        self.widget['batch_size'] = create_widget('labeled_entry', 
            master=frame_control, row=1, column=0, text='Batch size', class_type='int', required=True, required_mark=False)
        
        frame_manual = create_widget('frame', master=frame_control, row=2, column=0, padx=0, pady=0)
        frame_auto = create_widget('frame', master=frame_control, row=2, column=0, padx=0, pady=0)
        grid_configure(frame_manual, 0, 1)
        grid_configure(frame_auto, 1, 1)
        frame_auto.grid_remove()

        def set_manual():
            frame_auto.grid_remove()
            frame_manual.grid()

        def set_auto():
            frame_manual.grid_remove()
            frame_auto.grid()

        for text, button in self.widget['mode'].widget.items():
            if text == 'Manual':
                button.configure(command=set_manual)
            elif text == 'Auto':
                button.configure(command=set_auto)
            else:
                raise Exception()

        self.widget['set_stop_cri'] = create_widget('labeled_button', 
            master=frame_auto, row=0, column=0, columnspan=2, label_text='Stopping criterion', button_text='Set', pady=5)

        for key in ['mode', 'batch_size', 'set_stop_cri']:
            self.widget[key].disable()

        # optimization command
        self.widget['optimize_manual'] = create_widget('button', master=frame_manual, row=0, column=0, text='Optimize')
        self.widget['optimize_manual'].disable()
        self.widget['optimize_auto'] = create_widget('button', master=frame_auto, row=1, column=0, text='Optimize')
        self.widget['optimize_auto'].disable()

        # stop optimization command
        self.widget['stop_manual'] = create_widget('button', master=frame_manual, row=0, column=1, text='Stop')
        self.widget['stop_manual'].disable()
        self.widget['stop_auto'] = create_widget('button', master=frame_auto, row=1, column=1, text='Stop')
        self.widget['stop_auto'].disable()


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
            tk.messagebox.showinfo('Error', 'Invalid batch size' + error_msg, parent=self.root_view.root)
            return
        self.set_config(config)

    def enable_manual(self):
        if self.root_view.menu_config.entrycget(2, 'state') != tk.NORMAL:
            self.root_view.menu_config.entryconfig(2, state=tk.NORMAL)
        self.view.widget['mode'].enable('Manual')
        self.view.widget['optimize_manual'].enable()
        self.view.widget['stop_manual'].disable()

    def enable_auto(self):
        if self.root_view.menu_config.entrycget(2, 'state') != tk.NORMAL:
            self.root_view.menu_config.entryconfig(2, state=tk.NORMAL)
        self.view.widget['mode'].enable('Auto')
        self.view.widget['set_stop_cri'].enable()
        self.view.widget['optimize_auto'].enable()
        self.view.widget['stop_auto'].disable()

    def disable_manual(self):
        if self.root_view.menu_config.entrycget(2, 'state') != tk.DISABLED:
            self.root_view.menu_config.entryconfig(2, state=tk.DISABLED)
        self.view.widget['mode'].disable('Manual')
        self.view.widget['optimize_manual'].disable()
        self.view.widget['stop_manual'].enable()

    def disable_auto(self):
        if self.root_view.menu_config.entrycget(2, 'state') != tk.DISABLED:
            self.root_view.menu_config.entryconfig(2, state=tk.DISABLED)
        self.view.widget['mode'].disable('Auto')
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