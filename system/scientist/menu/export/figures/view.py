from system.gui.widgets.factory import create_widget


class MenuExportFiguresView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.window = create_widget('toplevel', master=self.root_view.root_view.root, title='Export Figures')

        self.widget = {}
        self.widget['choice'] = create_widget('radiobutton',
            master=self.window, row=0, column=0, text_list=['Performance Space', 'Selected Design', 'Hypervolume', 'Model Error'], 
            default='Performance Space', orientation='vertical')

        frame_action = create_widget('frame', master=self.window, row=1, column=0, padx=0, pady=0, sticky=None)
        self.widget['export'] = create_widget('button', master=frame_action, row=0, column=0, text='Export')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')