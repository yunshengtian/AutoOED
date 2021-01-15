from system.gui.widgets.factory import create_widget
from system.gui.widgets_modular import AdjustableTable


class VizDatabaseView:

    def __init__(self, root_view, columns):
        self.root_view = root_view

        self.widget = {}
        
        frame_db = create_widget('frame', master=self.root_view.frame_db, row=0, column=0, padx=0, pady=0)
        self.widget['table'] = AdjustableTable(master=frame_db, columns=columns)