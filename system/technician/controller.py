import numpy as np
import tkinter as tk
from tkinter import messagebox
from problem.common import get_problem_config
from system.params import *
from system.database.team import TeamDatabase
from system.agent import EvaluateAgent
from system.scheduler import EvaluateScheduler
from .view import TechnicianLoginView, TechnicianView

from .auto_set_program import AutoSetProgramController
from .auto_evaluate import AutoEvaluateController
from .manual_lock import ManualLockController
from .manual_fill import ManualFillController


class TechnicianController:

    def __init__(self):
        self.root_login = tk.Tk()
        self.root_login.title(f'{TITLE} - Technician')
        self.root_login.protocol('WM_DELETE_WINDOW', self._quit_login)
        self.root_login.resizable(False, False)
        self.view_login = TechnicianLoginView(self.root_login)
        self.bind_command_login()

        self.root = None
        self.view = None
        
        self.database = None
        self.table_name = None
        self.table_checksum = None
        self.eval_program = None

        self.agent = None

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
            task = self.view_login.widget['task'].get()
        except Exception as e:
            messagebox.showinfo('Error', e, parent=self.root_login)
            return

        try:
            self.database = TeamDatabase(ip, user, passwd)
        except Exception as e:
            messagebox.showinfo('Error', 'Invalid login info: ' + str(e), parent=self.root_login)
            return

        valid_login = self.database.login_verify(name=user, role='Technician', access=task)
        if not valid_login:
            messagebox.showinfo('Error', f'Invalid access to task {task}', parent=self.root_login)
            return

        self.after_login(table_name=task)

    def bind_command(self):
        '''
        '''
        self.view.widget['auto_set_program'].configure(command=self.auto_set_program)
        self.view.widget['auto_evaluate'].configure(command=self.auto_evaluate)
        self.view.widget['manual_lock'].configure(command=self.manual_lock)
        self.view.widget['manual_release'].configure(command=self.manual_release)
        self.view.widget['manual_fill'].configure(command=self.manual_fill)

    def after_login(self, table_name):
        '''
        Transit from login window to main window
        '''
        self._quit_login()

        self.table_name = table_name
        
        self.root = tk.Tk()
        self.root.title(f'{TITLE} - Technician')
        self.root.protocol('WM_DELETE_WINDOW', self._quit)
        self.view = TechnicianView(self.root)
        self.bind_command()
        
        self.agent = EvaluateAgent(self.database, self.table_name)
        self.agent.refresh()
        self.scheduler = EvaluateScheduler(self.agent)

        problem_cfg = self.agent.problem_cfg
        if problem_cfg is not None:
            self.view.widget['problem_info'].set_info(problem_cfg)

        self.root.after(self.refresh_rate, self.refresh)

        tk.mainloop()

    def refresh(self):
        '''
        '''
        self.scheduler.refresh()
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
            if self.agent.check_table_exist():
                columns = self.agent.get_column_names()
                self.view.init_db_table(columns)
                
                self.agent.refresh()
                self.view.widget['problem_info'].set_info(self.agent.problem_cfg)
            else:
                return

        checksum = self.database.get_checksum(table=self.table_name)
        if checksum == self.table_checksum or checksum == 0: return
        self.table_checksum = checksum

        data = self.database.load_table(name=self.table_name, column=self.view.get_table_columns())
        self.view.widget['db_table'].load(data)

    def auto_set_program(self):
        '''
        '''
        AutoSetProgramController(self)

    def set_eval_program(self, program_path):
        '''
        '''
        self.eval_program = program_path
        self.view.widget['auto_evaluate'].enable()

    def load_eval_program(self):
        return self.eval_program

    def auto_evaluate(self):
        '''
        '''
        AutoEvaluateController(self)

    def evaluate(self, eval_func, rowids):
        '''
        '''
        try:
            n_worker = self.view.widget['n_worker'].get()
        except Exception as e:
            tk.messagebox.showinfo('Error', str(e), parent=self.view.root)
            return

        self.scheduler.evaluate(eval_func, rowids, n_worker)

    def manual_lock(self):
        '''
        '''
        ManualLockController(self, lock=True)

    def manual_release(self):
        '''
        '''
        ManualLockController(self, lock=False)

    def check_entry(self, rowid):
        '''
        '''
        return self.database.check_entry(self.table_name, rowid)

    def lock_entry(self, rowid):
        '''
        '''
        if self.database.check_entry(self.table_name, rowid): return False
        try:
            self.database.lock_entry(self.table_name, rowid)
        except:
            return False
        return True

    def release_entry(self, rowid):
        '''
        '''
        if not self.database.check_entry(self.table_name, rowid): return False
        try:
            self.database.release_entry(self.table_name, rowid)
        except:
            return False
        return True

    def manual_fill(self):
        '''
        '''
        ManualFillController(self)

    def update_data(self, Y, rowids):
        '''
        '''
        self.agent.update_evaluation(Y, rowids)