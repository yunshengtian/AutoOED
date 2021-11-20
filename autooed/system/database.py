'''
Database related tools.
'''

import os
import sys
import sqlite3
import numpy as np
import yaml
from multiprocessing import Lock, Process, Queue, Value
from collections.abc import Iterable

from autooed.utils.path import get_root_dir


'''
Descriptions of the reserved database tables.
'''
table_descriptions = {

    '_empty_table': '''
        name varchar(50) not null primary key
        ''',

    '_config': '''
        name varchar(50) not null,
        config text not null
        ''',

}


def daemon_func(data_path, task_queue, result_queue):
    '''
    Daemon process for serial database interaction.

    Parameters
    ----------
    data_path: str
        Path of the database file.
    task_queue: multiprocessing.Queue
        Queue to put tasks in.
    result_queue: multiprocessing.Queue
        Queue to get results from.
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
                if not alive:
                    break
        else: # a single commmand
            alive = execute_cmd(msg)


class SafeLock:
    '''
    Safe database lock control for avoiding writing conflict.
    '''
    def __init__(self, lock, block=True):
        '''
        Parameters
        ----------
        lock: multiprocessing.Lock
            The database lock.
        block: bool
            Whether to acquire lock in a blocked way.
        '''
        self.lock = lock
        self.block = block
        self.locked = False

    def __enter__(self):
        self.locked = self.lock.acquire(block=self.block)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.locked:
            self.lock.release()
        if exc_type:
            return False


class Database:
    '''
    Database based on SQLite.
    '''
    def __init__(self):
        self.data_path = os.path.join(get_root_dir(), 'data.db')

        self.lock = Lock()
        self.execute_lock = Lock()
        self.task_queue = Queue()
        self.result_queue = Queue()

        # connect sqlite
        self.connect()

        # reserved tables
        self.reserved_tables = list(table_descriptions.keys())

        # reserved tables
        for name, desc in table_descriptions.items():
            if not self._check_reserved_table_exist(name):
                self.execute(f'create table "{name}" ({desc})')

        # checksum
        self.checksum = Value('i', 0)
                
    '''
    connection
    '''

    def connect(self, force=False):
        '''
        Connect to database.
        '''
        if force: return # TODO
        Process(target=daemon_func, args=(self.data_path, self.task_queue, self.result_queue)).start()

    def commit(self):
        '''
        Commit changes to database.
        '''
        self.task_queue.put('commit')

    def quit(self):
        '''
        Quit database.
        '''
        self.task_queue.put('quit')

    '''
    execution
    '''

    def _execute(self, exe_type, query, data=None, fetchone=False, fetchall=False):
        '''
        Execute a query by putting it in the task queue and fetch the results.

        Parameters
        ----------
        exe_type: str
            Whether to execute a single-row or multi-row query (execute or executemany).
        query: str
            The query command in SQL.
        data: list
            List of data associated with the query.
        fetchone: bool
            Whether to fetch one query result to return.
        fetchall: bool
            Whether to fetch all query results to return.

        Returns
        -------
        list
            A list of fetched results (if fetch).
        '''
        self.execute_lock.acquire()
        assert exe_type in ['execute', 'executemany']
        msg = [exe_type, query]
        if data is not None:
            msg.append(data)
            
        assert not (fetchone and fetchall)
        if fetchone:
            msg = (msg, 'fetchone')
        if fetchall:
            msg = (msg, 'fetchall')

        if fetchone or fetchall:
            self.task_queue.put(msg)
            result = self.result_queue.get()
            self.execute_lock.release()
            return result
        else:
            self.task_queue.put(msg)
            self.execute_lock.release()

    def execute(self, *args, **kwargs):
        '''
        Execute a single-row query by putting it in the task queue and fetch the results.
        '''
        return self._execute('execute', *args, **kwargs)
        
    def executemany(self, *args, **kwargs):
        '''
        Execute a multi-row query by putting it in the task queue and fetch the results.
        '''
        return self._execute('executemany', *args, **kwargs)

    '''
    table
    '''

    def get_table_list(self):
        '''
        Get the list of all database tables.
        '''
        with SafeLock(self.lock):
            inited_table_list = self.execute(f'select name from sqlite_master where type="table"', fetchall=True)
            empty_table_list = self.execute(f'select name from _empty_table', fetchall=True)
        table_list = inited_table_list + empty_table_list
        table_list = [table[0] for table in table_list if table[0] not in self.reserved_tables]
        return table_list

    def check_table_exist(self, name, block=True):
        '''
        Check if certain database table exist.

        Parameters
        ----------
        name: str
            Name of the table to check.
        block: bool
            Whether to acquire lock in a blocked way.
        '''
        assert name not in self.reserved_tables, f'{name} is a reserved table'
        with SafeLock(self.lock, block=block):
            inited_table_list = self.execute(f'select name from sqlite_master where type="table" and name="{name}"', fetchall=True)
            empty_table_list = self.execute(f'select name from _empty_table where name="{name}"', fetchall=True)
        inited_table_exist = len(inited_table_list) > 0
        empty_table_exist = len(empty_table_list) > 0
        assert not (inited_table_exist and empty_table_exist)
        return inited_table_exist or empty_table_exist

    def check_inited_table_exist(self, name):
        '''
        Check if certain database table exists and is initialized with data.

        Parameters
        ----------
        name: str
            Name of the table to check.
        '''
        assert name not in self.reserved_tables, f'{name} is a reserved table'
        inited_table_list = self.execute(f'select * from sqlite_master where type="table" and name="{name}"', fetchall=True)
        return len(inited_table_list) > 0

    def _check_reserved_table_exist(self, name):
        '''
        Check if certain reserved database table exists.

        Parameters
        ----------
        name: str
            Name of the table to check.
        '''
        assert name in self.reserved_tables, f'{name} is not a reserved table'
        table_list = self.execute(f'select * from sqlite_master where type="table" and name="{name}"', fetchall=True)
        return len(table_list) > 0

    def load_table(self, name, column=None):
        '''
        Load data from a database table.

        Parameters
        ----------
        name: str
            Name of the table to load data from.
        column: str/list
            Column name(s) of the table to load data from.
        '''
        with SafeLock(self.lock):
            assert self.check_table_exist(name, block=False), f'Table {name} does not exist'
            result = self.select_data(name, column)
        return result
    
    def create_table(self, name):
        '''
        Create a database table (uninitialized).

        Parameters
        ----------
        name: str
            Name of the table to create.
        '''
        name = name.lower()
        with SafeLock(self.lock):
            assert not self.check_table_exist(name, block=False), f'Table {name} exists'

            # in case not removed completely
            self.execute(f'delete from _config where name="{name}"')
            self.execute(f'delete from _empty_table where name="{name}"')

            self.execute(f'insert into _empty_table values ("{name}")')
            self.commit()

    def init_table(self, name, problem_cfg):
        '''
        Initialize a database table.

        Parameters
        ----------
        name: str
            Name of the table to initialize.
        problem_cfg: dict
            Problem configurations.
        '''
        problem_name = problem_cfg['name']
        n_var, n_obj = problem_cfg['n_var'], problem_cfg['n_obj']
        var_name_list, obj_name_list = problem_cfg['var_name'], problem_cfg['obj_name']
        var_type = problem_cfg['type']

        var_type_map = {
            'continuous': 'float',
            'integer': 'int',
            'binary': 'boolean',
            'categorical': 'varchar(50)',
        }

        description = ['status varchar(20) not null default "unevaluated"']
        if var_type == 'mixed':
            for var_name, var_info in zip(var_name_list, problem_cfg['var'].values()):
                description.append(f'"{var_name}" {var_type_map[var_info["type"]]} not null')
        else:
            for var_name in var_name_list:
                description.append(f'"{var_name}" {var_type_map[var_type]} not null')
        for obj_name in obj_name_list:
            description.append(f'"{obj_name}" float')
            description.append(f'"_{obj_name}_pred_mean" float')
            description.append(f'"_{obj_name}_pred_std" float')
        description += ['pareto boolean', 'batch int not null']
        description += ['_order int default -1', '_hypervolume float']
        
        with SafeLock(self.lock):
            self.execute(f'create table "{name}" ({",".join(description)})')
            self.execute(f'delete from _empty_table where name="{name}"')
            self.commit()

    def remove_table(self, name):
        '''
        Remove a database table.

        Parameters
        ----------
        name: str
            Name of the table to remove.
        '''
        assert name not in self.reserved_tables
        table_exist = True
        with SafeLock(self.lock):
            if self.check_inited_table_exist(name):
                self.execute(f'drop table "{name}"')
                self.execute(f'delete from _config where name="{name}"')
                self.commit()
            elif self.check_table_exist(name, block=False):
                self.execute(f'delete from _empty_table where name="{name}"')
                self.commit()
            else:
                table_exist = False
        if not table_exist:
            raise Exception(f'Table {name} does not exist')

    '''
    config
    '''

    def update_config(self, name, config):
        '''
        Update the experiment config of a database table.

        Parameters
        ----------
        name: str
            Name of the database table.
        config: dict
            Experiment configurations to upate.
        '''
        # convert all numpy array to list
        def convert_config(config):
            for key, val in config.items():
                if type(val) == np.ndarray:
                    config[key] = val.tolist()
                elif type(val) == dict:
                    convert_config(config[key])

        config = config.copy()
        convert_config(config)
        
        config_str = yaml.dump(config)
        with SafeLock(self.lock):
            self.execute(f'insert into _config (name, config) values ("{name}", "{config_str}")')
            self.commit()

    def query_config(self, name):
        '''
        Query the experiment config of a given database table.

        Parameters
        ----------
        name: str
            Name of the database table.

        Returns
        -------
        dict
            Queried experiment configurations (None if not found).
        '''
        config_str = self.execute(f'select config from _config where name="{name}" order by rowid desc limit 1', fetchone=True)
        if config_str is None:
            return None
        else:
            config = yaml.load(config_str[0], Loader=yaml.FullLoader)
            return config

    '''
    basic operations
    '''

    def insert_data(self, table, column, data, transform=False):
        '''
        Insert single-row data to the database.

        Parameters
        ----------
        table: str
            Name of the database table to insert.
        column: str/list
            Column name(s) of the table to insert.
        data: list/np.ndarray
            Data to insert.
        transform: bool
            Whether the data needs to be stacked for queries.

        Returns
        -------
        int
            Row number of the inserted data.
        '''
        if transform:
            data = self._transform_data(data)
        if type(data) == np.ndarray:
            data = data.tolist()
        if column is None:
            query = f'insert into "{table}" values ({",".join(["?"] * len(data))})'
        elif type(column) == str:
            query = f'insert into "{table}" ("{column}") values (?)'
        else:
            # assert len(column) == len(data), 'length mismatch of keys and values'
            column_str = ','.join([f'"{col}"' for col in column])
            query = f'insert into "{table}" ({column_str}) values ({",".join(["?"] * len(data))})'

        with SafeLock(self.lock):
            self.execute(query, data)
            self.commit()
            self._update_checksum()
            n_row = self.get_n_row(table)

        rowid = n_row
        return rowid

    def insert_multiple_data(self, table, column, data, transform=False):
        '''
        Insert multi-row data to the database.

        Parameters
        ----------
        table: str
            Name of the database table to insert.
        column: str/list
            Column name(s) of the table to insert.
        data: list/np.ndarray
            Data to insert.
        transform: bool
            Whether the data needs to be stacked for queries.

        Returns
        -------
        list
            Row numbers of the inserted data.
        '''
        if transform:
            data = self._transform_multiple_data(data)
        if type(data) == np.ndarray:
            data = data.tolist()
        if column is None:
            query = f'insert into "{table}" values ({",".join(["?"] * len(data[0]))})'
        elif type(column) == str:
            query = f'insert into "{table}" ("{column}") values (?)'
        else:
            # assert len(column) == len(data[0]), 'length mismatch of keys and values'
            column_str = ','.join([f'"{col}"' for col in column])
            query = f'insert into "{table}" ({column_str}) values ({",".join(["?"] * len(data[0]))})'

        with SafeLock(self.lock):
            self.executemany(query, data)
            self.commit()
            self._update_checksum()
            n_row = self.get_n_row(table)

        rowids = list(range(n_row - len(data) + 1, n_row + 1))
        return rowids

    def _get_rowid_condition(self, rowid):
        '''
        Get the condition part of a SQL query based on the specified row number(s).

        Parameters
        ----------
        rowid: int/list
            Row number(s) (if None then all rows).
        
        Returns
        -------
        str
            The condition part of the query.
        '''
        if rowid is None:
            # update all rows
            condition = ''
        elif isinstance(rowid, Iterable):
            # update multiple rows
            condition = f' where rowid in ({",".join(np.array(rowid, dtype=str))})'
        else:
            # update single row
            condition = f' where rowid = {int(rowid)}'
        return condition

    def update_data(self, table, column, data, rowid, transform=False):
        '''
        Update single-row data of the database.

        Parameters
        ----------
        table: str
            Name of the database table to update.
        column: str/list
            Column name(s) of the table to update.
        data: list/np.ndarray
            Data to update.
        rowid: int
            Row number of the table to update.
        transform: bool
            Whether the data needs to be stacked for queries.
        '''
        if transform:
            data = self._transform_data(data)
        if type(data) == np.ndarray:
            data = data.tolist()

        if type(column) == str:
            query = f'update "{table}" set "{column}"=?'
        else:
            # assert len(column) == len(data), 'length mismatch of keys and values'
            column_exp_str = ','.join([f'"{col}"=?' for col in column])
            query = f'update "{table}" set {column_exp_str}'

        assert type(rowid) == int, 'row number is not an integer, use update_multiple_data instead for multiple row numbers'
        condition = self._get_rowid_condition(rowid)
        query += condition

        with SafeLock(self.lock):
            self.execute(query, data)
            self.commit()
            self._update_checksum()

    def update_multiple_data(self, table, column, data, rowid=None, transform=False):
        '''
        Update multi-row data of the database.

        Parameters
        ----------
        table: str
            Name of the database table to update.
        column: str/list
            Column name(s) of the table to update.
        data: list/np.ndarray
            Data to update.
        rowid: list/np.ndarray
            Row numbers of the table to update (if None then all rows).
        transform: bool
            Whether the data needs to be stacked for queries.
        '''
        if transform:
            data = self._transform_multiple_data(data)
        if type(data) == np.ndarray:
            data = data.tolist()

        if type(column) == str:
            query = f'update "{table}" set "{column}"=?'
        else:
            # assert len(column) == len(data), 'length mismatch of keys and values'
            column_exp_str = ','.join([f'"{col}"=?' for col in column])
            query = f'update "{table}" set {column_exp_str}'

        with SafeLock(self.lock):
            # updating different data for different rows is not supported by sqlite
            if isinstance(rowid, Iterable):
                for single_data, single_rowid in zip(data, list(rowid)):
                    condition = self._get_rowid_condition(single_rowid)
                    self.execute(query + condition, single_data)
            else:
                condition = self._get_rowid_condition(rowid)
                self.executemany(query + condition, data)
            self.commit()
            self._update_checksum()

    def delete_data(self, table, rowid):
        '''
        Delete data from the database.

        Parameters
        ----------
        table: str
            Name of the database table to delete from.
        rowid: int/list
            Row number(s) of the table to delete from (if None then all rows).
        '''
        condition = self._get_rowid_condition(rowid)
        query = f'delete from "{table}"' + condition

        with SafeLock(self.lock):
            self.execute(query)
            self.commit()
            self._update_checksum()
    
    def _transform_data(self, data_list):
        '''
        Horizontally stack data together for single-row database queries.

        Parameters
        ----------
        data_list: list/np.ndarray
            List of data to be stacked.
        
        Returns
        -------
        np.ndarray
            Stacked data for database queries (in str format).
        '''
        new_data_list = []
        for data in data_list:
            data = np.array(data, dtype=str)
            if len(data.shape) == 0:
                data = np.expand_dims(data, axis=0)
            assert len(data.shape) == 1, f'error: data shape {data.shape}'
            new_data_list.append(data)
        return np.hstack(new_data_list)

    def _transform_multiple_data(self, data_list):
        '''
        Horizontally stack data together for multi-row database queries.

        Parameters
        ----------
        data_list: list/np.ndarray
            List of data to be stacked.
        
        Returns
        -------
        np.ndarray
            Stacked data for database queries (in str format).
        '''
        new_data_list = []
        for data in data_list:
            data = np.array(data, dtype=str)
            if len(data.shape) == 1:
                data = np.expand_dims(data, axis=1)
            assert len(data.shape) == 2
            new_data_list.append(data)
        return np.hstack(new_data_list)

    def select_data(self, table, column, rowid=None):
        '''
        Get data from database using select queries.

        Parameters
        ----------
        table: str
            Name of the database table to query.
        column: str/list
            Column name(s) of the table to query (if None then select all columns).
        rowid: int/list
            Row number(s) of the table to query (if None then select all rows).
        
        Returns
        -------
        list
            Selected data based on input arguments.
        '''
        if column is None:
            query = f'select * from "{table}"'
        elif type(column) == str:
            query = f'select "{column}" from "{table}"'
        else:
            column_str = ','.join([f'"{col}"' for col in column])
            query = f'select {column_str} from "{table}"'

        condition = self._get_rowid_condition(rowid)
        query += condition

        return self.execute(query, fetchall=True)

    def get_n_row(self, table):
        '''
        Get the number of rows of a database table.

        Parameters
        ----------
        table: str
            Name of the database table.

        Returns
        -------
        int
            Number of rows in the given table.
        '''
        query = f'select count(*) from "{table}"'
        return self.execute(query, fetchone=True)[0]

    def get_column_names(self, table):
        '''
        Get the column names of a database table.

        Parameters
        ----------
        table: str
            Name of the database table.

        Returns
        -------
        list
            Column names of the given table.
        '''
        query = f'select name from pragma_table_info("{table}")'
        column_names = self.execute(query, fetchall=True)
        column_names = [name[0] for name in column_names]
        return column_names

    def get_checksum(self, table=None):
        '''
        Get the checksum of a database table.

        Parameters
        ----------
        table: str
            Name of the database table.

        Returns
        -------
        int
            Checksum of the given table.
        '''
        return self.checksum.value

    def _update_checksum(self):
        '''
        Update the checksum of a database table.

        Parameters
        ----------
        table: str
            Name of the database table.
        '''
        self.checksum.value += 1
