import tkinter as tk
from system.gui.widgets.excel import Excel
from system.gui.widgets.factory import create_widget
from system.scientist.map import config_map


class DesignBoundView:

    def __init__(self, root_view, var_name, var_lb, var_ub):
        self.root_view = root_view

        self.titles = ['var_name', 'var_lb', 'var_ub']
        n_var = len(var_name)

        self.window = tk.Toplevel(master=self.root_view.window)
        self.window.title('Set Design Bounds')
        self.window.resizable(False, False)

        self.widget = {}

        # design space section
        frame_design = create_widget('frame', master=self.window, row=0, column=0)
        create_widget('label', master=frame_design, row=0, column=0, text='Enter the bounds for design variables:')
        self.widget['design_excel'] = Excel(master=frame_design, rows=n_var, columns=3, width=15,
            title=[config_map['problem'][title] for title in self.titles], dtype=[str, float, float], default=[None, 0, 1])
        self.widget['design_excel'].grid(row=1, column=0)

        # action section
        frame_action = tk.Frame(master=self.window)
        frame_action.grid(row=1, column=0)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')