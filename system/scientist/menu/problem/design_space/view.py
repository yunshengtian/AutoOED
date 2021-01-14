import tkinter as tk
from system.gui.widgets.factory import create_widget
from system.gui.widgets.excel import Excel
from system.scientist.map import config_map


class DesignSpaceView:

    def __init__(self, root_view, n_var):
        self.root_view = root_view
        self.n_var = n_var

        self.titles = ['var_name', 'var_lb', 'var_ub']

        self.window = tk.Toplevel(master=root_view.window)
        self.window.title('Configure Design Space')
        self.window.resizable(False, False)

        self.widget = {}

        # design space section
        frame_design = create_widget('frame', master=self.window, row=0, column=0)
        create_widget('label', master=frame_design, row=0, column=0, text='Enter the properties for design variables:')
        self.widget['design_excel'] = Excel(master=frame_design, rows=self.n_var, columns=3, width=15,
            title=[config_map['problem'][title] for title in self.titles], dtype=[str, float, float], default=[None, 0, 1])
        self.widget['design_excel'].grid(row=1, column=0)
        self.widget['design_excel'].set_column(0, [f'x{i + 1}' for i in range(self.n_var)])

        # action section
        frame_action = tk.Frame(master=self.window)
        frame_action.grid(row=1, column=0)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')