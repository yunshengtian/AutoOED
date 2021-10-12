import tkinter as tk
from tkinter.filedialog import asksaveasfile

from autooed.system.gui.widgets.factory import create_widget


class MenuExportFiguresView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.window = create_widget('toplevel', master=self.root_view.root_view.root, title='Export Figures')

        self.widget = {}
        self.widget['choice'] = create_widget('radiobutton',
            master=self.window, row=0, column=0, text_list=['Performance Space', 'Selected Design', 'Hypervolume', 'Model Error'], 
            default='Performance Space', orientation='vertical')

        frame_action = create_widget('frame', master=self.window, row=1, column=0, padx=0, pady=0, sticky=None)
        self.widget['export'] = create_widget('button', master=frame_action, row=0, column=0, text='Export')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')


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

        if path is None:
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