import numpy as np
import tkinter as tk
from tkinter import messagebox
from system.server.db_team import Database
from .view import WorkerLoginView, WorkerView
from .params import *

from .auto_set_script import AutoSetScriptController
from .auto_evaluate import AutoEvaluateController
from .manual_lock import ManualLockController
from .manual_fill import ManualFillController


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
        self.table_checksum = None
        self.problem_info = None
        self.eval_script = {
            'p_path': None,
            'c_path': None,
        }

        self.refresh_rate = REFRESH_RATE

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
        except Exception as e:
            messagebox.showinfo('Error', 'Invalid login info: ' + str(e), parent=self.root_login)
            return

        valid_login = self.database.login_verify(name=user, role='Worker', access=table)
        if not valid_login:
            messagebox.showinfo('Error', f'Invalid access to table {table}', parent=self.root_login)
            return

        self.after_login(table_name=table)

    def bind_command(self):
        '''
        '''
        self.view.widget['auto_set_script'].configure(command=self.auto_set_script)

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

        self.problem_info = self.database.query_problem(self.table_name)
        self.view.widget['problem_info'].set_info(**self.problem_info)

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

        if self.view.widget['db_table'] is None:
            if self.database.check_table_exist(self.table_name):
                self.database.execute(f'describe {self.table_name}')
                columns = [res[0] for res in self.database.fetchall() if res[0] != 'id']
                self.view.init_db_table(columns)
                self.problem_info = self.database.query_problem(self.table_name)
                self.view.widget['problem_info'].set_info(**self.problem_info)
            else:
                return

        checksum = self.database.get_checksum(table=self.table_name)
        if checksum == self.table_checksum or checksum == 0: return
        self.table_checksum = checksum

        data = self.database.load_table(name=self.table_name)
        data = np.array(data, dtype=str)[:, 1:]

        self.view.widget['db_table'].update(columns=None, data=data)

    def auto_set_script(self):
        '''
        '''
        AutoSetScriptController(self)

    def set_eval_script(self, p_path, c_path):
        '''
        '''
        self.eval_script = {
            'p_path': p_path,
            'c_path': c_path
        }
        self.view.widget['auto_eval'].configure(state=tk.NORMAL)

    def load_eval_script(self):
        return self.eval_script['p_path'], self.eval_script['c_path']