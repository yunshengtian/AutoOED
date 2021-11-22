import numpy as np
import pandas as pd
import tkinter as tk
from tkinter.filedialog import asksaveasfile

from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.utils.layout import center


class MenuExportStatsView:

    def __init__(self, root_view, n_obj):
        self.root_view = root_view
        self.master_window = self.root_view.root_view.root
        self.window = create_widget('toplevel', master=self.master_window, title='Export Statistics')

        self.widget = {}
        if n_obj == 1:
            self.widget['choice'] = create_widget('radiobutton',
                master=self.window, row=0, column=0, text_list=['Optimum', 'Model Error'], default='Optimum')
        else:
            self.widget['choice'] = create_widget('radiobutton',
                master=self.window, row=0, column=0, text_list=['Hypervolume', 'Model Error'], default='Hypervolume')

        frame_action = create_widget('frame', master=self.window, row=1, column=0, padx=0, pady=0, sticky=None)
        self.widget['export'] = create_widget('button', master=frame_action, row=0, column=0, text='Export')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')

        center(self.window, self.master_window)


class MenuExportStatsController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.agent = self.root_controller.agent
        
        n_obj = self.agent.problem_cfg['n_obj']
        self.view = MenuExportStatsView(self.root_view, n_obj)

        self.view.widget['export'].configure(command=self.export)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def export(self):
        '''
        '''
        choice = self.view.widget['choice'].get()

        if choice == 'Optimum':
            data = self.agent.load_hypervolume()
            x = np.arange(len(data))
            df = pd.DataFrame({'Number of samples': x, 'Optimum': data})

        elif choice == 'Hypervolume':
            data = self.agent.load_hypervolume()
            x = np.arange(len(data))
            df = pd.DataFrame({'Number of samples': x, 'Hypervolume': data})

        elif choice == 'Model Error':
            data = self.agent.load_model_error().T
            obj_name = self.agent.problem_cfg['obj_name']
            x = np.arange(self.agent.get_n_init_sample(), self.agent.get_n_valid_sample())
            df_dict = {'Number of samples': x}
            for name, d in zip(obj_name, data):
                df_dict[f'{name} error'] = d
            df = pd.DataFrame(df_dict)
            
        else:
            tk.messagebox.showinfo('Invalid Choice', f'Cannot export {choice}', parent=self.view.window)
            return

        if len(data) == 0:
            tk.messagebox.showinfo('Empty Data', f'{choice} data is empty, cannot export', parent=self.view.window)
            return

        try:
            path = asksaveasfile(defaultextension='.csv')
        except Exception as e:
            tk.messagebox.showinfo('Error', str(e), parent=self.view.window)
            return

        if path is None:
            return
        
        try:
            df.to_csv(path.name, index=False)
        except Exception as e:
            tk.messagebox.showinfo('Error', str(e), parent=self.view.window)
            return

        self.view.window.destroy()