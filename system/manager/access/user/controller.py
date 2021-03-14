import tkinter as tk
from .model import ManageUserModel
from .view import ManageUserView


class ManageUserController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view_init

        self.user_info = {}

        self.in_creating_user = False
        self.database = self.root_controller.database

        self.model = ManageUserModel(self.database)
        self.view = ManageUserView(self.root_view)

        self.view.widget['user_list'].bind_cmd(reload_cmd=self.database.get_user_list, select_cmd=self.select_user)
        self.view.widget['user_list'].reload()

        self.view.widget['create'].configure(command=self.create_user)
        self.view.widget['delete'].configure(command=self.delete_user)

        self.view.widget['save'].configure(command=self.save_change)
        self.view.widget['cancel'].configure(command=self.cancel_change)
        
        self.view.widget['delete'].disable()
        self.view.disable_info_widgets()

    def exit_creating_user(self):
        '''
        Exit creating user status
        '''
        self.in_creating_user = False
        self.view.widget['create'].enable()
        self.view.widget['user_list'].delete(tk.END)
        self.user_info.clear()

    def save_change(self):
        '''
        Save changes to user
        '''
        if self.in_creating_user:
            # try to save changes
            try:
                name = self.view.widget['name'].get()
            except:
                error_msg = self.view.widget['name'].get_error_msg()
                error_msg = '' if error_msg is None else ': ' + error_msg
                tk.messagebox.showinfo('Error', 'Invalid value for "' + self.view.info_map['name'] + '"' + error_msg, parent=self.view.window)
                return

            if name in self.database.get_user_list():
                tk.messagebox.showinfo('Error', f'User {name} already exists', parent=self.view.window)
                return
            try:
                self.view.save_widget_values(self.user_info)
            except:
                return
            self.model.save_user(self.user_info)
            tk.messagebox.showinfo('Success', f'User {name} saved', parent=self.view.window)
            
            # reload
            self.exit_creating_user()
            self.view.widget['user_list'].reload()
            self.view.widget['user_list'].select(name)
        else:
            curr_idx = self.view.widget['user_list'].curselection()[0]
            old_name = self.view.widget['user_list'].get(curr_idx)
            if_save = tk.messagebox.askquestion('Save Changes', f'Are you sure to save the changes to user "{old_name}"?', parent=self.view.window)

            if if_save == 'yes':
                # try to save changes
                new_name = self.view.widget['name'].get()
                if old_name != new_name: # problem name changed
                    if new_name in self.database.get_user_list():
                        tk.messagebox.showinfo('Error', f'User {new_name} already exists', parent=self.view.window)
                        return
                try:
                    self.view.save_widget_values(self.user_info)
                except:
                    return
                if old_name != new_name:
                    self.model.remove_user(old_name)
                self.model.save_user(self.user_info)
                tk.messagebox.showinfo('Success', f'User {self.user_info["name"]} saved', parent=self.view.window)

                # reload
                self.view.widget['user_list'].reload()
                self.view.widget['user_list'].select(new_name)
            else:
                # cancel changes
                return

    def cancel_change(self):
        '''
        Cancel changes to user
        '''
        if self.in_creating_user:
            self.exit_creating_user()
            self.view.disable_info_widgets()
        self.view.widget['user_list'].select_event()
        self.user_info.clear()

    def create_user(self):
        '''
        Create new user
        '''
        self.in_creating_user = True
        
        self.view.widget['user_list'].insert(tk.END, '')
        self.view.widget['user_list'].select_clear(0, tk.END)
        self.view.widget['user_list'].select_set(tk.END)

        self.view.enable_info_widgets()
        self.view.widget['access'].widget.config(values=self.database.get_table_list() + ['*', ''])
        self.view.widget['create'].disable()
        self.view.widget['delete'].disable()
        self.user_info.clear()

    def delete_user(self):
        '''
        Delete selected user # TODO: also stop evaluations from the user side
        '''
        index = int(self.view.widget['user_list'].curselection()[0])
        name = self.view.widget['user_list'].get(index)
        if_delete = tk.messagebox.askquestion('Delete User', f'Are you sure to delete user "{name}"?', parent=self.view.window)
        if if_delete == 'yes':
            self.view.widget['user_list'].delete(index)
            listbox_size = self.view.widget['user_list'].size()
            if listbox_size == 0:
                self.view.widget['delete'].disable()
                self.view.disable_info_widgets()
            else:
                self.view.widget['user_list'].select_set(min(index, listbox_size - 1))
                self.view.widget['user_list'].select_event()
            self.model.remove_user(name)
        else:
            return
        self.user_info.clear()

    def select_user(self, event):
        '''
        Select user, load user info
        '''
        try:
            index = int(event.widget.curselection()[0])
        except:
            return
        name = event.widget.get(index)
        if name == '':
            return
        elif self.in_creating_user:
            self.exit_creating_user()

        self.view.enable_info_widgets()
        self.view.widget['access'].widget.config(values=self.database.get_table_list() + ['*', ''])
        info = self.model.load_user(name)
        self.view.load_widget_values(info)
        self.view.widget['name'].disable()

        self.view.widget['delete'].enable()
        self.user_info.clear()
        self.user_info.update(info)