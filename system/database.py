import sqlite3
import numpy as np

from .utils import check_pareto


class Database:
    '''
    SQLite database (compatible with multiprocessing)
    Keys: x1, x2, ..., f1, f2, ..., expected_f1, expected_f2, ..., uncertainty_f1, uncertainty_f2, ..., hv, is_pareto
    '''
    def __init__(self, db_path, n_var, n_obj, hv):
        self.db_path = db_path
        self.n_var = n_var
        self.n_obj = n_obj
        self.hv = hv
        self.conn = sqlite3.connect(self.db_path)
        self.cur = self.conn.cursor()
        self._create()

    def _create(self):
        '''
        Create database table
        '''
        key_list = [f'x{i + 1} real' for i in range(self.n_var)] + \
            [f'f{i + 1} real' for i in range(self.n_obj)] + \
            [f'expected_f{i + 1} real' for i in range(self.n_obj)] + \
            [f'uncertainty_f{i + 1} real' for i in range(self.n_obj)] + \
            ['hv real', 'is_pareto boolean']
        self.cur.execute(f'create table data ({",".join(key_list)})')
        self.conn.commit()

    def init(self, X, Y):
        '''
        Initialize database table with initial data X, Y
        '''
        sample_len = X.shape[0]
        Y_expected = np.zeros((sample_len, self.n_obj))
        Y_uncertainty = np.zeros((sample_len, self.n_obj))

        hv_value = np.full(sample_len, self.hv.calc(Y))
        is_pareto = check_pareto(Y)
        data = np.column_stack([X, Y, Y_expected, Y_uncertainty, hv_value, is_pareto])
        self.cur.executemany(f'insert into data values ({",".join(["?"] * (self.n_var + 3 * self.n_obj + 2))})', data)
        self.conn.commit()
        
    def insert(self, X, Y, Y_expected, Y_uncertainty):
        '''
        Insert data into rows of database table
        '''
        sample_len = X.shape[0]
        Y_keys = [f'f{i + 1}' for i in range(self.n_obj)]
        self.cur.execute(f'select {",".join(Y_keys)} from data')
        old_Y = np.array(self.cur.fetchall())
        all_Y = np.vstack([old_Y, Y])

        hv_value = np.full(sample_len, self.hv.calc(all_Y))
        is_pareto = np.where(check_pareto(all_Y))[0] + 1
        data = np.column_stack([X, Y, Y_expected, Y_uncertainty, hv_value]).tolist()
        for i in range(len(data)):
            data[i].append(False)
        with self.conn:
            self.cur.executemany(f'insert into data values ({",".join(["?"] * (self.n_var + 3 * self.n_obj + 2))})', data)
            self.cur.execute(f'update data set is_pareto = false')
            self.cur.execute(f'update data set is_pareto = true where rowid in ({",".join(is_pareto.astype(str))})')
        self.conn.commit()

    def select(self, keys, dtype=float, rowid=None):
        '''
        Query data from database
        '''
        if rowid is None:
            self.cur.execute(f'select {",".join(keys)} from data')
        else:
            self.cur.execute(f'select {",".join(keys)} from data where rowid = {rowid}')
        result = np.array(self.cur.fetchall(), dtype=dtype)
        return result

    def select_multiple(self, keys_list, dtype_list=None, rowid_list=None):
        '''
        Query multiple types of data from database
        '''
        if dtype_list is None:
            dtype_list = [float] * len(keys_list)
        if rowid_list is None:
            rowid_list = [None] * len(keys_list)
        assert len(keys_list) == len(dtype_list) == len(rowid_list)

        with self.conn:
            result_list = []
            for keys, dtype, rowid in zip(keys_list, dtype_list, rowid_list):
                if rowid is None:
                    self.cur.execute(f'select {",".join(keys)} from data')
                else:
                    self.cur.execute(f'select {",".join(keys)} from data where rowid = {rowid}')
                result = np.array(self.cur.fetchall(), dtype=dtype)
                result_list.append(result)
        return result_list

    def quit(self):
        self.conn.close()