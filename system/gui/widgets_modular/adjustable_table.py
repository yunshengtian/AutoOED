from system.gui.widgets.table import Table
from system.gui.widgets.factory import create_widget
from system.gui.utils.grid import grid_configure


class AdjustableTable(Table):

    def __init__(self, master, columns):
        '''
        '''
        self.widget = {}
        
        frame_table = create_widget('frame', master=master, row=0, column=0, padx=0, pady=0)
        grid_configure(master, 0, 0)
        super().__init__(frame_table, columns)

        frame_settings = create_widget('frame', master=master, row=1, column=0, padx=0, pady=0)
        self.widget['cellwidth'] = create_widget('spinbox', master=frame_settings, row=0, column=0, text='Cell width', from_=50, to=300)
        self.widget['precision'] = create_widget('spinbox', master=frame_settings, row=0, column=1, text='Float precision', from_=0, to=100)
        self.widget['update'] = create_widget('button', master=frame_settings, row=0, column=2, text='Update')

        self.widget['cellwidth'].set(self.params['cellwidth'])
        self.widget['precision'].set(self.params['precision'])
        self.widget['update'].configure(command=self.update_params)

    def update_params(self):
        '''
        '''
        params = {}
        params['cellwidth'] = self.widget['cellwidth'].get()
        params['precision'] = self.widget['precision'].get()
        self.set_params(params)
