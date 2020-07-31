from abc import abstractmethod
import tkinter as tk
from tkinter import ttk
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


class Entry:
    '''
    Entry widget with customized get() and set() method
    '''
    def __init__(self, widget, valid_check=None):
        self.widget = widget
        self.valid_check = valid_check

    def enable(self):
        self.widget.configure(state=tk.NORMAL)
    
    def disable(self):
        self.widget.configure(state=tk.DISABLED)

    def get(self):
        val = self.widget.get()
        if val == '':
            result = None
        else:
            result = self._get(val)
        if self.valid_check is not None and not self.valid_check(result):
            raise Exception('Invalid value specified in the entry')
        return result

    def set(self, val):
        new_val = str(self._set(val))
        if isinstance(self.widget, tk.Entry):
            self.widget.delete(0, tk.END)
            self.widget.insert(0, new_val)
        else:
            self.widget.set(new_val)

    @abstractmethod
    def _get(self, val):
        pass

    @abstractmethod
    def _set(self, val):
        pass

class StringEntry(Entry):
    '''
    Entry for string
    '''
    def _get(self, val):
        return val

    def _set(self, val):
        return val

class IntEntry(Entry):
    '''
    Entry for integer
    '''
    def _get(self, val):
        return int(val)

    def _set(self, val):
        return int(val)

class FloatEntry(Entry):
    '''
    Entry for float number
    '''
    def _get(self, val):
        return float(val)

    def _set(self, val):
        return float(val)

class StringListEntry(Entry):
    '''
    Entry for list of string
    '''
    def _get(self, val):
        return val.split(',')

    def _set(self, val):
        return ','.join(val)

class IntListEntry(Entry):
    '''
    Entry for list of float number
    '''
    def _get(self, val):
        return [int(num) for num in val.split(',')]

    def _set(self, val):
        return ','.join([str(int(num)) for num in val])

class FloatListEntry(Entry):
    '''
    Entry for list of float number
    '''
    def _get(self, val):
        return [float(num) for num in val.split(',')]

    def _set(self, val):
        return ','.join([str(float(num)) for num in val])


# predefined formatting
entry_width = 5
combobox_width = 10

# widget creation tools
def create_frame(master, row, column, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='NSEW'):
    frame = tk.Frame(master=master, bg='white')
    frame.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return frame

def create_labeled_frame(master, row, column, text, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='NSEW'):
    frame = tk.LabelFrame(master=master, bg='white', text=text)
    frame.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return frame

def create_label(master, row, column, text, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='W'):
    label = tk.Label(master=master, bg='white', text=text)
    label.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)

def create_multiple_label(master, text_list, **kwargs):
    for i, text in enumerate(text_list):
        create_label(master=master, row=i, column=0, text=text, **kwargs)

def create_entry(master, row, column, class_type, width=entry_width, valid_check=None, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='W'):
    entry = tk.Entry(master=master, bg='white', width=width, justify='right')
    entry.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return class_type(entry, valid_check=valid_check)

def create_labeled_entry(master, row, column, text, class_type, width=entry_width, valid_check=None, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='EW'):
    frame = create_frame(master, row, column, rowspan, columnspan, padx, pady, sticky)
    grid_configure(frame, [0], [0, 1])
    label = tk.Label(master=frame, bg='white', text=text + ': ')
    label.grid(row=0, column=0, sticky='W')
    entry = tk.Entry(master=frame, bg='white', width=width, justify='right')
    entry.grid(row=0, column=1, sticky='E')
    return class_type(entry, valid_check=valid_check)

def create_combobox(master, row, column, values, width=combobox_width, valid_check=None, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='W'):
    combobox = ttk.Combobox(master=master, values=values, width=width)
    combobox.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return StringEntry(combobox, valid_check=valid_check)

def create_labeled_combobox(master, row, column, text, values, width=combobox_width, valid_check=None, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='NSEW'):
    frame = create_frame(master, row, column, rowspan, columnspan, padx, pady, sticky)
    grid_configure(frame, [0], [0, 1])
    label = tk.Label(master=frame, bg='white', text=text + ': ')
    label.grid(row=0, column=0, sticky='W')
    combobox = ttk.Combobox(master=frame, values=values, width=width)
    combobox.grid(row=0, column=1, sticky='E')
    return StringEntry(combobox, valid_check=valid_check)

def create_button(master, row, column, text, command=None, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='NSEW'):
    button = tk.Button(master=master, text=text, command=command)
    button.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return button
