import tkinter as tk


class Excel(tk.Frame):
    '''
    Excel-like table in tkinter gui, with column-based structure
    '''
    def __init__(self, master, rows, columns, width, title=None, dtype=None, default=None, required=None, valid_check=None):
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

        # make titles
        if title is not None:
            for column in range(self.n_column):
                self._make_entry(0, column + 1, self.width, title[column], False) 

        # make entries
        for row in range(self.n_row):
            for column in range(self.n_column):
                self.entries[row][column] = self._make_entry(row + 1, column + 1, self.width, '', True)

        # set data types
        if dtype is None:
            self.dtype = [str for _ in range(self.n_column)]
        else:
            assert len(dtype) == self.n_column
            self.dtype = dtype

        # set default values
        if default is None:
            self.default = [None for _ in range(self.n_column)]
        else:
            assert len(default) == self.n_column
            self.default = default

        # set required flags
        if required is None:
            self.required = [False for _ in range(self.n_column)]
        else:
            assert len(required) == self.n_column
            self.required = required

        # set validity check functions
        if valid_check is None:
            self.valid_check = [None for _ in range(self.n_column)]
        else:
            assert len(valid_check) == self.n_column
            self.valid_check = valid_check

    def _make_entry(self, row, column, width, text, state):
        entry = tk.Entry(self, width=width)
        if text: entry.insert(0, text)
        entry['state'] = tk.NORMAL if state else tk.DISABLED
        entry.coords = (row - 1, column - 1)
        entry.grid(row=row, column=column)
        return entry

    def get(self, row, column):
        val = self.entries[row][column].get()
        if val == '':
            result = None if self.required[column] else self.default[column]
        else:
            try:
                result = self.dtype[column](val)
            except:
                raise Exception('Invalid value specified in the entry')
        if self.valid_check[column] is not None and not self.valid_check[column](result):
            raise Exception('Invalid value specified in the entry')
        return result

    def get_row(self, row):
        return [self.get(row, column) for column in range(self.n_column)]

    def get_column(self, column):
        return [self.get(row, column) for row in range(self.n_row)]

    def get_all(self):
        return [[self.get(row, column) for column in range(self.n_column)] for row in range(self.n_row)]

    def set(self, row, column, val):
        self.entries[row][column].delete(0, tk.END)
        self.entries[row][column].insert(0, str(val))

    def set_row(self, row, val):
        for column, v in enumerate(val):
            self.set(row, column, v)
    
    def set_column(self, column, val):
        for row, v in enumerate(val):
            self.set(row, column, v)

    def set_all(self, val):
        for row, v_row in enumerate(val):
            for column, v in enumerate(v_row):
                self.set(row, column, v)

    def enable(self, row, column):
        self.entries[row][column].configure(state=tk.NORMAL)

    def enable_row(self, row):
        for column in range(self.n_column):
            self.enable(row, column)

    def enable_column(self, column):
        for row in range(self.n_row):
            self.enable(row, column)

    def disable(self, row, column):
        self.entries[row][column].configure(state=tk.DISABLED)

    def disable_row(self, row):
        for column in range(self.n_column):
            self.disable(row, column)

    def disable_column(self, column):
        for row in range(self.n_row):
            self.disable(row, column)

    def update_n_row(self, n_row):
        self.n_row = n_row
        self.entries = [[None for _ in range(self.n_column)] for _ in range(self.n_row)]

        # make entries
        for row in range(self.n_row):
            for column in range(self.n_column):
                self.entries[row][column] = self._make_entry(row + 1, column + 1, self.width, '', True)