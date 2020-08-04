import numpy as np
from tkintertable import TableCanvas, TableModel


class Table:
    '''
    Excel-like table in tkinter gui
    '''
    def __init__(self, master, titles):
        self.model = TableModel()
        for title in titles:
            self.model.addColumn(colname=title)
        self.table = TableCanvas(parent=master, model=self.model, read_only=True)
        self.table.show()
        
        self.n_rows = 0
        self.key_map = None

    def register_key_map(self, key_map):
        self.key_map = key_map

    def _process_val(self, val):
        if isinstance(val, bool):
            if val == True: return 'True'
            else: return 'False'
        elif isinstance(val, float):
            return round(val, 4)
        else:
            return val

    def insert(self, data):
        '''
        Insert data into bottom of the table
        '''
        old_n_rows = self.n_rows
        for key, val in data.items():
            if isinstance(val, np.ndarray): val = val.tolist()

            new_n_rows = old_n_rows + len(val)
            if new_n_rows > self.n_rows:
                self.model.autoAddRows(new_n_rows - self.n_rows)
                self.n_rows = new_n_rows
            
            for i, row in enumerate(range(old_n_rows, self.n_rows)):
                if self.key_map is not None and key in self.key_map:
                    mapped_keys = self.key_map[key]
                    for j, mapped_key in enumerate(mapped_keys):
                        self.model.data[row][mapped_key] = self._process_val(val[i][j])
                else:
                    self.model.data[row][key] = self._process_val(val[i])
        
        self.table.redrawTable()

    def update(self, data, rowids=None):
        '''
        Update rows of the table
        '''
        for key, val in data.items():
            if isinstance(val, np.ndarray): val = val.tolist()

            row_range = range(len(val)) if rowids is None else rowids

            for i, row in enumerate(row_range):
                if self.key_map is not None and key in self.key_map:
                    mapped_keys = self.key_map[key]
                    for j, mapped_key in enumerate(mapped_keys):
                        self.model.data[row][mapped_key] = self._process_val(val[i][j])
                else:
                    self.model.data[row][key] = self._process_val(val[i])