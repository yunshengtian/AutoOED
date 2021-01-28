from system.gui.widgets.factory import create_widget


class ProblemInfoWidget:

    def __init__(self, master, row, column):
        self.desc = {
            'name': 'Name',
            'type': 'Variable type',
            'n_var': 'Number of variables',
            'n_obj': 'Number of objectives',
            'n_constr': 'Number of constraints',
            'obj_type': 'Type of objectives',
        }
        self.widget = {}
        frame_info = create_widget('labeled_frame', master=master, row=row, column=column, text='Problem Info')
        create_widget('label', master=frame_info, row=0, column=0, pady=0, text='')
        for row, key in enumerate(self.desc.keys()):
            self.widget[key] = create_widget('label', master=frame_info, row=row + 1, column=0, pady=5, text=f'{self.desc[key]}: unknown')
        create_widget('label', master=frame_info, row=7, column=0, pady=0, text='')

    def set_info(self, problem_cfg):
        '''
        '''
        for key in self.desc:
            if problem_cfg[key] is not None:
                self.widget[key].config(text=f'{self.desc[key]}: {problem_cfg[key]}')
            else:
                self.widget[key].config(text=f'{self.desc[key]}: unknown')

    def update_info(self, problem_cfg):
        '''
        '''
        for key in self.desc:
            if problem_cfg[key] is not None:
                self.widget[key].config(text=f'{self.desc[key]}: {problem_cfg[key]}')

    def clear_info(self):
        '''
        '''
        for key, widget in self.widget.items():
            widget.config(text=f'{self.desc[key]}: unknown')