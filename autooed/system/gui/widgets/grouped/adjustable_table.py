from autooed.system.gui.widgets.table import Table
from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.utils.grid import grid_configure


class DisplaySettingsView:

    def __init__(self, master):
        self.window = create_widget('toplevel', master=master, title='Display Settings')
        frame_settings = create_widget('frame', master=self.window, row=0, column=0, padx=0, pady=0)
        grid_configure(frame_settings, 1, 0)
        
        self.widget = {}
        
        self.widget['cellwidth'] = create_widget('spinbox', master=frame_settings, row=0, column=0, text='Cell width:', from_=50, to=300, sticky='NSEW')
        self.widget['precision'] = create_widget('spinbox', master=frame_settings, row=1, column=0, text='Float precision:', from_=0, to=100, sticky='NSEW')

        frame_action = create_widget('frame', master=frame_settings, row=2, column=0, padx=0, pady=0)
        grid_configure(frame_action, 0, 1)
        self.widget['update'] = create_widget('button', master=frame_action, row=0, column=0, text='Update')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')

    def get_params(self):
        params = {}
        params['cellwidth'] = self.widget['cellwidth'].get()
        params['precision'] = self.widget['precision'].get()
        return params


class DisplaySettingsController:

    def __init__(self, root):
        self.root = root
        self.view = DisplaySettingsView(self.root.master)

        self.view.widget['cellwidth'].set(self.root.params['cellwidth'])
        self.view.widget['precision'].set(self.root.params['precision'])

        self.view.widget['update'].configure(command=self.update_params)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def update_params(self):
        params = self.view.get_params()
        self.root.set_params(params)


class AdjustableTable(Table):

    def __init__(self, master, columns):
        '''
        '''
        self.master = master
        self.widget = {}
        
        frame_table = create_widget('frame', master=master, row=0, column=0, columnspan=2, padx=0, pady=0)
        grid_configure(master, 0, 0)
        super().__init__(frame_table, columns)

        self.widget['set'] = create_widget('button', master=master, row=1, column=0, sticky='E', text='Display Settings', command=self.update_settings)

    def update_settings(self):
        DisplaySettingsController(self)
