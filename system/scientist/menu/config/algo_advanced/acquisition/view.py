from system.gui.widgets.factory import create_widget
from system.gui.utils.grid import grid_configure
from system.scientist.map import algo_config_map, algo_value_map


class AcquisitionView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.widget = {}

        self.frame = create_widget('frame', master=self.root_view.frame_acquisition, row=1, column=0)
        grid_configure(self.frame, None, 0)
        self.widget['name'] = create_widget('labeled_combobox',
            master=self.frame, row=0, column=0, width=25, text=algo_config_map['acquisition']['name'], 
            values=list(algo_value_map['acquisition']['name'].values()), required=True)