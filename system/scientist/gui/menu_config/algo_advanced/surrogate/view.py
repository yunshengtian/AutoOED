from system.gui.widgets.factory import create_widget
from system.gui.utils.grid import grid_configure
from system.scientist.gui.map import algo_config_map, algo_value_map


class SurrogateView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.widget = {}
        self.label = {}

        self.frame = create_widget('frame', master=self.root_view.frame_surrogate, row=0, column=0)
        grid_configure(self.frame, None, 0)
        
        self.widget['name'] = create_widget('labeled_combobox',
            master=self.frame, row=0, column=0, width=20, text=algo_config_map['surrogate']['name'], 
            values=list(algo_value_map['surrogate']['name'].values()), required=True)

        self.create_frame_param()

        self.curr_name = None

        self.activate = {
            'Gaussian Process': self.activate_gp,
            'Thompson Sampling': self.activate_ts,
            'Neural Network': self.activate_nn,
        }
        self.deactivate = {
            'Gaussian Process': self.deactivate_gp,
            'Thompson Sampling': self.deactivate_ts,
            'Neural Network': self.deactivate_nn,
        }

    def create_frame_param(self):
        self.frame_param = create_widget('frame', master=self.frame, row=1, column=0, padx=0, pady=0, sticky='NSEW')
        grid_configure(self.frame_param, None, 0)

    def select(self, name):
        if name == self.curr_name: return
        if self.curr_name is not None:
            self.deactivate[self.curr_name]()
            self.frame_param.destroy()
            self.create_frame_param()
        self.activate[name]()
        self.curr_name = name

    def activate_gp(self):
        self.label['nu'], self.widget['nu'] = create_widget('labeled_combobox',
            master=self.frame_param, row=0, column=0, width=5, text=algo_config_map['surrogate']['nu'], values=[1, 3, 5, -1], class_type='int', return_label=True,
            default=5)

    def deactivate_gp(self):
        for key in ['nu']:
            self.label.pop(key)
            self.widget.pop(key)

    def activate_ts(self):
        self.label['nu'], self.widget['nu'] = create_widget('labeled_combobox',
            master=self.frame_param, row=0, column=0, width=5, text=algo_config_map['surrogate']['nu'], values=[1, 3, 5, -1], class_type='int', return_label=True,
            default=5)
        self.label['n_spectral_pts'], self.widget['n_spectral_pts'] = create_widget('labeled_entry',
            master=self.frame_param, row=1, column=0, text=algo_config_map['surrogate']['n_spectral_pts'], class_type='int', return_label=True,
            default=100, valid_check=lambda x: x > 0, error_msg='number of spectral sampling points must be positive')
        self.label['mean_sample'], self.widget['mean_sample'] = create_widget('checkbutton',
            master=self.frame_param, row=2, column=0, text=algo_config_map['surrogate']['mean_sample'], return_label=True)

    def deactivate_ts(self):
        for key in ['nu', 'n_spectral_pts', 'mean_sample']:
            self.label.pop(key)
            self.widget.pop(key)

    def activate_nn(self):
        self.label['hidden_sizes'], self.widget['hidden_sizes'] = create_widget('labeled_entry',
            master=self.frame_param, row=0, column=0, text=algo_config_map['surrogate']['hidden_sizes'], class_type='intlist', return_label=True,
            default=[50, 50, 50], valid_check=lambda x: all([s > 0 for s in x]), error_msg='all layer sizes must be positive')
        self.label['activation'], self.widget['activation'] = create_widget('labeled_combobox',
            master=self.frame_param, row=1, column=0, text=algo_config_map['surrogate']['activation'], values=['tanh', 'relu'], class_type='string', return_label=True,
            default='tanh')
        self.label['lr'], self.widget['lr'] = create_widget('labeled_entry',
            master=self.frame_param, row=2, column=0, text=algo_config_map['surrogate']['lr'], class_type='float', return_label=True,
            default=1e-3, valid_check=lambda x: x > 0, error_msg='learning rate must be positive')
        self.label['n_epoch'], self.widget['n_epoch'] = create_widget('labeled_entry',
            master=self.frame_param, row=3, column=0, text=algo_config_map['surrogate']['n_epoch'], class_type='int', return_label=True,
            default=100, valid_check=lambda x: x > 0, error_msg='number of epoch must be positive')
        
    def deactivate_nn(self):
        for key in ['hidden_sizes', 'activation', 'lr', 'n_epoch']:
            self.label.pop(key)
            self.widget.pop(key)