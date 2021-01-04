import sys
import sqlite3
import numpy as np
from multiprocessing import Lock, Process, Queue

from system.utils.process_safe import ProcessSafeExit


def daemon_func(data_path, task_queue, result_queue):
    '''
    Daemon process for serial database interaction
    '''
    conn = sqlite3.connect(data_path)
    cur = conn.cursor()
    alive = True

    def execute_cmd(msg):
        cmd, args = None, None
        if isinstance(msg, str): # command without argument
            cmd = msg
        elif isinstance(msg, list): # command with arguments
            cmd, *args = msg
        else:
            raise NotImplementedError

        alive = True
        if cmd == 'execute':
            cur.execute(*args)
        elif cmd == 'executemany':
            cur.executemany(*args)
        elif cmd == 'fetchone':
            result_queue.put(cur.fetchone())
        elif cmd == 'fetchall':
            result_queue.put(cur.fetchall())
        elif cmd == 'commit':
            conn.commit()
        elif msg == 'quit':
            conn.close()
            alive = False
        else:
            raise NotImplementedError
        return alive

    while alive:
        msg = task_queue.get()
        if isinstance(msg, tuple): # multiple commands
            for m in msg:
                alive = execute_cmd(m)
        else: # a single commmand
            alive = execute_cmd(msg)


