import tkinter as tk
import numpy as np


class Excel(tk.Frame):
    '''
    Excel-like table in tkinter gui, with column-based structure
    '''
    def __init__(self, master, rows, columns, width, title=None, dtype=None, default=None, required=None, required_mark=None, valid_check=None):
        '''
        Input:
            rows: number of rows
            columns: number of columns
            width: entry width
            title: titles of each column
            dtype: data types of each column
            default: default values of each column
            required: whether values of each column are required
            valid_check: functions that check the validity of each column
        '''
        super().__init__(master)
        self.n_row = rows
        self.n_column = columns
        self.width = width
        self.entries = [[None for _ in range(self.n_column)] for _ in range(self.n_row)]
        self.title = title

        self.config(default=default, required=required, required_mark=required_mark, valid_check=valid_check)

        # make titles
        if self.title is not None:
            for column in range(self.n_column):
                column_name = self.title[column]
                if self.required[column] and self.required_mark:
                    column_name += ' (*)'
                self._make_entry(0, column + 1, self.width, column_name, False) 

        # make entries
        for row in range(self.n_row):
            for column in range(self.n_column):
                self.entries[row][column] = self._make_entry(row + 1, column + 1, self.width, '', True)

        # set data types
        if dtype is None:
            self.dtype = [str] * self.n_column
        else:
            assert len(dtype) == self.n_column
            self.dtype = dtype

    def config(self, default=None, required=None, required_mark=None, valid_check=None):
        # set default values
        if default is None:
            self.default = [None] * self.n_column
        else:
            assert len(default) == self.n_column
            self.default = default

        # set required flags
        if required is None:
            self.required = [False] * self.n_column
        else:
            if type(required) == bool:
                self.required = [required] * self.n_column
            else:
                assert len(required) == self.n_column
                self.required = required
            
        # set required mark flags
        if required_mark is None:
            self.required_mark = True
        elif required_mark == False:
            self.required_mark = False

        # set validity check functions
        if valid_check is None:
            self.valid_check = [None] * self.n_column
        else:
            assert len(valid_check) == self.n_column
            self.valid_check = valid_check

    def _make_entry(self, row, column, width, text, state):
        entry = tk.Entry(self, width=width)
        if text: entry.insert(0, text)
        entry['state'] = 'normal' if state else 'readonly'
        entry.coords = (row - 1, column - 1)
        entry.grid(row=row, column=column)
        return entry

    def get(self, row, column):
        val = self.entries[row][column].get()
        column_name = f'"{self.title[column]}"' if self.title is not None else f'column {column}'
        if val == '':
            if self.required[column]:
                raise Exception(f'Required value for {column_name} not specified')
            else:
                result = self.default[column]
        else:
            try:
                if self.dtype[column] == bool:
                    val = val.lower()
                    assert val in ['true', 'false', '1', '0']
                    result = bool(val == 'true' or val == '1')
                else:
                    result = self.dtype[column](val)
            except:
                raise Exception(f'Invalid value specified in the entry of {column_name}')
        if self.valid_check[column] is not None and not self.valid_check[column](result):
            raise Exception(f'Invalid value specified in the entry of {column_name}')
        return result

    def get_row(self, row):
        return [self.get(row, column) for column in range(self.n_column)]

    def get_column(self, column):
        return [self.get(row, column) for row in range(self.n_row)]

    def get_all(self):
        return [[self.get(row, column) for column in range(self.n_column)] for row in range(self.n_row)]
    
    def get_grid(self, row_start=None, row_end=None, column_start=None, column_end=None):
        if row_start is None: row_start = 0
        if row_end is None: row_end = self.n_row - 1
        if column_start is None: column_start = 0
        if column_end is None: column_end = self.n_column - 1
        return [[self.get(row, column) for column in range(column_start, column_end + 1)] for row in range(row_start, row_end + 1)]

    def set(self, row, column, val):
        if val is None: return
        self.entries[row][column].delete(0, tk.END)
        self.entries[row][column].insert(0, str(val))

    def set_row(self, row, val):
        if val is None: return
        if type(val) not in [list, np.ndarray]:
            val = [val] * self.n_column
        for column, v in enumerate(val):
            self.set(row, column, v)
    
    def set_column(self, column, val):
        if val is None: return
        if type(val) not in [list, np.ndarray]:
            val = [val] * self.n_row
        for row, v in enumerate(val):
            self.set(row, column, v)

    def set_all(self, val):
        if val is None: return
        if type(val) not in [list, np.ndarray]:
            val = [[val] * self.n_column] * self.n_row
        for row, v_row in enumerate(val):
            for column, v in enumerate(v_row):
                self.set(row, column, v)

    def enable(self, row, column):
        self.entries[row][column].configure(state='normal')

    def enable_row(self, row):
        for column in range(self.n_column):
            self.enable(row, column)

    def enable_column(self, column):
        for row in range(self.n_row):
            self.enable(row, column)

    def disable(self, row, column):
        self.entries[row][column].configure(state='readonly')

    def disable_row(self, row):
        for column in range(self.n_column):
            self.disable(row, column)

    def disable_column(self, column):
        for row in range(self.n_row):
            self.disable(row, column)

    def update_n_row(self, n_row):
        # remove existing entries
        for row in range(self.n_row):
            for column in range(self.n_column):
                self.entries[row][column].grid_remove()

        self.n_row = n_row
        self.entries = [[None for _ in range(self.n_column)] for _ in range(self.n_row)]

        # make entries
        for row in range(self.n_row):
            for column in range(self.n_column):
                self.entries[row][column] = self._make_entry(row + 1, column + 1, self.width, '', True)