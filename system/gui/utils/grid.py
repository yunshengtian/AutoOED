import tkinter as tk
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)


def grid_configure(master, row_list, column_list, row_weights=None, column_weights=None):
    '''
    Configure spacing expansion for widget when resolution change
    '''
    if row_weights is None:
        row_weights = [1] * len(row_list)
    if column_weights is None:
        column_weights = [1] * len(column_list)
    for i, row in enumerate(row_list):
        tk.Grid.rowconfigure(master, row, weight=row_weights[i])
    for i, column in enumerate(column_list):
        tk.Grid.columnconfigure(master, column, weight=column_weights[i])


def embed_figure(fig, master, toolbar=True):
    '''
    Embed matplotlib figure in tkinter
    '''
    canvas = FigureCanvasTkAgg(fig, master=master)
    canvas.draw()
    canvas.get_tk_widget().grid(row=0, column=0, sticky='NSEW')

    if toolbar:
        frame_toolbar = tk.Frame(master=master, bg='white')
        frame_toolbar.grid(row=1, column=0, sticky='NSEW')
        toolbar_obj = NavigationToolbar2Tk(canvas, frame_toolbar)
        toolbar_obj.update()