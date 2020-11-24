import tkinter as tk
from tkinter import messagebox
from system.server.db_team import Database
from .view import WorkerLoginView, WorkerView
from .params import *


class WorkerController:

    def __init__(self):
        self.root_login = tk.Tk()
        self.root_login.title('OpenMOBO - Worker')
        self.root_login.protocol('WM_DELETE_WINDOW', self._quit_login)
        self.root_login.resizable(False, False)
        self.view_login = WorkerLoginView(self.root_login)
        self.bind_command_login()

        self.root = None
        self.view = None
        
        self.database = None
        self.table_name = None

        self.refresh_rate = REFRESH_RATE

        self.table_checksum = None

    def bind_command_login(self):
        '''
        '''
        self.view_login.widget['login'].configure(command=self.login_database)

    def login_database(self):
        '''
        '''
        try:
            ip = self.view_login.widget['ip'].get()
            user = self.view_login.widget['user'].get()
            passwd = self.view_login.widget['passwd'].get()
            table = self.view_login.widget['table'].get()
        except Exception as e:
            messagebox.showinfo('Error', e, parent=self.root_login)
            return

        try:
            self.database = Database(ip, user, passwd)
        except:
            messagebox.showinfo('Error', 'Invalid IP or username or password', parent=self.root_login)
            return

        self.after_login(table_name=table)

    def bind_command(self):
        '''
        '''
        self.view.widget['auto_eval'].configure(state=tk.DISABLED)
        self.view.widget['manual_fill'].configure(state=tk.DISABLED)

    def after_login(self, table_name):
        '''
        Transit from login window to main window
        '''
        self._quit_login()

        self.table_name = table_name
        
        self.root = tk.Tk()
        self.root.title('OpenMOBO - Worker')
        self.root.protocol('WM_DELETE_WINDOW', self._quit)
        self.view = WorkerView(self.root)
        self.bind_command()

        self.root.after(self.refresh_rate, self.refresh)

        tk.mainloop()

    def refresh(self):
        '''
        '''
        self.refresh_table()
        self.root.after(self.refresh_rate, self.refresh)

    def _quit_login(self):
        '''
        Quit handling for login window
        '''
        self.root_login.quit()
        self.root_login.destroy()

    def _quit(self):
        '''
        Quit handling for main window
        '''
        self.root.quit()
        self.root.destroy()

    def run(self):
        tk.mainloop()

    def refresh_table(self):
        '''
        '''
        assert self.table_name is not None
        checksum = self.database.get_checksum(table=self.table_name)
        if checksum == self.table_checksum or checksum == 0: return

        self.table_checksum = checksum

        data = self.database.load_table(name=self.table_name)

        if self.view.widget['db_table'] is None:
            self.database.execute(f'describe {self.table_name}')
            titles = [res[0] for res in self.database.fetchall()]
            self.view.init_db_table(titles)

        self.view.widget['db_table'].update(data)
