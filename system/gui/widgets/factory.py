'''
Widget creation helper tools
'''

import tkinter as tk
from tkinter import ttk, scrolledtext

from system.gui.widgets.button import Button
from system.gui.widgets.entry import get_entry
from system.gui.widgets.variable import get_variable
from system.gui.utils.grid import grid_configure

from system.params import LOGO_WIDTH, LOGO_HEIGHT
from system.utils.path import get_logo_path
from system.gui.widgets.image import StaticImageFrame


# predefined formatting
padx = 10
pady = 10
combobox_width = 10
entry_width = 5


def create_logo(master, row, column, rowspan=1, columnspan=1, padx=padx, pady=pady, sticky='NSEW'):
    image_logo = StaticImageFrame(master=master, img_path=get_logo_path(), width=LOGO_WIDTH, height=LOGO_HEIGHT)
    image_logo.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return image_logo


def create_label(master, row, column, text, 
        rowspan=1, columnspan=1, padx=padx, pady=pady, sticky='W'):
    label = tk.Label(master=master, text=text)
    label.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return label
    

def create_frame(master, row, column, 
        rowspan=1, columnspan=1, padx=padx, pady=pady, sticky='NSEW'):
    frame = tk.Frame(master=master)
    frame.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return frame


def create_combobox(master, row, column, values, class_type='string', readonly=True, width=combobox_width, required=False, default=None, valid_check=None, error_msg=None,  
        rowspan=1, columnspan=1, padx=padx, pady=pady, sticky='W'):
    combobox = ttk.Combobox(master=master, values=values, state='readonly' if readonly else None, width=width, justify='right')
    combobox.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return get_entry(class_type, combobox, required=required, default=default, readonly=readonly, valid_check=valid_check, error_msg=error_msg)


def create_button(master, row, column, text, command=None, 
        rowspan=1, columnspan=1, padx=padx, pady=pady, sticky='NSEW'):
    button = Button(master=master, text=text, command=command)
    button.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return button


def create_entry(master, row, column, class_type, width=entry_width, required=False, default=None, valid_check=None, error_msg=None, 
        rowspan=1, columnspan=1, padx=padx, pady=pady, sticky='W'):
    entry = tk.Entry(master=master, width=width, justify='right')
    entry.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return get_entry(class_type, entry, required=required, default=default, valid_check=valid_check, error_msg=error_msg)


def create_checkbutton(master, row, column, text,
        rowspan=1, columnspan=1, padx=padx, pady=pady, sticky=None, return_label=False):
    frame = create_frame(master, row, column, rowspan, columnspan, padx, pady, sticky)
    var = tk.IntVar()
    checkbutton = tk.Checkbutton(master=frame, variable=var, highlightthickness=0, bd=0)
    checkbutton.grid(row=0, column=0)
    label = tk.Label(master=frame, text=text)
    label.grid(row=0, column=1)
    variable = get_variable('checkbutton', var, checkbutton)
    if return_label:
        return label, variable
    else:
        return variable


def create_radiobutton(master, row, column, text_list, default=None, orientation='horizontal',
        rowspan=1, columnspan=1, padx=padx, pady=pady, sticky=None):
    assert orientation in ['horizontal', 'vertical']
    frame = create_frame(master, row, column, rowspan, columnspan, padx, pady, sticky)
    var = tk.StringVar(master=None, value=default)
    buttons = {}
    for i, text in enumerate(text_list):
        button = ttk.Radiobutton(master=frame, text=text, variable=var, value=text)
        if orientation == 'horizontal':
            button.grid(row=0, column=i)
        elif orientation == 'vertical':
            button.grid(row=1, column=0)
        buttons[text] = button
    variable = get_variable('radiobutton', var, buttons)
    return variable


def create_spinbox(master, row, column, text, from_, to, width=entry_width,
        rowspan=1, columnspan=1, padx=padx, pady=pady, sticky=None, return_label=False):
    frame = create_frame(master, row, column, rowspan, columnspan, padx, pady, sticky)
    label = tk.Label(master=frame, text=text)
    label.grid(row=0, column=0)
    var = tk.IntVar()
    spinbox = tk.Spinbox(master=frame, from_=from_, to=to, width=width, textvariable=var)
    spinbox.grid(row=0, column=1, padx=padx)
    variable = get_variable('spinbox', var, spinbox)
    if return_label:
        return label, variable
    else:
        return variable


def create_labeled_frame(master, row, column, text, 
        rowspan=1, columnspan=1, padx=padx, pady=pady, sticky='NSEW'):
    frame = tk.LabelFrame(master=master, text=text)
    frame.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    return frame


