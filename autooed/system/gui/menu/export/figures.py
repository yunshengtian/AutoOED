import tkinter as tk
from tkinter.filedialog import asksaveasfile

from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.utils.layout import center


class MenuExportFiguresView:

    def __init__(self, root_view, n_obj):
        self.root_view = root_view
        self.master_window = self.root_view.root_view.root
        self.window = create_widget('toplevel', master=self.master_window, title='Export Figures')

        self.widget = {}
        
        if n_obj == 1:
            text_list = ['Performance Space', 'Selected Design', 'Optimum', 'Model Error']
        else:
            text_list = ['Performance Space', 'Selected Design', 'Hypervolume', 'Model Error']
        self.widget['choice'] = create_widget('radiobutton',
            master=self.window, row=0, column=0, text_list=text_list, 
            default='Performance Space', orientation='vertical')

        frame_action = create_widget('frame', master=self.window, row=1, column=0, padx=0, pady=0, sticky=None)
        self.widget['export'] = create_widget('button', master=frame_action, row=0, column=0, text='Export')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')

        center(self.window, self.master_window)


class MenuExportFiguresController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        n_obj = self.root_controller.agent.problem_cfg['n_obj']
        self.view = MenuExportFiguresView(self.root_view, n_obj)

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
        elif choice == 'Hypervolume' or choice == 'Optimum':
            viz_stats_controller.save_hv_figure(path.name)
        elif choice == 'Model Error':
            viz_stats_controller.save_error_figure(path.name)
        else:
            tk.messagebox.showinfo('Invalid Choice', f'Cannot export {choice}', parent=self.view.window)
            return

        self.view.window.destroy()