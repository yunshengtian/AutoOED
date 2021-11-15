from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk, scrolledtext


class Entry(ABC):
    '''
    Entry widget with customized get() and set() method
    '''
    def __init__(self, widget, required=False, default=None, readonly=False, valid_check=None, error_msg=None):
        '''
        Input:
            widget: tkinter Entry or Combobox
            required: whether the entry value is required
            default: default value for entry, only works when is not required
            valid_check: function that checks validity of entry value
            error_msg: custom error message to display when valid_check fails
        '''
        self.widget = widget
        self.required = required
        self.default = default
        if self.default is not None:
            self.set(self.default)
        self.readonly = readonly
        self.valid_check = valid_check
        self.error_msg = error_msg

    def config(self, required=None, default=None, readonly=None, valid_check=None, error_msg=None):
        if required is not None:
            self.required = required
        if default is not None:
            self.default = default
            self.set(self.default)
        if readonly is not None:
            self.readonly = readonly
        if valid_check is not None:
            self.valid_check = valid_check
        if error_msg is not None:
            self.error_msg = error_msg

    def enable(self, readonly=None):
        '''
        Enable changing entry value
        '''
        if readonly is None: readonly = self.readonly
        if readonly and self.widget['state'] != 'readonly':
            self.widget.configure(state='readonly')
        elif self.widget['state'] != 'normal':
            self.widget.configure(state='normal')
    
    def disable(self):
        '''
        Disable changing entry value
        '''
        if self.widget['state'] != 'disabled':
            self.widget.configure(state='disabled')

    def get(self):
        '''
        Get entry value
        '''
        val = self.widget.get()
        if val == '':
            result = None if self.required else self.default
        else:
            result = self._get(val)
        if self.required:
            assert result is not None, 'Required value not specified'
        if result is not None and self.valid_check is not None and not self.valid_check(result):
            exception_msg = 'Invalid value'
            if self.error_msg is not None:
                exception_msg += ': ' + self.error_msg
            raise Exception(exception_msg)
        return result

    def set(self, val):
        '''
        Set entry value
        '''
        if val is None:
            new_val = ''
        else:
            new_val = str(self._set(val))
        if type(self.widget) == tk.Entry:
            self.widget.delete(0, tk.END)
            self.widget.insert(0, new_val)
        elif type(self.widget) == scrolledtext.ScrolledText:
            self.widget.delete(1.0, tk.END)
            self.widget.insert(tk.END, new_val)
        else:
            self.widget.set(new_val)

    def select(self):
        '''
        Generate select event
        '''
        if type(self.widget) == ttk.Combobox:
            curr_idx = self.widget['values'].index(self.widget.get()) # NOTE: assume all combobox values are unique
            self.widget.current(curr_idx)
            self.widget.event_generate('<<ComboboxSelected>>')

    @abstractmethod
    def _get(self, val):
        pass

    @abstractmethod
    def _set(self, val):
        pass

    def get_error_msg(self):
        '''
        Get the error message when valid_check fails
        '''
        if self.required and self.widget.get() == '':
            return 'entry cannot be empty'
        else:
            return self.error_msg


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


def get_entry(name, *args, **kwargs):
    '''
    Create entry by name and other arguments
    '''
    factory = {
        'string': StringEntry,
        'int': IntEntry,
        'float': FloatEntry,
        'stringlist': StringListEntry,
        'intlist': IntListEntry,
        'floatlist': FloatListEntry,
    }
    return factory[name](*args, **kwargs)