def create_labeled_combobox(master, row, column, text, values=None, class_type='string', readonly=True, width=combobox_width, justify='right', required=False, required_mark=True, default=None, valid_check=None, error_msg=None, 
        rowspan=1, columnspan=1, padx=padx, pady=pady, sticky='NSEW', return_label=False):
    frame = create_frame(master, row, column, rowspan, columnspan, padx, pady, sticky)
    grid_configure(frame, [0], [0, 1])
    label_text = text + ' (*): ' if required and required_mark else text + ': '
    label = tk.Label(master=frame, text=label_text)
    label.grid(row=0, column=0, sticky='W')
    combobox = ttk.Combobox(master=frame, values=values, state='readonly' if readonly else None, width=width, justify=justify)
    combobox.grid(row=0, column=1, sticky='E')
    entry = get_entry(class_type, combobox, required=required, default=default, readonly=readonly, valid_check=valid_check, error_msg=error_msg)
    if return_label:
        return label, entry
    else:
        return entry


def create_labeled_button(master, row, column, label_text, button_text, command=None, required=False, required_mark=True,
        rowspan=1, columnspan=1, padx=padx, pady=pady, sticky='NSEW', return_label=False):
    frame = create_frame(master, row, column, rowspan, columnspan, padx, pady, sticky)
    grid_configure(frame, [0], [0, 1])
    label_text = label_text + ' (*): ' if required and required_mark else label_text + ': '
    label = tk.Label(master=frame, text=label_text)
    label.grid(row=0, column=0, sticky='W')
    button = Button(master=frame, text=button_text, command=command)
    button.grid(row=0, column=1, sticky='E')
    if return_label:
        return label, button
    else:
        return button


def create_labeled_entry(master, row, column, text, class_type, width=entry_width, required=False, required_mark=True, default=None, valid_check=None, error_msg=None,  
        rowspan=1, columnspan=1, padx=padx, pady=pady, sticky='EW', return_label=False):
    frame = create_frame(master, row, column, rowspan, columnspan, padx, pady, sticky)
    grid_configure(frame, [0], [0, 1])
    label_text = text + ' (*): ' if required and required_mark else text + ': '
    label = tk.Label(master=frame, text=label_text)
    label.grid(row=0, column=0, sticky='W')
    entry = tk.Entry(master=frame, width=width, justify='right')
    entry.grid(row=0, column=1, sticky='E')
    entry = get_entry(class_type, entry, required=required, default=default, valid_check=valid_check, error_msg=error_msg)
    if return_label:
        return label, entry
    else:
        return entry


def create_labeled_button_entry(master, row, column, label_text, button_text, command=None, width=entry_width, required=False, required_mark=True, default=None, valid_check=None, error_msg=None,
        rowspan=1, columnspan=1, padx=padx, pady=pady, sticky='NSEW', return_label=False):
    frame = create_frame(master, row, column, rowspan, columnspan, 0, pady / 2, sticky)
    grid_configure(frame, [0], [1])
    label_text = label_text + ' (*): ' if required and required_mark else label_text + ': '
    label = tk.Label(master=frame, text=label_text)
    label.grid(row=0, column=0, columnspan=2, sticky='W', padx=padx, pady=pady / 2)
    button = Button(master=frame, text=button_text, command=command)
    button.grid(row=1, column=0, padx=padx)
    entry = tk.Entry(master=frame, width=width, justify='right')
    entry.grid(row=1, column=1, sticky='EW', padx=padx)
    entry = get_entry('string', entry, required=required, default=default, valid_check=valid_check, error_msg=error_msg)
    if return_label:
        return label, button, entry
    else:
        return button, entry


def create_labeled_text(master, row, column, text, width, height, rowspan=1, columnspan=1, padx=padx, pady=pady, sticky='NSEW', return_label=False):
    frame = create_frame(master, row, column, rowspan, columnspan, padx, pady, sticky)
    label_text = text + ':'
    label = tk.Label(master=frame, text=label_text)
    label.grid(row=0, column=0, sticky='W')
    scrtext = scrolledtext.ScrolledText(master=frame, width=width, height=height)
    scrtext.grid(row=1, column=0, pady=pady / 2, sticky='EW')
    entry = get_entry('string', scrtext)
    if return_label:
        return label, entry
    else:
        return entry


def create_widget(name, *args, **kwargs):
    '''
    Create widget by name and other arguments
    '''
    factory = {
        'logo': create_logo,
        'label': create_label,
        'frame': create_frame,
        'combobox': create_combobox,
        'button': create_button,
        'entry': create_entry,
        'checkbutton': create_checkbutton,
        'radiobutton': create_radiobutton,
        'spinbox': create_spinbox,
        'labeled_frame': create_labeled_frame,
        'labeled_combobox': create_labeled_combobox,
        'labeled_button': create_labeled_button,
        'labeled_entry': create_labeled_entry,
        'labeled_button_entry': create_labeled_button_entry,
        'labeled_text': create_labeled_text,
    }
    return factory[name](*args, **kwargs)


def show_widget_error(master, widget, name):
    '''
    Show error messagebox if value of widget is not valid
    '''
    error_msg = widget.get_error_msg()
    error_msg = '' if error_msg is None else ': ' + error_msg
    tk.messagebox.showinfo('Error', f'Invalid value for "{name}"' + error_msg, parent=master)