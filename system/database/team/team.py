import os
import mysql.connector
import requests
import ipaddress
import numpy as np
import yaml
from collections.abc import Iterable

from .table import get_table_descriptions, get_table_post_processes
from .procedure import get_procedure_queries, get_procedure_access
from .function import get_function_queries, get_function_access
from .trigger import get_trigger_queries


def root(func):
    '''
    '''
    def new_func(self, *args, **kwargs):
        assert self.login_info['user'] == 'root', 'root privilege is needed'
        return func(self, *args, **kwargs)
    return new_func


class TeamDatabase:
    '''
    '''
    def __init__(self, host, user, passwd):
        '''
        '''
        self.login_info = {
            'host': host,
            'user': user,
            'passwd': passwd,
        }
        self.database = 'autooed'

        # connect mysql
        self.conn = mysql.connector.connect(**self.login_info, autocommit=True)
        self.cursor = self.conn.cursor()

        # create database
        self.execute(f"show databases like '{self.database}'")
        if self.cursor.fetchone() == None:
            self.execute(f'create database {self.database}')

        # connect database
        self.execute(f'use {self.database}')

        # reserved tables
        table_descriptions = get_table_descriptions()
        self.reserved_tables = list(table_descriptions.keys())
        
        # initialize reserved utilities
        if user == 'root':

            # reserved tables
            table_post_processes = get_table_post_processes()
            for name, desc in table_descriptions.items():
                if not self._check_reserved_table_exist(name):
                    self.execute(f'create table {name} ({desc})')
                    if name in table_post_processes.keys():
                        self.execute(table_post_processes[name])

            # reserved procedures
            procedure_queries = get_procedure_queries(self.database)
            for name, query in procedure_queries.items():
                if not self._check_procedure_exist(name):
                    self.execute(query)
            
            # reserved functions
            function_queries = get_function_queries(self.database)
            for name, query in function_queries.items():
                if not self._check_function_exist(name):
                    self.execute(query)

            self.execute('set global log_bin_trust_function_creators = 1')

    '''
    connection
    '''

    def connect(self, force=False):
        '''
        '''
        if self.conn.is_connected() and not force: return
        self.conn = mysql.connector.connect(**self.login_info, autocommit=True)
        self.cursor = self.conn.cursor()
        self.execute(f'use {self.database}')

    def quit(self):
        '''
        '''
        self.conn.disconnect()

    '''
    execution
    '''

    def execute(self, query, data=None):
        '''
        '''
        self.connect() # TODO: check latency
        # TODO: exception handling
        if data is None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, data)

    def executemany(self, query, data=None):
        '''
        '''
        self.connect() # TODO: check latency
        # TODO: exception handling
        if data is None:
            self.cursor.executemany(query)
        else:
            self.cursor.executemany(query, data)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    '''
    login
    '''

    def login_verify(self, name, role, access):
        '''
        '''
        query = f'''
            select login_verify('{name}', '{role}', '{access}')
            '''
        self.execute(query)
        return self.fetchone()[0]

    '''
    utilities
    '''

    @root
    def _check_function_exist(self, name):
        '''
        '''
        query = f'''
            select exists(select * from information_schema.routines where routine_type='FUNCTION' and routine_schema='{self.database}' and routine_name='{name}');
            '''
        self.execute(query)
        return self.fetchone()[0]

    @root
    def _check_procedure_exist(self, name):
        '''
        '''
        query = f'''
            select exists(select * from information_schema.routines where routine_type='PROCEDURE' and routine_schema='{self.database}' and routine_name='{name}');
            '''
        self.execute(query)
        return self.fetchone()[0]

    @root
    def _grant_function_access(self, func_name, user_name):
        '''
        '''
        self.execute(f"grant execute on function {self.database}.{func_name} to '{user_name}'@'%'")

    @root
    def _grant_procedure_access(self, proc_name, user_name):
        '''
        '''
        self.execute(f"grant execute on procedure {self.database}.{proc_name} to '{user_name}'@'%'")

    '''
    user
    '''

    @root
    def get_user_list(self, role=None):
        '''
        '''
        if role is None:
            self.execute('select name from _user')
        else:
            self.execute(f"select name from _user where role = '{role}'")
        user_list = [res[0] for res in self.cursor]
        return user_list

    @root
    def get_active_user_list(self, return_host=False, role=None):
        '''
        '''
        user_list = self.get_user_list(role=role)
        active_user_list = []
        active_host_list = []
        self.execute(f"select user, host from information_schema.processlist where db = '{self.database}'")
        for res in self.cursor:
            user, host = res
            if user in user_list:
                active_user_list.append(user)
                active_host_list.append(host)
        if return_host:
            return active_user_list, active_host_list
        else:
            return active_user_list
    
    def get_current_user(self, return_host=False):
        '''
        '''
        user = self.login_info['user']
        if not return_host:
            return user
        host = self.login_info['host']
        if host == 'localhost' or ipaddress.ip_address(host).is_private:
            try:
                host = requests.get('https://checkip.amazonaws.com').text.strip()
            except:
                raise Exception('Cannot identify public IP address, please check internet connection')
        return user, host

    @root
    def check_user_exist(self, name):
        '''
        '''
        user_list = self.get_user_list()
        return name in user_list

    @root
    def create_user(self, name, passwd, role, access):
        '''
        '''
        assert not self.check_user_exist(name), f'user {name} already exists'

        # create user
        try:
            self.execute(f'drop user {name}')
            self.execute('flush privileges')
        except:
            pass
        self.execute(f"create user '{name}'@'%' identified by '{passwd}'")

        # grant table access
        if access == '*':
            for table in self.get_inited_table_list():
                self.execute(f"grant all privileges on {self.database}.{table} to '{name}'@'%'")
        elif access == '':
            pass
        else:
            assert access in self.get_table_list(), f"table {access} doesn't exist"
            if access in self.get_inited_table_list():
                self.execute(f"grant all privileges on {self.database}.{access} to '{name}'@'%'")

        # grant procedure access
        for proc_name, proc_access in get_procedure_access().items():
            if proc_access == 'all' or role.lower() == proc_access:
                self._grant_procedure_access(proc_name=proc_name, user_name=name)
        
        # grant function access
        for func_name, func_access in get_function_access().items():
            if func_access == 'all' or role.lower() == func_access:
                self._grant_function_access(func_name=func_name, user_name=name)

        self.execute('flush privileges')

        self.insert_data(table='_user', column=None, data=(name, passwd, role, access))

    @root
    def update_user(self, name, passwd, role, access):
        '''
        '''
        assert self.check_user_exist(name), f"user {name} doesn't exist"

        self.execute(f"select name, passwd, role, access from _user where name = '{name}'")
        user_info = self.cursor.fetchone()
        if user_info == (name, passwd, role, access): return
        _, old_passwd, _, old_access = user_info

        if old_passwd != passwd:
            self.execute(f"alter user '{name}'@'%' identified by '{passwd}'")

        if old_access != access:
            table_list = self.get_inited_table_list()
            if access == '*':
                for table in table_list:
                    self.execute(f"grant all privileges on {self.database}.{table} to '{name}'@'%'")
            else:
                if old_access == '*':
                    for table in table_list:
                        self.execute(f"revoke all privileges on {self.database}.{table} from '{name}'@'%'")
                elif old_access == '':
                    pass
                else:
                    self.execute(f"revoke all privileges on {self.database}.{old_access} from '{name}'@'%'")
                self.execute(f"grant all privileges on {self.database}.{access} to '{name}'@'%'")
            self.execute('flush privileges')

        self.execute(f'update _user set passwd=%s, role=%s, access=%s where name="{name}"', data=(passwd, role, access))

    @root
    def remove_user(self, name):
        '''
        '''
        user_list = self.get_user_list()
        assert name in user_list, f"user {name} doesn't exist"
        assert name != 'root', 'cannot drop root user'

        self.execute(f'drop user {name}')
        self.execute('flush privileges')

        self.execute(f'delete from _user where name="{name}"')

    '''
    table
    '''

    @root
    def get_inited_table_list(self):
        '''
        '''
        self.execute('show tables')
        table_list = [res[0] for res in self.cursor if res[0] not in self.reserved_tables]
        return table_list

    @root
    def get_table_list(self):
        '''
        '''
        self.execute('select name from _empty_table')
        empty_table_list = [res[0] for res in self.cursor]
        inited_table_lsit = self.get_inited_table_list()
        return inited_table_lsit + empty_table_list

    def check_table_exist(self, name):
        '''
        '''
        assert name not in self.reserved_tables, f'{name} is a reserved table'
        query = f'''
            select check_table_exist('{name}')
            '''
        self.execute(query)
        return self.fetchone()[0]

    def check_inited_table_exist(self, name):
        '''
        '''
        assert name not in self.reserved_tables, f'{name} is a reserved table'
        query = f'''
            select check_inited_table_exist('{name}')
            '''
        self.execute(query)
        return self.fetchone()[0]

    @root
    def _check_reserved_table_exist(self, name):
        '''
        '''
        assert name in self.reserved_tables, f'{name} is not a reserved table'
        self.execute('show tables')
        table_list = [res[0] for res in self.cursor]
        return name in table_list

    def load_table(self, name, column=None):
        '''
        '''
        assert self.check_table_exist(name), f"Table {name} doesn't exist"
        data = self.select_data(name, column)
        if column is None:
            data = [d[1:] for d in data] # omit rowid
        return data

    @root
    def create_table(self, name):
        '''
        '''
        if self.check_table_exist(name):
            raise Exception(f'Table {name} exists')
        self.insert_data(table='_empty_table', column=None, data=[name])

    def init_table(self, name, problem_cfg):
        '''
        '''
        problem_name = problem_cfg['name']
        n_var, n_obj = problem_cfg['n_var'], problem_cfg['n_obj']
        var_type = problem_cfg['type']

        if var_type == 'mixed':
            var_str = ','.join([var_info['type'] for var_info in problem_cfg['var'].values()])
        else:
            var_str = ''

        query = f'''
            call init_table('{name}', '{problem_name}', '{var_type}', '{n_var}', '{n_obj}', '{var_str}')
            '''
        self.execute(query)

        for query in get_trigger_queries(name, n_var, n_obj):
            self.execute(query)

    @root
    def remove_table(self, name):
        '''
        '''
        assert name not in self.reserved_tables
        if self.check_inited_table_exist(name):
            self.execute(f'drop table {name}')
            self.execute(f"update _user set access='' where access='{name}'")
            self.execute(f"delete from _problem_info where name='{name}'")
            self.execute(f"delete from _config where name='{name}'")
        elif self.check_table_exist(name):
            self.execute(f'delete from _empty_table where name="{name}"')
        else:
            raise Exception(f'Table {name} does not exist')

    '''
    problem
    '''

    def query_problem(self, name):
        '''
        '''
        query = f'''
            call query_problem('{name}')
            '''
        self.execute(query)
        result = self.fetchone()
        if result is None:
            return None
        else:
            return result[0]

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
        query = f'''
            call update_config('{name}', "{config_str}")
            '''
        self.execute(query)

    def query_config(self, name):
        '''
        '''
        query = f'''
            select query_config('{name}')
            '''
        self.execute(query)
        config_str = self.fetchone()[0]
        if config_str is None:
            return None
        else:
            config = yaml.load(config_str, Loader=yaml.FullLoader)
            return config

    '''
    entry lock
    '''

    def check_entry(self, name, rowid):
        '''
        '''
        query = f'''
            select check_entry('{name}', {rowid})
            '''
        self.execute(query)
        return self.fetchone()[0]

    def lock_entry(self, name, rowid):
        '''
        '''
        query = f'''
            call lock_entry('{name}', {rowid})
            '''
        self.execute(query)

    def release_entry(self, name, rowid):
        '''
        '''
        query = f'''
            call release_entry('{name}', {rowid})
            '''
        self.execute(query)

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
            query = f"insert into {table} values ({','.join(['%s'] * len(data))})"
        elif type(column) == str:
            query = f"insert into {table} values (%s)"
        else:
            # assert len(column) == len(data), 'length mismatch of keys and values'
            query = f"insert into {table} ({','.join(column)}) values ({','.join(['%s'] * len(data))})"
        self.execute(query, data)

        self.execute('select last_insert_id()')
        rowid = self.fetchone()[0]
        return rowid

    def insert_multiple_data(self, table, column, data, transform=False):
        '''
        '''
        if transform:
            data = self._transform_multiple_data(data)
        if type(data) == np.ndarray:
            data = data.tolist()
        if column is None:
            query = f"insert into {table} values ({','.join(['%s'] * len(data[0]))})"
        elif type(column) == str:
            query = f"insert into {table} values (%s)"
        else:
            # assert len(column) == len(data[0]), 'length mismatch of keys and values'
            query = f"insert into {table} ({','.join(column)}) values ({','.join(['%s'] * len(data[0]))})"
        self.executemany(query, data)

        self.execute('select last_insert_id()')
        rowid = self.fetchone()[0]
        rowids = list(range(rowid, rowid + len(data)))
        return rowids

    def _get_rowid_condition(self, rowid):
        '''
        '''
        if isinstance(rowid, int):
            # update single row
            condition = f' where rowid = {rowid}'
        elif isinstance(rowid, Iterable):
            # update multiple rows
            condition = f' where rowid in ({",".join(np.array(rowid, dtype=str))})'
        elif rowid is None:
            # update all rows
            condition = ''
        else:
            raise NotImplementedError
        return condition

    def update_data(self, table, column, data, rowid=None, transform=False):
        '''
        '''
        if transform:
            data = self._transform_data(data)
        if type(data) == np.ndarray:
            data = data.tolist()

        if type(column) == str:
            query = f"update {table} set {column}=%s"
        else:
            # assert len(column) == len(data), 'length mismatch of keys and values'
            query = f"update {table} set {','.join([col + '=%s' for col in column])}"

        condition = self._get_rowid_condition(rowid)
        query += condition

        self.execute(query, data)

    def update_multiple_data(self, table, column, data, rowid=None, transform=False):
        '''
        '''
        if transform:
            data = self._transform_multiple_data(data)
        if type(data) == np.ndarray:
            data = data.tolist()

        if type(column) == str:
            query = f"update {table} set {column}=%s"
        else:
            # assert len(column) == len(data[0]), 'length mismatch of keys and values'
            query = f"update {table} set {','.join([col + '=%s' for col in column])}"

        if rowid is not None:
            assert isinstance(rowid, Iterable) and len(rowid) == len(data)
            if isinstance(rowid, np.ndarray):
                rowid = rowid.tolist()
            for i in range(len(data)):
                data[i].append(rowid[i])
            query += ' where rowid=%s'
        
        self.executemany(query, data)

    def delete_data(self, table, rowid=None):
        '''
        '''
        condition = self._get_rowid_condition(rowid)
        query = f'delete from {table}' + condition

        self.execute(query)
    
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

        self.execute(query)
        return self.fetchall()

    def get_n_row(self, table):
        '''
        '''
        query = f'select rowid from {table} order by rowid desc limit 1'
        self.execute(query)
        return self.fetchone()[0]

    def get_column_names(self, table):
        '''
        '''
        query = f"select column_name from information_schema.columns where table_name = '{table}' order by ordinal_position"
        self.execute(query)
        column_names = [res[0] for res in self.cursor if res[0] != 'rowid']
        return column_names

    def get_checksum(self, table):
        '''
        '''
        self.connect()
        self.execute(f'checksum table {table}')
        return self.cursor.fetchone()[1]
