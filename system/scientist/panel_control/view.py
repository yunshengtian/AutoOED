import tkinter as tk
from system.gui.widgets.button import Button
from system.gui.widgets.factory import create_widget
from system.scientist.map import config_map


class PanelControlView:

    def __init__(self, root_view):
        self.root_view = root_view

        # control overall frame
        frame_control = create_widget('labeled_frame', master=self.root_view.root, row=1, column=1, text='Control')

        self.widget = {}
        self.widget['mode'] = create_widget('labeled_combobox',
            master=frame_control, row=0, column=0, columnspan=2, text='Optimization mode', values=['manual', 'auto'], required=True, required_mark=False)
        self.widget['batch_size'] = create_widget('labeled_entry', 
            master=frame_control, row=1, column=0, columnspan=2, text=config_map['general']['batch_size'], class_type='int', required=True, required_mark=False)
        self.widget['n_iter'] = create_widget('labeled_entry', 
            master=frame_control, row=2, column=0, columnspan=2, text=config_map['general']['n_iter'], class_type='int', required=True, required_mark=False)

        self.widget['set_stop_cri'] = create_widget('labeled_button', 
            master=frame_control, row=3, column=0, columnspan=2, label_text='Stopping criterion', button_text='Set', pady=5)

        for key in ['mode', 'batch_size', 'n_iter', 'set_stop_cri']:
            self.widget[key].disable()

        # optimization command
        self.widget['optimize'] = Button(master=frame_control, text="Optimize", state=tk.DISABLED)
        self.widget['optimize'].grid(row=4, column=0, padx=5, pady=10, sticky='NSEW')

        # stop optimization command
        self.widget['stop'] = Button(master=frame_control, text='Stop', state=tk.DISABLED)
        self.widget['stop'].grid(row=4, column=1, padx=5, pady=10, sticky='NSEW')

        self.cfg_widget = {
            'mode': self.widget['mode'],
            'batch_size': self.widget['batch_size'],
            'n_iter': self.widget['n_iter'],
        }