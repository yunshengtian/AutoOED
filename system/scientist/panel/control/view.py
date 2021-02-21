import tkinter as tk
from system.gui.widgets.button import Button
from system.gui.widgets.factory import create_widget
from system.gui.utils.grid import grid_configure
from system.scientist.map import config_map


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
            master=frame_control, row=1, column=0, text=config_map['experiment']['batch_size'], class_type='int', required=True, required_mark=False)
        
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
        self.widget['optimize_manual'] = Button(master=frame_manual, text="Optimize", state=tk.DISABLED)
        self.widget['optimize_manual'].grid(row=0, column=0, padx=5, pady=10, sticky='NSEW')
        self.widget['optimize_auto'] = Button(master=frame_auto, text="Optimize", state=tk.DISABLED)
        self.widget['optimize_auto'].grid(row=1, column=0, padx=5, pady=10, sticky='NSEW')

        # stop optimization command
        self.widget['stop_manual'] = Button(master=frame_manual, text='Stop', state=tk.DISABLED)
        self.widget['stop_manual'].grid(row=0, column=1, padx=5, pady=10, sticky='NSEW')
        self.widget['stop_auto'] = Button(master=frame_auto, text='Stop', state=tk.DISABLED)
        self.widget['stop_auto'].grid(row=1, column=1, padx=5, pady=10, sticky='NSEW')