class PersonalDatabase:
    '''
    SQLite database (compatible with multiprocessing)
    '''
    def __init__(self, data_path):
        '''
        Input:
            data_path: file path to database
        '''
        self.lock = Lock()
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.daemon = Process(target=daemon_func, args=(data_path, self.task_queue, self.result_queue))
        self.daemon.start()
    
    def get_lock(self):
        '''
        Get multiprocessing lock
        Usage: with self.get_lock(): ...
        '''
        return self.lock

    def create(self, table_name, key, lock=True):
        '''
        Create table in database
        '''
        if lock:
            self.lock.acquire()

        if isinstance(key, str):
            # create table with single key
            self.task_queue.put(['execute', f'create table {table_name} ({key})'])
        elif isinstance(key, list):
            # create table with multiple keys
            self.task_queue.put(['execute', f'create table {table_name} ({",".join(key)})'])
        else:
            raise NotImplementedError

        if lock:
            self.lock.release()

    def select(self, table_name, key, dtype, rowid=None, lock=True):
        '''
        Select array data from all rows of the table
        '''
        if rowid is None:
            row_cond = ''
        elif isinstance(rowid, int):
            row_cond = f' where rowid = {rowid}'
        elif isinstance(rowid, list) or isinstance(rowid, np.ndarray):
            row_cond = f' where rowid in ({",".join(np.array(rowid, dtype=str))})'
        else:
            raise NotImplementedError

        result = None

        if lock:
            self.lock.acquire()

        try:
            if isinstance(key, str):
                # select array from single column
                self.task_queue.put((['execute', f'select {key} from {table_name}' + row_cond], 'fetchall'))
                result = np.array(self.result_queue.get(), dtype=dtype).squeeze()
            elif isinstance(key, list):
                if isinstance(dtype, type):
                    # select array with single datatype from multiple columns
                    self.task_queue.put((['execute', f'select {",".join(key)} from {table_name}' + row_cond], 'fetchall'))
                    result = np.array(self.result_queue.get(), dtype=dtype)
                elif isinstance(dtype, list):
                    # select array with multiple datatypes from multiple columns
                    result = []
                    for key_, dtype_ in zip(key, dtype):
                        if isinstance(key_, str):
                            self.task_queue.put((['execute', f'select {key_} from {table_name}' + row_cond], 'fetchall'))
                            res = np.array(self.result_queue.get(), dtype=dtype_).squeeze()
                        elif isinstance(key_, list):
                            self.task_queue.put((['execute', f'select {",".join(key_)} from {table_name}' + row_cond], 'fetchall'))
                            res = np.array(self.result_queue.get(), dtype=dtype_)
                        else:
                            raise NotImplementedError
                        result.append(res)
            else:
                raise NotImplementedError
        except ProcessSafeExit:
            if lock:
                self.lock.release()
            self.quit()
            sys.exit(0)

        if lock:
            self.lock.release()
        
        return result

    def select_last(self, table_name, key, dtype, lock=True):
        '''
        Select scalar data from the last row of the table
        '''
        result = None

        if lock:
            self.lock.acquire()

        try:
            if isinstance(key, str):
                # select scalar from single column
                self.task_queue.put((['execute', f'select {key} from {table_name} order by rowid desc limit 1'], 'fetchall'))
                result = np.array(self.result_queue.get(), dtype=dtype).squeeze()
            elif isinstance(key, list):
                if isinstance(dtype, type):
                    # select scalar with single datatype from multiple columns
                    self.task_queue.put((['execute', f'select {",".join(key)} from {table_name} order by rowid desc limit 1'], 'fetchall'))
                    result = np.array(self.result_queue.get(), dtype=dtype)
                elif isinstance(dtype, list):
                    # select scalar with multiple datatypes from multiple columns
                    result = []
                    for key_, dtype_ in zip(key, dtype):
                        if isinstance(key_, str):
                            self.task_queue.put((['execute', f'select {key_} from {table_name} order by rowid desc limit 1'], 'fetchall'))
                            res = np.array(self.result_queue.get(), dtype=dtype_).squeeze()
                        elif isinstance(key_, list):
                            self.task_queue.put((['execute', f'select {",".join(key_)} from {table_name} order by rowid desc limit 1'], 'fetchall'))
                            res = np.array(self.result_queue.get(), dtype=dtype_)
                        else:
                            raise NotImplementedError
                        result.append(res)
            else:
                raise NotImplementedError
        except ProcessSafeExit:
            if lock:
                self.lock.release()
            self.quit()
            sys.exit(0)

        if lock:
            self.lock.release()
        
        return result

    def insert(self, table_name, key, data, lock=True):
        '''
        Insert array data to table
        '''
        if lock:
            self.lock.acquire()

        if isinstance(key, str):
            # insert single array into single column
            self.task_queue.put(['executemany', f'insert into {table_name} ({key}) values (?)', data])
        elif isinstance(key, list):
            # insert multiple array to multiple columns
            data = np.column_stack([np.array(arr, dtype=object) for arr in data])
            self.task_queue.put(['executemany', f'insert into {table_name} ({",".join(key)}) values ({",".join(["?"] * data.shape[1])})', data])
        elif key is None:
            # insert multiple array to all columns
            data = np.column_stack([np.array(arr, dtype=object) for arr in data])
            self.task_queue.put(['executemany', f'insert into {table_name} values ({",".join(["?"] * data.shape[1])})', data])
        else:
            raise NotImplementedError
        
        if lock:
            self.lock.release()

    def update(self, table_name, key, data, rowid, lock=True):
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

        if lock:
            self.lock.acquire()

        if isinstance(key, str):
            # update single scalar to single column
            self.task_queue.put(['executemany', f'update {table_name} set {key} = ?' + condition, np.atleast_2d(np.array(data, dtype=object))])
        elif isinstance(key, list):
            # update multiple scalars to multiple columns
            flattened_data = np.atleast_2d(np.hstack(np.array(data, dtype=object)))
            self.task_queue.put(['executemany', f'update {table_name} set ({",".join(key)}) = ({",".join(["?"] * flattened_data.shape[1])})' + condition, flattened_data])
        else:
            raise NotImplementedError
        
        if lock:
            self.lock.release()

    def get_last_rowid(self, table_name, lock=True):
        '''
        Get the last rowid from database (i.e., number of rows in database)
        '''
        if lock:
            self.lock.acquire()

        self.task_queue.put((['execute', f'select max(rowid) from {table_name}'], 'fetchone'))
        result = self.result_queue.get()[0]

        if lock:
            self.lock.release()

        return result

    def commit(self):
        '''
        Commit changes to database, prevent losing unsaved changes
        '''
        self.task_queue.put('commit')

    def quit(self):
        '''
        Quit database
        '''
        self.task_queue.put('quit')