import numpy as np
from tkintertable import TableCanvas, TableModel


class Table:
    '''
    Excel-like table in tkinter gui
    '''
    def __init__(self, master, columns):

        # default params
        self.params = {
            'cellwidth': 110,
            'precision': 6,
        }

        self.data = []

        self.model = TableModel()
        self.columns = columns
        for column in columns:
            self.model.addColumn(colname=column)
        self.table = TableCanvas(parent=master, model=self.model, cellwidth=self.params['cellwidth'], read_only=True)
        self.table.setSelectedRow(-1)
        self.table.show()
        
        self.n_rows = 0

    def set_params(self, params):
        assert params.keys() == self.params.keys()
        self.params = params
        self.table.cellwidth = self.params['cellwidth']
        self.refresh()

    def get_params(self):
        return self.params.copy()

    def _process_val(self, val):
        if val is None:
            return 'N/A'
        elif isinstance(val, bool):
            if val == True: return 'Y'
            else: return 'N'
        elif isinstance(val, float):
            if np.isnan(val): return 'N/A'
            else: return round(val, self.params['precision'])
        elif isinstance(val, complex):
            mean = round(val.real, self.params['precision'])
            std = round(val.imag, self.params['precision'])
            return f'{mean}±{std}'
        else:
            return str(val)

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

    def load(self, data, transform=False):
        '''
        '''
        if transform:
            data = self.transform_data(data)

        if len(data) > self.n_rows:
            self.model.autoAddRows(len(data) - self.n_rows)
            self.data.extend([[None for _ in self.columns] for _ in range(len(data) - self.n_rows)])
        elif len(data) < self.n_rows:
            self.model.deleteRows(rowlist=range(len(data), self.n_rows))
            del self.data[len(data):]
        self.n_rows = len(data)

        for row in range(self.n_rows):
            row_data = data[row]
            for j, col in enumerate(self.columns):
                self.model.data[row][col] = self._process_val(row_data[j])
                self.data[row][self.columns.index(col)] = row_data[j]

        self.table.redrawTable()

    def insert(self, columns, data, transform=False):
        '''
        Insert data into bottom of the table
        '''
        if transform:
            data = self.transform_data(data)

        old_n_rows = self.n_rows
        if len(data) > 0:
            self.model.autoAddRows(len(data))
            self.data.extend([[None for _ in self.columns] for _ in data])
            self.n_rows = old_n_rows + len(data)

        if columns is None: columns = self.columns

        for i, row in enumerate(range(old_n_rows, self.n_rows)):
            row_data = data[i]
            for j, col in enumerate(columns):
                self.model.data[row][col] = self._process_val(row_data[j])
                self.data[row][self.columns.index(col)] = row_data[j]
        
        self.table.redrawTable()

    def update(self, columns, data, rowids=None, transform=False):
        '''
        Update rows of the table (TODO: support single rowid)
        '''
        if transform:
            data = self.transform_data(data)

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
                self.data[row][self.columns.index(col)] = row_data[j]

        self.table.redrawTable()

    def refresh(self):
        '''
        '''
        for row in range(self.n_rows):
            for j, col in enumerate(self.columns):
                self.model.data[row][col] = self._process_val(self.data[row][j])
        
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