import sqlite3
import numpy as np
from multiprocessing import Lock


class Database:
    '''
    SQLite database (compatible with multiprocessing)
    '''
    def __init__(self, data_path):
        '''
        Input:
            data_path: file path to database
        '''
        self.conn = sqlite3.connect(data_path)
        self.cur = self.conn.cursor()
        self.alive = True
        self.lock = Lock()
    
    def get_lock(self):
        '''
        Get multiprocessing lock
        Usage: with self.get_lock(): ...
        '''
        return self.lock

    def create(self, table_name, key):
        '''
        Create table in database
        '''
        if isinstance(key, str):
            # create table with single key
            self.cur.execute(f'create table {table_name} ({key})')
        elif isinstance(key, list):
            # create table with multiple keys
            self.cur.execute(f'create table {table_name} ({",".join(key)})')
        else:
            raise NotImplementedError

    def select(self, table_name, key, dtype, lock=True):
        '''
        Select array data from all rows of the table
        '''
        if isinstance(key, str):
            # select array from single column
            self.cur.execute(f'select {key} from {table_name}')
            return np.array(self.cur.fetchall(), dtype=dtype).squeeze()
        elif isinstance(key, list):
            if isinstance(dtype, type):
                # select array with single datatype from multiple columns
                self.cur.execute(f'select {",".join(key)} from {table_name}')
                return np.array(self.cur.fetchall(), dtype=dtype)
            elif isinstance(dtype, list):
                # select array with multiple datatypes from multiple columns
                if lock:
                    self.lock.acquire()
                result_list = []
                for key_, dtype_ in zip(key, dtype):
                    if isinstance(key_, str):
                        self.cur.execute(f'select {key_} from {table_name}')
                        result = np.array(self.cur.fetchall(), dtype=dtype_).squeeze()
                    elif isinstance(key_, list):
                        self.cur.execute(f'select {",".join(key_)} from {table_name}')
                        result = np.array(self.cur.fetchall(), dtype=dtype_)
                    else:
                        raise NotImplementedError
                    result_list.append(result)
                if lock:
                    self.lock.release()
                return result_list
        else:
            raise NotImplementedError

    def select_last(self, table_name, key, dtype, lock=True):
        '''
        Select scalar data from the last row of the table
        '''
        if isinstance(key, str):
            # select scalar from single column
            self.cur.execute(f'select {key} from {table_name} order by rowid desc limit 1')
            return np.array(self.cur.fetchall(), dtype=dtype).squeeze()
        elif isinstance(key, list):
            if isinstance(dtype, type):
                # select scalar with single datatype from multiple columns
                self.cur.execute(f'select {",".join(key)} from {table_name} order by rowid desc limit 1')
                return np.array(self.cur.fetchall(), dtype=dtype)
            elif isinstance(dtype, list):
                # select scalar with multiple datatypes from multiple columns
                if lock:
                    self.lock.acquire()
                result_list = []
                for key_, dtype_ in zip(key, dtype):
                    if isinstance(key_, str):
                        self.cur.execute(f'select {key_} from {table_name} order by rowid desc limit 1')
                        result = np.array(self.cur.fetchall(), dtype=dtype_).squeeze()
                    elif isinstance(key_, list):
                        self.cur.execute(f'select {",".join(key_)} from {table_name} order by rowid desc limit 1')
                        result = np.array(self.cur.fetchall(), dtype=dtype_)
                    else:
                        raise NotImplementedError
                    result_list.append(result)
                if lock:
                    self.lock.release()
                return result_list
        else:
            raise NotImplementedError

    def insert(self, table_name, key, data):
        '''
        Insert array data to table
        '''
        if isinstance(key, str):
            # insert single array into single column
            self.cur.executemany(f'insert into {table_name} ({key}) values (?)', data)
        elif isinstance(key, list):
            # insert multiple array to multiple columns
            data = np.column_stack([np.array(arr, dtype=object) for arr in data])
            self.cur.executemany(f'insert into {table_name} ({",".join(key)}) values ({",".join(["?"] * data.shape[1])})', data)
        elif key is None:
            # insert multiple array to all columns
            data = np.column_stack([np.array(arr, dtype=object) for arr in data])
            self.cur.executemany(f'insert into {table_name} values ({",".join(["?"] * data.shape[1])})', data)
        else:
            raise NotImplementedError

    def update(self, table_name, key, data, rowid):
        '''
        Update scalar data to table
        NOTE: updating different values to different rows is not supported
        '''
        if isinstance(rowid, int):
            # update single row
            condition = f' where rowid = {rowid}'
        elif isinstance(rowid, list) or isinstance(rowid, np.ndarray):
            # update multiple rows
            condition = f' where rowid in ({",".join(np.array(rowid, dtype=str))})'
        elif rowid is None:
            # update all rows
            condition = ''
        else:
            raise NotImplementedError

        if isinstance(key, str):
            # update single scalar to single column
            self.cur.executemany(f'update {table_name} set {key} = ?' + condition, [[data]])
        elif isinstance(key, list):
            # update multiple scalars to multiple columns
            flattened_data = []
            for d in data:
                if isinstance(d, list) or isinstance(d, np.ndarray):
                    flattened_data.extend(d)
                else:
                    flattened_data.append(d)
            self.cur.executemany(f'update {table_name} set ({",".join(key)}) = ({",".join(["?"] * len(flattened_data))})' + condition, [flattened_data])
        else:
            raise NotImplementedError

    def commit(self):
        '''
        Commit changes to database, prevent losing unsaved changes
        '''
        self.conn.commit()

    def get_last_rowid(self, table_name):
        '''
        Get the last rowid from database (i.e., number of rows in database)
        '''
        self.cur.execute(f'select max(rowid) from {table_name}')
        return self.cur.fetchone()[0]

    def quit(self):
        '''
        Quit database
        '''
        self.conn.close()