'''
Widget creation helper tools
'''

import tkinter as tk
from tkinter import ttk

from system.gui.utils.button import Button
from system.gui.utils.entry import get_entry
from system.gui.utils.grid import grid_configure


# predefined formatting
entry_width = 5
combobox_width = 10


def create_frame(master, row, column, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='NSEW', bg='white'):
    frame = tk.Frame(master=master, bg=bg)
    frame.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return frame


def create_labeled_frame(master, row, column, text, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='NSEW', bg='white'):
    frame = tk.LabelFrame(master=master, bg=bg, text=text)
    frame.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return frame


def create_label(master, row, column, text, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='W', bg='white'):
    label = tk.Label(master=master, bg=bg, text=text)
    label.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)


def create_entry(master, row, column, class_type, width=entry_width, required=False, default=None, valid_check=None, error_msg=None, changeable=True, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='W', bg='white'):
    entry = tk.Entry(master=master, bg=bg, width=width, justify='right')
    entry.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return get_entry(class_type, entry, required=required, default=default, valid_check=valid_check, error_msg=error_msg, changeable=changeable)


def create_labeled_entry(master, row, column, text, class_type, width=entry_width, required=False, required_mark=True, default=None, valid_check=None, error_msg=None, changeable=True, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='EW', bg='white'):
    frame = create_frame(master, row, column, rowspan, columnspan, padx, pady, sticky, bg)
    grid_configure(frame, [0], [0, 1])
    label_text = text + ' (*): ' if required and required_mark else text + ': '
    label = tk.Label(master=frame, bg=bg, text=label_text)
    label.grid(row=0, column=0, sticky='W')
    entry = tk.Entry(master=frame, bg='white', width=width, justify='right')
    entry.grid(row=0, column=1, sticky='E')
    return get_entry(class_type, entry, required=required, default=default, valid_check=valid_check, error_msg=error_msg, changeable=changeable)


def create_combobox(master, row, column, values, readonly=True, width=combobox_width, required=False, default=None, valid_check=None, error_msg=None, changeable=True, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='W'):
    combobox = ttk.Combobox(master=master, values=values, state='readonly' if readonly else None, width=width)
    combobox.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return get_entry('string', combobox, required=required, default=default, readonly=readonly, valid_check=valid_check, error_msg=error_msg, changeable=changeable)


def create_labeled_combobox(master, row, column, text, values, readonly=True, width=combobox_width, required=False, required_mark=True, default=None, valid_check=None, error_msg=None, changeable=True, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='NSEW', bg='white'):
    frame = create_frame(master, row, column, rowspan, columnspan, padx, pady, sticky, bg)
    grid_configure(frame, [0], [0, 1])
    label_text = text + ' (*): ' if required and required_mark else text + ': '
    label = tk.Label(master=frame, bg=bg, text=label_text)
    label.grid(row=0, column=0, sticky='W')
    combobox = ttk.Combobox(master=frame, values=values, state='readonly' if readonly else None, width=width)
    combobox.grid(row=0, column=1, sticky='E')
    return get_entry('string', combobox, required=required, default=default, readonly=readonly, valid_check=valid_check, error_msg=error_msg, changeable=changeable)


def create_button(master, row, column, text, command=None, 
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='NSEW'):
    button = Button(master=master, text=text, command=command)
    button.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return button


def create_labeled_button_entry(master, row, column, label_text, button_text, command=None, width=entry_width, required=False, required_mark=True, default=None, valid_check=None, error_msg=None, changeable=True,
        rowspan=1, columnspan=1, padx=10, pady=10, sticky='NSEW', bg='white'):
    frame = create_frame(master, row, column, rowspan, columnspan, 0, pady / 2, sticky, bg)
    grid_configure(frame, [0], [1])
    label_text = label_text + ' (*): ' if required and required_mark else label_text + ': '
    label = tk.Label(master=frame, bg=bg, text=label_text)
    label.grid(row=0, column=0, columnspan=2, sticky='W', padx=padx, pady=pady / 2)
    button = Button(master=frame, text=button_text, command=command)
    button.grid(row=1, column=0, padx=padx)
    entry = tk.Entry(master=frame, bg='white', width=width, justify='right')
    entry.grid(row=1, column=1, sticky='EW', padx=padx)
    return button, get_entry('string', entry, required=required, default=default, valid_check=valid_check, error_msg=error_msg, changeable=changeable)


def create_widget(name, *args, **kwargs):
    '''
    Create widget by name and other arguments
    '''
    factory = {
        'frame': create_frame,
        'labeled_frame': create_labeled_frame,
        'label': create_label,
        'entry': create_entry,
        'labeled_entry': create_labeled_entry,
        'combobox': create_combobox,
        'labeled_combobox': create_labeled_combobox,
        'button': create_button,
        'labeled_button_entry': create_labeled_button_entry,
    }
    return factory[name](*args, **kwargs)