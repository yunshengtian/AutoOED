import tkinter as tk
from system.gui.utils.grid import grid_configure
from system.gui.widgets.factory import create_widget
from system.gui.widgets.listbox import Listbox
from system.scientist.map import config_map


class MenuProblemView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.window = tk.Toplevel(master=self.root_view.root)
        self.window.title('Manage Problem')
        self.window.resizable(False, False)

        self.widget = {}

        # problem section
        frame_problem = create_widget('frame', master=self.window, row=0, column=0)
        frame_list = create_widget('labeled_frame', master=frame_problem, row=0, column=0, text='Problem List')
        frame_list_display = create_widget('frame', master=frame_list, row=0, column=0, padx=5, pady=5)
        frame_list_action = create_widget('frame', master=frame_list, row=1, column=0, padx=0, pady=0)
        frame_config = create_widget('labeled_frame', master=frame_problem, row=0, column=1, text='Problem Config')
        frame_config_display = create_widget('frame', master=frame_config, row=0, column=0, padx=0, pady=0)
        frame_config_action = create_widget('frame', master=frame_config, row=1, column=0, padx=0, pady=0, sticky=None)
        
        grid_configure(frame_list, 0, 0)

        # list subsection
        self.widget['problem_list'] = Listbox(master=frame_list_display)
        self.widget['problem_list'].grid()
        
        self.widget['create'] = create_widget('button', master=frame_list_action, row=0, column=0, text='Create')
        self.widget['delete'] = create_widget('button', master=frame_list_action, row=0, column=1, text='Delete')

        # config subsection
        self.widget['name'] = create_widget('labeled_entry', 
            master=frame_config_display, row=0, column=0, text=config_map['problem']['name'], class_type='string', width=15, required=True)
        self.widget['n_var'] = create_widget('labeled_entry', 
            master=frame_config_display, row=1, column=0, text=config_map['problem']['n_var'], class_type='int', required=True)
        self.widget['n_obj'] = create_widget('labeled_entry', 
            master=frame_config_display, row=2, column=0, text=config_map['problem']['n_obj'], class_type='int', required=True)
        self.widget['n_constr'] = create_widget('labeled_entry', 
            master=frame_config_display, row=3, column=0, text=config_map['problem']['n_constr'], class_type='int')

        frame_config_space = tk.Frame(master=frame_config_display)
        frame_config_space.grid(row=4, column=0)
        self.widget['set_design'] = create_widget('button', master=frame_config_space, row=0, column=0, text='Configure design space')
        self.widget['set_performance'] = create_widget('button', master=frame_config_space, row=0, column=1, text='Configure performance space')

        self.widget['browse_obj_eval'], self.widget['disp_obj_eval'] = create_widget('labeled_button_entry',
            master=frame_config_display, row=5, column=0, label_text=config_map['problem']['objective_eval'], button_text='Browse', width=30)
        
        self.widget['browse_constr_eval'], self.widget['disp_constr_eval'] = create_widget('labeled_button_entry',
            master=frame_config_display, row=6, column=0, label_text=config_map['problem']['constraint_eval'], button_text='Browse', width=30)

        self.widget['save'] = create_widget('button', master=frame_config_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_config_action, row=0, column=1, text='Cancel')

        self.cfg_widget = {
            'name': self.widget['name'],
            'n_var': self.widget['n_var'],
            'n_obj': self.widget['n_obj'],
            'n_constr': self.widget['n_constr'],
            'objective_eval': self.widget['disp_obj_eval'],
            'constraint_eval': self.widget['disp_constr_eval'],
        }

    def enable_config_widgets(self):
        '''
        Enable all config widgets
        '''
        for key in ['save', 'cancel', 'set_design', 'set_performance', 'browse_obj_eval', 'browse_constr_eval']:
            self.widget[key].enable()
        for widget in self.cfg_widget.values():
            widget.enable()
            widget.set(None)

    def disable_config_widgets(self):
        '''
        Disable all config widgets
        '''
        for key in ['save', 'cancel', 'set_design', 'set_performance', 'browse_obj_eval', 'browse_constr_eval']:
            self.widget[key].disable()
        for widget in self.cfg_widget.values():
            widget.set(None)
            widget.disable()

    def save_widget_values(self, config):
        '''
        Save values of widgets to config dict
        '''
        temp_config = {}
        for name, widget in self.cfg_widget.items():
            try:
                temp_config[name] = widget.get()
            except:
                error_msg = widget.get_error_msg()
                error_msg = '' if error_msg is None else ': ' + error_msg
                tk.messagebox.showinfo('Error', 'Invalid value for "' + config_map['problem'][name] + '"' + error_msg, parent=self.window)
                raise Exception()
        for key, val in temp_config.items():
            config[key] = val

    def load_widget_values(self, config):
        '''
        Load values of widgets from config dict
        '''
        for name, widget in self.cfg_widget.items():
            widget.set(config[name])
            widget.select()