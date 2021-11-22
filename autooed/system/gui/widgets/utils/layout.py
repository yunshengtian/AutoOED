import tkinter as tk


def grid_configure(master, row_list=None, column_list=None, row_weights=None, column_weights=None):
    '''
    Configure spacing expansion for widget when resolution change
    '''
    if type(row_list) == int:
        row_list = list(range(row_list + 1))
    if type(column_list) == int:
        column_list = list(range(column_list + 1))
    if row_list is not None:
        if row_weights is None:
            row_weights = [1] * len(row_list)
        for i, row in enumerate(row_list):
            tk.Grid.rowconfigure(master, row, weight=row_weights[i])
    if column_list is not None:
        if column_weights is None:
            column_weights = [1] * len(column_list)
        for i, column in enumerate(column_list):
            tk.Grid.columnconfigure(master, column, weight=column_weights[i])


def center(window, master=None):
    '''
    Center a tkinter window
    '''
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    if master is None: # screen center
        frm_width = window.winfo_rootx() - window.winfo_x()
        titlebar_height = window.winfo_rooty() - window.winfo_y()
        win_width = width + 2 * frm_width
        win_height = height + titlebar_height + frm_width
        x = window.winfo_screenwidth() // 2 - win_width // 2
        y = window.winfo_screenheight() // 2 - win_height // 2
    else: # master center
        x = master.winfo_x() + master.winfo_width() // 2 - width // 2
        y = master.winfo_y() + master.winfo_height() // 2 - height // 2
    window.withdraw()
    window.geometry('+{}+{}'.format(x, y))
    window.deiconify()
