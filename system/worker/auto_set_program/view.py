import tkinter as tk
from system.gui.widgets.factory import create_widget
from system.scientist.map import config_map


class AutoSetProgramView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.window = create_widget('toplevel', master=self.root_view.root, title='Set Evaluation Program')

        self.widget = {}

        frame_program = create_widget('frame', master=self.window, row=0, column=0)
        self.widget['browse_obj_func'], self.widget['disp_obj_func'] = create_widget('labeled_button_entry',
            master=frame_program, row=0, column=0, label_text=config_map['problem']['obj_func'], button_text='Browse', width=30, required=True)

        frame_action = tk.Frame(master=self.window)
        frame_action.grid(row=1, column=0)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')