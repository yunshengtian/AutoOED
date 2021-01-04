import tkinter as tk
from .view import ManualLockView


class ManualLockController:

    def __init__(self, root_controller, lock):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.lock = lock

        self.view = ManualLockView(self.root_view, self.lock)

        self.view.widget['disp_n_row'].config(
            default=1, 
            valid_check=lambda x: x > 0, 
            error_msg='number of rows must be positive',
        )
        self.view.widget['disp_n_row'].set(1)
        self.view.widget['set_n_row'].configure(command=self.update_table)

        table = self.root_controller.view.widget['db_table']
        self.view.widget['rowid_excel'].config(
            valid_check=[lambda x: x > 0 and x <= table.n_rows]
        )
        
        self.view.widget['start'].configure(command=self.change_entry_lock)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def update_table(self):
        '''
        Update excel table of rowids to be evaluated
        '''
        n_row = self.view.widget['disp_n_row'].get()
        self.view.widget['rowid_excel'].update_n_row(n_row)

    def change_entry_lock(self):
        '''
        '''
        try:
            rowids = self.view.widget['rowid_excel'].get_column(0)
        except:
            tk.messagebox.showinfo('Error', 'Invalid row numbers', parent=self.view.window)
            return

        success_rowids = []
        failed_rowids = []

        for rowid in rowids:
            success = self.root_controller.lock_entry(rowid) if self.lock else self.root_controller.release_entry(rowid)
            if success:
                success_rowids.append(rowid)
            else:
                failed_rowids.append(rowid)

        action = 'lock' if self.lock else 'release'
        action_past = 'locked' if self.lock else 'released'
        if len(failed_rowids) == 0:
            tk.messagebox.showinfo('Done', f'Successfully {action_past} all rows requested', parent=self.view.window)
        elif len(success_rowids) == 0:
            tk.messagebox.showinfo('Done', f'Failed to {action} all rows requested', parent=self.view.window)
        else:
            tk.messagebox.showinfo('Done', f'Successfully {action_past} rows [{",".join(success_rowids)}], but failed to {action} rows [{",".join(failed_rowids)}]')

        self.view.window.destroy()