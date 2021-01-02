import numpy as np
import tkinter as tk
from tkinter import messagebox
from system.server.db_team import Database
from system.server.gui.view import ServerLoginView, ServerInitView, ServerView
from system.server.gui.table import CreateTableController, LoadTableController, RemoveTableController
from system.server.gui.access import ManageAdminController, ManageUserController 
from .params import *


class ServerController:

    def __init__(self):
        self.root_login = tk.Tk()
        self.root_login.title('OpenMOBO - Server')
        self.root_login.protocol('WM_DELETE_WINDOW', self._quit_login)
        self.root_login.resizable(False, False)
        self.view_login = ServerLoginView(self.root_login)
        self.bind_command_login()

        self.root_init = None
        self.view_init = None

        self.root = None
        self.view = None
        
        self.database = None
        self.table_name = None
        self.table_checksum = None
        self.problem_info = None

        self.refresh_rate = REFRESH_RATE

        self.active_scientist_user = None
        self.active_scientist_host = None
        self.active_worker_user_list = []
        self.active_worker_host_list = []

    def bind_command_login(self):
        '''
        '''
        self.view_login.widget['login'].configure(command=self.login_database)

    def login_database(self):
        '''
        '''
        try:
            user = self.view_login.widget['user'].get()
            passwd = self.view_login.widget['passwd'].get()
            self.database = Database('localhost', user, passwd)
        except Exception as e:
            messagebox.showinfo('Error', e, parent=self.root_login)
            return

        self.after_login()

    def bind_command_init(self):
        '''
        '''
        self.refresh_info_init()
        self.view_init.widget['refresh'].configure(command=self.refresh_info_init)
        self.view_init.widget['create_table'].configure(command=self.create_table)
        self.view_init.widget['load_table'].configure(command=self.load_table)
        self.view_init.widget['remove_table'].configure(command=self.remove_table)
        self.view_init.widget['manage_admin'].configure(command=self.manage_admin)
        self.view_init.widget['manage_user'].configure(command=self.manage_user)

        if self.database.get_current_user() != 'root':
            self.view_init.widget['create_table'].disable()
            self.view_init.widget['remove_table'].disable()
            self.view_init.widget['manage_admin'].disable()
            self.view_init.widget['manage_user'].disable()

    def refresh_info_init(self):
        '''
        '''
        try:
            user, ip = self.database.get_current_user(return_host=True)
        except Exception as e:
            messagebox.showinfo('Error', e, parent=self.root_init)
            user = self.database.get_current_user()
            ip = 'unknown'
        self.view_init.widget['user'].config(text='Username: ' + user)
        self.view_init.widget['ip'].config(text='IP Address: ' + ip)

    def create_table(self):
        '''
        '''
        CreateTableController(self)
                
    def load_table(self):
        '''
        '''
        LoadTableController(self)

    def remove_table(self):
        '''
        '''
        RemoveTableController(self)

    def manage_admin(self):
        '''
        '''
        ManageAdminController(self)

    def manage_user(self):
        '''
        '''
        ManageUserController(self)

    def bind_command(self):
        '''
        '''
        self.refresh_info()
        self.view.widget['server_refresh'].configure(command=self.refresh_info)

    def refresh_info(self):
        '''
        '''
        try:
            user, ip = self.database.get_current_user(return_host=True)
        except Exception as e:
            messagebox.showinfo('Error', e, parent=self.root_init)
            user = self.database.get_current_user()
            ip = 'unknown'
        self.view.widget['server_user'].config(text='Username: ' + user)
        self.view.widget['server_ip'].config(text='IP Address: ' + ip)

    def after_login(self):
        '''
        Transit from login window to initial window
        '''
        self._quit_login()
        
        self.root_init = tk.Tk()
        self.root_init.title('OpenMOBO - Server')
        self.root_init.protocol('WM_DELETE_WINDOW', self._quit_init)
        self.root_init.resizable(False, False)
        self.view_init = ServerInitView(self.root_init)
        self.bind_command_init()

        tk.mainloop()

    def after_init(self, table_name):
        '''
        Transit from initial window to main window
        '''
        self._quit_init()

        self.table_name = table_name
        
        self.root = tk.Tk()
        self.root.title('OpenMOBO - Server')
        self.root.protocol('WM_DELETE_WINDOW', self._quit)
        self.view = ServerView(self.root)
        self.bind_command()

        self.problem_info = self.database.query_problem(self.table_name)
        self.view.widget['problem_info'].set_info(**self.problem_info)

        self.root.after(self.refresh_rate, self.refresh)

        tk.mainloop()

    def refresh(self):
        '''
        '''
        self.refresh_scientist()
        self.refresh_worker()
        self.refresh_table()
        self.root.after(self.refresh_rate, self.refresh)

    def _quit_login(self):
        '''
        Quit handling for login window
        '''
        self.root_login.quit()
        self.root_login.destroy()

    def _quit_init(self):
        '''
        Quit handling for initial window
        '''
        self.root_init.quit()
        self.root_init.destroy()

    def _quit(self):
        '''
        Quit handling for main window
        '''
        self.root.quit()
        self.root.destroy()

    def run(self):
        tk.mainloop()

    def refresh_scientist(self):
        '''
        '''
        user_list, host_list = self.database.get_active_user_list(return_host=True, role='Scientist')
        
        # TODO: refuse multiple scientist connections

        if self.active_scientist_user is None:
            if user_list == []:
                # offline to offline
                return
            else:
                # offline to online
                self.active_scientist_user = user_list[0]
                self.active_scientist_host = host_list[0]
        else:
            if self.active_scientist_user in user_list:
                # online to online
                return
            else:
                # online to offline
                self.active_scientist_user = None
                self.active_scientist_host = None

        user_label, host_label = self.active_scientist_user, self.active_scientist_host
        if user_label is None: user_label = 'unknown'
        if host_label is None: host_label = 'unknown'
        self.view.widget['sci_user'].config(text='Username: ' + user_label)
        self.view.widget['sci_ip'].config(text='IP Address: ' + host_label)

    def refresh_worker(self):
        '''
        '''
        user_list, host_list = self.database.get_active_user_list(return_host=True, role='Worker')
        if user_list == self.active_worker_user_list and host_list == self.active_worker_host_list: return

        self.active_worker_user_list = user_list
        self.active_worker_host_list = host_list

        # TODO: optimize efficiency
        for i in self.view.widget['worker_disp'].get_children():
            self.view.widget['worker_disp'].delete(i)
        for user, host in zip(user_list, host_list):
            self.view.widget['worker_disp'].insert('', 'end', text=user, values=(host, '', ''))

    def refresh_table(self):
        '''
        '''
        assert self.table_name is not None

        if self.view.widget['db_table'] is None:
            if self.database.check_table_exist(self.table_name):
                self.database.execute(f'describe {self.table_name}')
                columns = [res[0] for res in self.database.fetchall() if res[0] != 'id']
                self.view.init_db_table(columns)
            else:
                return

        checksum = self.database.get_checksum(table=self.table_name)
        if checksum == self.table_checksum or checksum == 0: return
        self.table_checksum = checksum

        data = self.database.load_table(name=self.table_name)
        data = np.array(data, dtype=str)[:, 1:]

        self.view.widget['db_table'].update(columns=None, data=data)
