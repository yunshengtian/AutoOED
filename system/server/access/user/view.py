import tkinter as tk
from system.gui.utils.grid import grid_configure
from system.gui.widgets.factory import create_widget
from system.gui.widgets.listbox import Listbox


class ManageUserView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.window = tk.Toplevel(master=self.root_view.root)
        self.window.title('Manage User Access')
        self.window.resizable(False, False)

        self.widget = {}

        # problem section
        frame_user = create_widget('frame', master=self.window, row=0, column=0)
        frame_list = create_widget('labeled_frame', master=frame_user, row=0, column=0, text='User List')
        frame_list_display = create_widget('frame', master=frame_list, row=0, column=0, padx=5, pady=5)
        frame_list_action = create_widget('frame', master=frame_list, row=1, column=0, padx=0, pady=0)
        frame_info = create_widget('labeled_frame', master=frame_user, row=0, column=1, text='User Information')
        frame_info_display = create_widget('frame', master=frame_info, row=0, column=0, padx=0, pady=0)
        frame_info_action = create_widget('frame', master=frame_info, row=1, column=0, padx=0, pady=0, sticky=None)
        
        grid_configure(frame_list, 0, 0)

        # list subsection
        self.widget['user_list'] = Listbox(master=frame_list_display)
        self.widget['user_list'].grid()
        
        self.widget['create'] = create_widget('button', master=frame_list_action, row=0, column=0, text='Create')
        self.widget['delete'] = create_widget('button', master=frame_list_action, row=0, column=1, text='Delete')

        # info subsection
        self.widget['name'] = create_widget('labeled_entry', 
            master=frame_info_display, row=0, column=0, text='Username', class_type='string', width=15, required=True)
        self.widget['passwd'] = create_widget('labeled_entry', 
            master=frame_info_display, row=1, column=0, text='Password', class_type='string', width=15, required=True)
        self.widget['role'] = create_widget('labeled_combobox',
            master=frame_info_display, row=2, column=0, text='Role', values=['Scientist', 'Worker'], width=15, required=True)
        self.widget['access'] = create_widget('labeled_combobox',
            master=frame_info_display, row=3, column=0, text='Task access', width=15, required=True)

        self.widget['save'] = create_widget('button', master=frame_info_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_info_action, row=0, column=1, text='Cancel')

        self.info_map = {
            'name': 'username',
            'passwd': 'password'
        }

        self.info_widget = {
            'name': self.widget['name'],
            'passwd': self.widget['passwd'],
            'role': self.widget['role'],
            'access': self.widget['access'],
        }

    def enable_info_widgets(self):
        '''
        Enable all info widgets
        '''
        for key in ['save', 'cancel']:
            self.widget[key].enable()
        for widget in self.info_widget.values():
            widget.enable()
            widget.set(None)

    def disable_info_widgets(self):
        '''
        Disable all info widgets
        '''
        for key in ['save', 'cancel']:
            self.widget[key].disable()
        for widget in self.info_widget.values():
            widget.set(None)
            widget.disable()

    def save_widget_values(self, info):
        '''
        Save values of widgets to info dict
        '''
        temp_info = {}
        for name, widget in self.info_widget.items():
            try:
                temp_info[name] = widget.get()
            except:
                error_msg = widget.get_error_msg()
                error_msg = '' if error_msg is None else ': ' + error_msg
                tk.messagebox.showinfo('Error', 'Invalid value for "' + self.info_map[name] + '"' + error_msg, parent=self.window)
                raise Exception()
        for key, val in temp_info.items():
            info[key] = val

    def load_widget_values(self, info):
        '''
        Load values of widgets from info dict
        '''
        for name, widget in self.info_widget.items():
            widget.set(info[name])
            widget.select()