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
        self.table = TableCanvas(parent=master, model=self.model, cellwidth=110, read_only=True)
        self.table.setSelectedRow(-1)
        self.table.show()
        
        self.n_rows = 0

    def _process_val(self, val):
        if isinstance(val, bool):
            if val == True: return 'True'
            else: return 'False'
        elif isinstance(val, float):
            if np.isnan(val): return 'N/A'
            else: return round(val, 4)
        else:
            return val

    def insert(self, data):
        '''
        Insert data into bottom of the table
        '''
        new_n_rows = len(data)
        if new_n_rows > self.n_rows:
            self.model.autoAddRows(new_n_rows - self.n_rows)
            self.n_rows = new_n_rows

        for row in range(len(data)):
            row_data = data[row]
            for col in range(len(row_data)):
                entry_data = row_data[col]
                self.model.data[row][col] = self._process_val(entry_data)
        
        self.table.redrawTable()

    def update(self, data, rowids=None):
        '''
        Update rows of the table (TODO: support single rowid)
        '''
        if rowids is None:
            rowids = list(range(len(data)))
            new_n_rows = len(data)
            if new_n_rows > self.n_rows:
                self.model.autoAddRows(new_n_rows - self.n_rows)
                self.n_rows = new_n_rows

        assert len(data) == len(rowids)
        for i, row in enumerate(rowids):
            row_data = data[i]
            for col in range(len(row_data)):
                entry_data = row_data[col]
                self.model.data[row][col] = self._process_val(entry_data)

        self.table.redrawTable()

    def get(self, row, column):
        '''
        Get the cell value
        '''
        return self.table.model.data[row][column]

    def get_column(self, column):
        '''
        Get values of a column
        '''
        return [self.get(row, column) for row in range(self.n_rows)]

    def export_csv(self):
        '''
        Export table content to a csv file
        '''
        self.table.exportTable()