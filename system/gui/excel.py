import tkinter as tk


class Excel(tk.Frame):
    '''
    Excel-like table in tkinter gui
    '''
    def __init__(self, master, rows, columns, width, row_titles=None, column_titles=None):
        super().__init__(master)
        self.n_row = rows
        self.n_column = columns
        self.entries = [[None for _ in range(self.n_column)] for _ in range(self.n_row)]

        if column_titles is not None:
            for column in range(self.n_column):
                self._make_entry(0, column + 1, width, column_titles[column], False) 

        for row in range(self.n_row):
            if row_titles is not None:
                self._make_entry(row + 1, 0, 5, row_titles[row], False)
                
            for column in range(self.n_column):
                self.entries[row][column] = self._make_entry(row + 1, column + 1, width, '', True)

    def _make_entry(self, row, column, width, text, state):
        entry = tk.Entry(self, width=width)
        if text: entry.insert(0, text)
        entry['state'] = tk.NORMAL if state else tk.DISABLED
        entry.coords = (row - 1, column - 1)
        entry.grid(row=row, column=column)
        return entry

    def get(self, row, column, dtype=str, valid_check=None):
        val = self.entries[row][column].get()
        if val == '':
            result = None
        else:
            try:
                result = dtype(val)
            except:
                raise Exception('Invalid value specified in the entry')
        if valid_check is not None and not valid_check(result):
            raise Exception('Invalid value specified in the entry')
        return result

    def get_row(self, row, dtype=str, valid_check=None):
        return [self.get(row, column, dtype, valid_check) for column in range(self.n_column)]

    def get_column(self, column, dtype=str, valid_check=None):
        return [self.get(row, column, dtype, valid_check) for row in range(self.n_row)]

    def get_all(self, dtype=str, valid_check=None):
        return [[self.get(row, column, dtype, valid_check) for column in range(self.n_column)] for row in range(self.n_row)]

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