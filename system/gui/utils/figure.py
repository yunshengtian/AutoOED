import tkinter as tk
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)


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