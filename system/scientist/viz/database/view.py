from system.gui.widgets.factory import create_widget
from system.gui.utils.grid import grid_configure


class VizDatabaseView:

    def __init__(self, root_view):
        self.root_view = root_view
        
        self.frame = create_widget('frame', master=self.root_view.frame_db, row=0, column=0)