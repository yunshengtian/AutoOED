from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.utils.layout import grid_configure, center


class DisplaySettingsView:

    def __init__(self, root_view):
        self.root_view = root_view
        self.master_window = self.root_view.root
        self.window = create_widget('toplevel', master=self.master_window, title='Display Settings')
        frame_settings = create_widget('frame', master=self.window, row=0, column=0, padx=0, pady=0)
        grid_configure(frame_settings, 1, 0)
        
        self.widget = {}
        
        self.widget['cellwidth'] = create_widget('labeled_spinbox', master=frame_settings, row=0, column=0, text='Cell width:', from_=50, to=300, sticky='NSEW')
        self.widget['precision'] = create_widget('labeled_spinbox', master=frame_settings, row=1, column=0, text='Float precision:', from_=0, to=100, sticky='NSEW')

        frame_action = create_widget('frame', master=frame_settings, row=2, column=0, padx=0, pady=0)
        grid_configure(frame_action, 0, 1)
        self.widget['update'] = create_widget('button', master=frame_action, row=0, column=0, text='Update')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')

        center(self.window, self.master_window)

    def get_params(self):
        params = {}
        params['cellwidth'] = self.widget['cellwidth'].get()
        params['precision'] = self.widget['precision'].get()
        return params


class DisplaySettingsController:

    def __init__(self, root):
        self.root = root
        self.table = self.root.table
        self.view = DisplaySettingsView(self.root.view)

        self.view.widget['cellwidth'].set(self.table.params['cellwidth'])
        self.view.widget['precision'].set(self.table.params['precision'])

        self.view.widget['update'].configure(command=self.update_params)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def update_params(self):
        params = self.view.get_params()
        self.table.set_params(params)