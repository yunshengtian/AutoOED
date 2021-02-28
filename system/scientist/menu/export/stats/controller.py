import numpy as np
import pandas as pd
import tkinter as tk
from tkinter.filedialog import asksaveasfile
from .view import MenuExportStatsView


class MenuExportStatsController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.agent = self.root_controller.agent

        self.view = MenuExportStatsView(self.root_view)

        self.view.widget['export'].configure(command=self.export)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def export(self):
        '''
        '''
        choice = self.view.widget['choice'].get()

        if choice == 'Hypervolume':
            data = self.agent.load_hypervolume()
            x = np.arange(len(data))
            df = pd.DataFrame({'Number of samples': x, 'Hypervolume': data})

        elif choice == 'Model Error':
            data = self.agent.load_model_error()
            obj_name = self.agent.problem_cfg['obj_name']
            x = np.arange(len(data))
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