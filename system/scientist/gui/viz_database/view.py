from system.gui.widgets.factory import create_widget
from system.gui.utils.grid import grid_configure


class DatabaseView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.widget = {}

        self.frame = create_widget('frame', master=self.root_view.frame_db, row=0, column=0, sticky=None)
        grid_configure(self.frame, [0], [0, 1, 2, 3])
        self.widget['enter_design'] = create_widget('button', master=self.frame, row=0, column=0, text='Enter Design Variables')
        self.widget['enter_performance'] = create_widget('button', master=self.frame, row=0, column=1, text='Enter Performance Values')
        self.widget['start_local_eval'] = create_widget('button', master=self.frame, row=0, column=2, text='Start Local Evaluation')
        self.widget['start_remote_eval'] = create_widget('button', master=self.frame, row=0, column=3, text='Start Remote Evaluation')
        self.widget['stop_eval'] = create_widget('button', master=self.frame, row=0, column=4, text='Stop Evaluation')

        self.frame_db_table = create_widget('frame', master=self.root_view.frame_db, row=1, column=0)