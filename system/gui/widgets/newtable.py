import numpy as np
from tkintertable import TableCanvas, TableModel


class Table:
    '''
    Excel-like table in tkinter gui
    '''
    def __init__(self, master, columns):
        self.model = TableModel()
        self.columns = columns
        for column in columns:
            self.model.addColumn(colname=column)
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

    def transform_data(self, data_list):
        '''
        '''
        new_data_list = []
        for data in data_list:
            data = np.array(data, dtype=str)
            if len(data.shape) == 1:
                data = np.expand_dims(data, axis=1)
            assert len(data.shape) == 2
            new_data_list.append(data)
        return np.hstack(new_data_list)

    def insert(self, columns, data, transform=False):
        '''
        Insert data into bottom of the table
        '''
        if transform:
            data = self.transform_data(data)

        data = np.array(data, dtype=str)
        data[data == 'None'] = 'N/A'

        new_n_rows = len(data)
        if new_n_rows > self.n_rows:
            self.model.autoAddRows(new_n_rows - self.n_rows)
            self.n_rows = new_n_rows

        if columns is None: columns = self.columns

        for row in range(len(data)):
            row_data = data[row]
            for j, col in enumerate(columns):
                self.model.data[row][col] = self._process_val(row_data[j])
        
        self.table.redrawTable()

    def update(self, columns, data, rowids=None, transform=False):
        '''
        Update rows of the table (TODO: support single rowid)
        '''
        if transform:
            data = self.transform_data(data)

        data = np.array(data, dtype=str)
        data[data == 'None'] = 'N/A'

        if rowids is None:
            rowids = list(range(len(data)))
            new_n_rows = len(data)
            if new_n_rows > self.n_rows:
                self.model.autoAddRows(new_n_rows - self.n_rows)
                self.n_rows = new_n_rows

        if columns is None: columns = self.columns

        assert len(data) == len(rowids)
        for i, row in enumerate(rowids):
            row_data = data[i]
            for j, col in enumerate(columns):
                self.model.data[row][col] = self._process_val(row_data[j])

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