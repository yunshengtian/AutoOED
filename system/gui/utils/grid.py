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
