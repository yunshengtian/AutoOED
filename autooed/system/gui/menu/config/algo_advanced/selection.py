from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.utils.grid import grid_configure
from autooed.system.gui.map import algo_config_map, algo_value_map


class SelectionView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.widget = {}

        self.frame = create_widget('frame', master=self.root_view.frame_selection, row=3, column=0)
        grid_configure(self.frame, None, 0)
        self.widget['name'] = create_widget('labeled_combobox',
            master=self.frame, row=0, column=0, width=25, text=algo_config_map['selection']['name'], 
            values=list(algo_value_map['selection']['name'].values()), required=True)


class SelectionController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = SelectionView(self.root_view)
