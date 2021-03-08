from system.gui.widgets.factory import create_widget
from system.gui.widgets_modular import AdjustableTable


class VizDatabaseView:

    def __init__(self, root_view, columns):
        self.root_view = root_view
        self.root = self.root_view.root

        self.widget = {}
        
        frame_db = create_widget('frame', master=self.root_view.frame_db, row=0, column=0, padx=0, pady=0)
        self.widget['table'] = AdjustableTable(master=frame_db, columns=columns)

        frame_enter = create_widget('frame', master=frame_db, row=1, column=0, padx=0, pady=0)
        self.widget['enter_design'] = create_widget('button', master=frame_enter, row=0, column=0, text='Enter Design')
        self.widget['enter_performance'] = create_widget('button', master=frame_enter, row=0, column=1, text='Enter Performance')
        self.widget['table'].widget['set'].grid(row=1, column=1)

    def get_table_columns(self):
        return self.widget['table'].columns