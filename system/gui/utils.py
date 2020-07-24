import tkinter as tk
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)


def gridconfigure(master, row_list, column_list, row_weights=None, column_weights=None):
    '''
    Configure spacing expansion for widget when resolution change
    '''
    if row_weights is None:
        row_weights = [1] * len(row_list)
    if column_weights is None:
        column_weights = [1] * len(column_list)
    for row in row_list:
        tk.Grid.rowconfigure(master, row, weight=row_weights[row])
    for column in column_list:
        tk.Grid.columnconfigure(master, column, weight=column_weights[column])


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
        toolbar_obj.configure(background='white')
        toolbar_obj.update()


class Entry:
    '''
    Entry widget creation tools
    '''
    def __init__(self, widget, valid_check=None):
        self.widget = widget
        self.valid_check = valid_check
    def get(self):
        val = self.widget.get()
        if val == '':
            return None
        result = self._get(val)
        if self.valid_check is not None:
            if not self.valid_check(result):
                raise Exception('Invalid value specified in the entry')
        return result
    def _get(self, val):
        return val

class IntEntry(Entry):
    def _get(self, val):
        return int(val)

class FloatEntry(Entry):
    def _get(self, val):
        return float(val)
        
class FloatListEntry(Entry):
    def _get(self, val):
        return [float(num) for num in val.split(',')]

class StringListEntry(Entry):
    def _get(self, val):
        return val.split(',')