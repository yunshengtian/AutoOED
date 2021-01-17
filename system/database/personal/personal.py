import os
import sys
import sqlite3
import numpy as np
import yaml
from multiprocessing import Lock, Process, Queue, Value
from collections.abc import Iterable

from system.utils.path import get_root_dir
from .table import get_table_descriptions


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
                if not alive:
                    break
        else: # a single commmand
            alive = execute_cmd(msg)


class SafeLock:
    '''
    '''
    def __init__(self, lock, block=True):
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


class PersonalDatabase:
    '''
    '''
    def __init__(self):
        '''
        '''
        self.data_path = os.path.join(get_root_dir(), 'data.db')

        self.lock = Lock()
        self.execute_lock = Lock()
        self.task_queue = Queue()
        self.result_queue = Queue()

        # connect sqlite
        self.connect()

        # reserved tables
        table_descriptions = get_table_descriptions()
        self.reserved_tables = table_descriptions.keys()

        # reserved tables
        for name, desc in table_descriptions.items():
            if not self._check_reserved_table_exist(name):
                self.execute(f'create table {name} ({desc})')

        # checksum
        self.checksum = Value('i', 0)
                
    '''
    connection
    '''

    def connect(self, force=False):
        '''
        '''
        if force: return # TODO
        self.daemon = Process(target=daemon_func, args=(self.data_path, self.task_queue, self.result_queue))
        self.daemon.start()

    def commit(self):
        '''
        Commit changes to database
        '''
        self.task_queue.put('commit')

    def quit(self):
        '''
        Quit database
        '''
        self.task_queue.put('quit')

    '''
    execution
    '''

    def _execute(self, exe_type, query, data=None, fetchone=False, fetchall=False):
        '''
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
        '''
        return self._execute('execute', *args, **kwargs)
        
    def executemany(self, *args, **kwargs):
        '''
        '''
        return self._execute('executemany', *args, **kwargs)

    '''
    table
    '''

    def get_table_list(self):
        '''
        '''
        with SafeLock(self.lock):
            inited_table_list = self.execute(f'select name from sqlite_master where type="table"', fetchall=True)
            empty_table_list = self.execute(f'select name from _empty_table', fetchall=True)
        table_list = inited_table_list + empty_table_list
        table_list = [table[0] for table in table_list if table[0] not in self.reserved_tables]
        return table_list

    def check_table_exist(self, name, block=True):
        '''
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
        '''
        assert name not in self.reserved_tables, f'{name} is a reserved table'
        inited_table_list = self.execute(f'select * from sqlite_master where type="table" and name="{name}"', fetchall=True)
        return len(inited_table_list) > 0

    def _check_reserved_table_exist(self, name):
        '''
        '''
        assert name in self.reserved_tables, f'{name} is not a reserved table'
        table_list = self.execute(f'select * from sqlite_master where type="table" and name="{name}"', fetchall=True)
        return len(table_list) > 0

    def load_table(self, name):
        '''
        '''
        with SafeLock(self.lock):
            assert self.check_table_exist(name, block=False), f'Table {name} does not exist'
            result = self.execute(f'select * from {name}', fetchall=True)
        return result
    
    def create_table(self, name):
        '''
        '''
        with SafeLock(self.lock):
            assert not self.check_table_exist(name, block=False), f'Table {name} exists'
            self.execute(f'insert into _empty_table values ("{name}")')
            self.commit()

    def init_table(self, name, var_type, n_var, n_obj, n_constr, obj_type):
        '''
        '''
        description = ['status varchar(20) not null default "unevaluated"']
        for i in range(1, n_var + 1):
            description.append(f'x{i} float not null')
        for i in range(1, n_obj + 1):
            description.append(f'f{i} float')
        for i in range(1, n_obj + 1):
            description.append(f'f{i}_expected float')
        for i in range(1, n_obj + 1):
            description.append(f'f{i}_uncertainty float')
        description += ['is_pareto boolean', 'config_id int not null', 'batch_id int not null']

        if isinstance(obj_type, str):
            obj_type_str = obj_type
        elif isinstance(obj_type, Iterable):
            obj_type_str = ','.join(obj_type)
        else:
            raise Exception('invalid objective type')
        
        with SafeLock(self.lock):
            self.execute(f'create table {name} ({",".join(description)})')
            self.execute(f'delete from _empty_table where name="{name}"')
            self.execute(f'insert into _problem_info values ("{name}", "{var_type}", {n_var}, {n_obj}, {n_constr}, "{obj_type_str}")')
            self.commit()

    def import_table_from_file(self, name, file_path):
        '''
        '''
        # TODO
        raise NotImplementedError

    def remove_table(self, name):
        '''
        '''
        assert name not in self.reserved_tables
        table_exist = True
        with SafeLock(self.lock):
            if self.check_inited_table_exist(name):
                self.execute(f'drop table {name}')
                self.execute(f'delete from _problem_info where name="{name}"')
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
    problem
    '''

    def query_problem(self, name):
        '''
        '''
        result = self.execute(f'select * from _problem_info where name="{name}"', fetchone=True)

        if result is None:
            var_type, n_var, n_obj, n_constr, obj_type = [None] * 5
        else:
            var_type, n_var, n_obj, n_constr, obj_type = result[1:]
            if ',' in obj_type:
                obj_type = obj_type.split(',')

        return {
            'name': name,
            'var_type': var_type,
            'n_var': n_var,
            'n_obj': n_obj,
            'n_constr': n_constr,
            'obj_type': obj_type,
        }

    '''
    config
    '''

    def update_config(self, name, config):
        '''
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
        '''
        if transform:
            data = self._transform_data(data)
        if type(data) == np.ndarray:
            data = data.tolist()
        if column is None:
            query = f"insert into {table} values ({','.join(['?'] * len(data))})"
        elif type(column) == str:
            query = f"insert into {table} values (?)"
        else:
            # assert len(column) == len(data), 'length mismatch of keys and values'
            query = f"insert into {table} ({','.join(column)}) values ({','.join(['?'] * len(data))})"

        with SafeLock(self.lock):
            self.execute(query, data)
            self.commit()
            self._update_checksum()

    def insert_multiple_data(self, table, column, data, transform=False):
        '''
        '''
        if transform:
            data = self._transform_multiple_data(data)
        if type(data) == np.ndarray:
            data = data.tolist()
        if column is None:
            query = f"insert into {table} values ({','.join(['?'] * len(data[0]))})"
        elif type(column) == str:
            query = f"insert into {table} values (?)"
        else:
            # assert len(column) == len(data[0]), 'length mismatch of keys and values'
            query = f"insert into {table} ({','.join(column)}) values ({','.join(['?'] * len(data[0]))})"

        with SafeLock(self.lock):
            self.executemany(query, data)
            self.commit()
            self._update_checksum()

    def _get_rowid_condition(self, rowid):
        '''
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

    def update_data(self, table, column, data, rowid=None, transform=False):
        '''
        '''
        if transform:
            data = self._transform_data(data)
        if type(data) == np.ndarray:
            data = data.tolist()

        if type(column) == str:
            query = f"update {table} set {column}=?"
        else:
            # assert len(column) == len(data), 'length mismatch of keys and values'
            query = f"update {table} set {','.join([col + '=?' for col in column])}"

        condition = self._get_rowid_condition(rowid)
        query += condition

        with SafeLock(self.lock):
            self.execute(query, data)
            self.commit()
            self._update_checksum()

    def update_multiple_data(self, table, column, data, rowid=None, transform=False):
        '''
        '''
        if transform:
            data = self._transform_multiple_data(data)
        if type(data) == np.ndarray:
            data = data.tolist()

        if type(column) == str:
            query = f"update {table} set {column}=?"
        else:
            # assert len(column) == len(data), 'length mismatch of keys and values'
            query = f"update {table} set {','.join([col + '=?' for col in column])}"

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
        '''
        condition = self._get_rowid_condition(rowid)
        query = f'delete from {table}' + condition

        with SafeLock(self.lock):
            self.execute(query)
            self.commit()
            self._update_checksum()
    
    def _transform_data(self, data_list):
        '''
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
        '''
        if column is None:
            query = f'select * from {table}'
        elif type(column) == str:
            query = f"select {column} from {table}"
        else:
            query = f"select {','.join(column)} from {table}"

        condition = self._get_rowid_condition(rowid)
        query += condition

        return self.execute(query, fetchall=True)

    def get_n_row(self, table):
        '''
        '''
        query = f'select count(*) from {table}'
        return self.execute(query, fetchone=True)[0]

    def get_column_names(self, table):
        '''
        '''
        query = f'select name from pragma_table_info("{table}")'
        column_names = self.execute(query, fetchall=True)
        column_names = [name[0] for name in column_names]
        return column_names

    def get_checksum(self):
        '''
        '''
        return self.checksum.value

    def _update_checksum(self):
        '''
        '''
        self.checksum.value += 1