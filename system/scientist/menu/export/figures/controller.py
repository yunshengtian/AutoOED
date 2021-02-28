import tkinter as tk
from tkinter.filedialog import asksaveasfile
from .view import MenuExportFiguresView


class MenuExportFiguresController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = MenuExportFiguresView(self.root_view)

        self.view.widget['export'].configure(command=self.export)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def export(self):
        '''
        '''
        try:
            path = asksaveasfile(defaultextension='.png')
        except Exception as e:
            tk.messagebox.showinfo('Error', str(e), parent=self.view.window)
            return

        viz_space_controller = self.root_controller.root_controller.controller['viz_space']
        viz_stats_controller = self.root_controller.root_controller.controller['viz_stats']

        choice = self.view.widget['choice'].get()
        if choice == 'Performance Space':
            viz_space_controller.save_performance_figure(path.name)
        elif choice == 'Selected Design':
            viz_space_controller.save_design_figure(path.name)
        elif choice == 'Hypervolume':
            viz_stats_controller.save_hv_figure(path.name)
        elif choice == 'Model Error':
            viz_stats_controller.save_error_figure(path.name)
        else:
            tk.messagebox.showinfo('Invalid Choice', f'Cannot export {choice}', parent=self.view.window)
            return

        self.view.window.destroy()