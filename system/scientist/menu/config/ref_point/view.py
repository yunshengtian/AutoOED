from system.gui.widgets.factory import create_widget
from system.gui.widgets.excel import Excel


class RefPointView:
    
    def __init__(self, root_view, problem_cfg):
        self.root_view = root_view

        self.window = create_widget('toplevel', master=self.root_view.window, title='Set Reference Point')

        self.widget = {}

        frame_ref_point = create_widget('labeled_frame', master=self.window, text='Reference Point', row=0, column=0)
        frame_excel = create_widget('frame', master=frame_ref_point, row=0, column=0)
        self.widget['excel'] = Excel(master=frame_excel, rows=problem_cfg['n_obj'], columns=2, width=15,
            title=['Name', 'Reference Point'], dtype=[str, float])
        self.widget['excel'].grid(row=0, column=0)
        self.widget['excel'].set_column(0, problem_cfg['obj_name'])
        self.widget['excel'].disable_column(0)

        frame_action = create_widget('frame', master=self.window, row=1, column=0, padx=0, pady=0, sticky=None)
        self.widget['save'] = create_widget('button', master=frame_action, text='Save', row=0, column=0)
        self.widget['cancel'] = create_widget('button', master=frame_action, text='Cancel', row=0, column=1)