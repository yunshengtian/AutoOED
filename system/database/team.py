import os
import mysql.connector
import requests
import ipaddress
import numpy as np
from collections.abc import Iterable


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
        self.database = 'openmobo'

        # connect mysql
        self.conn = mysql.connector.connect(**self.login_info, autocommit=True)
        self.cursor = self.conn.cursor()

        # connect database
        if self.check_db_exist(self.database):
            self.execute(f'use {self.database}')
        else:
            self.execute(f'create database {self.database}')
            self.execute(f'use {self.database}')

        self.reserved_tables = ['_user', '_empty_table', '_problem_info', '_lock']
        
        # initialize database utilities
        if user == 'root':
            if not self.check_table_exist('_user'):
                self.create_table(name='_user', description='''
                    name varchar(50) not null primary key,
                    passwd varchar(20),
                    role varchar(10) not null,
                    access varchar(50) not null
                    ''')

            if not self.check_table_exist('_empty_table'):
                self.create_table(name='_empty_table', description='name varchar(50) not null primary key')

            if not self.check_table_exist('_problem_info'):
                self.create_table(name='_problem_info', description='''
                    name varchar(50) not null primary key,
                    var_type varchar(20),
                    n_var int,
                    n_obj int,
                    n_constr int,
                    minimize varchar(100)
                    ''')

            if not self.check_table_exist('_lock'):
                self.create_table(name='_lock', description='''
                    name varchar(50) not null,
                    row int not null
                    ''')
                self.execute('alter table _lock add unique index(name, row)')

            self._create_function_login_verify()
            self._create_procedure_init_table()
            self._create_procedure_update_problem()
            self._create_procedure_query_problem()
            self._create_function_check_entry()
            self._create_procedure_lock_entry()
            self._create_procedure_release_entry()

    def connect(self, force=False):
        '''
        '''
        if self.conn.is_connected() and not force: return
        self.conn = mysql.connector.connect(**self.login_info, autocommit=True)
        self.cursor = self.conn.cursor()
        self.execute(f'use {self.database}')
        
    def check_root(self):
        '''
        '''
        assert self.login_info['user'] == 'root', 'root previlege is needed'

    def check_function_exist(self, name):
        '''
        '''
        query = f'''
            select exists(select * from information_schema.routines where routine_type='function' and routine_schema='{self.database}' and routine_name='{name}');
            '''
        self.execute(query)
        return self.fetchone()[0]

    def check_procedure_exist(self, name):
        '''
        '''
        query = f'''
            select exists(select * from information_schema.routines where routine_type='procedure' and routine_schema='{self.database}' and routine_name='{name}');
            '''
        self.execute(query)
        return self.fetchone()[0]

    def _create_function_login_verify(self):
        '''
        ROOT
        '''
        self.check_root()
        if self.check_function_exist('login_verify'): return
        query = f'''
            create function login_verify( 
                name_ varchar(50), role_ varchar(10), access_ varchar(50)
            )
            returns boolean
            begin
                declare user_exist, init_table_exist, uninit_table_exist boolean;
                select exists(select * from _user where name=name_ and role=role_ and (access=access_ or access='*')) into user_exist;
                select exists(select * from information_schema.tables where table_schema='{self.database}' and table_name=access_) into init_table_exist;
                select exists(select * from _empty_table where name=access_) into uninit_table_exist;
                return user_exist and (init_table_exist or uninit_table_exist);
            end
            '''
        self.execute(query)

    def login_verify(self, name, role, access):
        '''
        '''
        query = f'''
            select login_verify('{name}', '{role}', '{access}')
            '''
        self.execute(query)
        return self.fetchone()[0]

    def _create_procedure_init_table(self):
        '''
        ROOT
        '''
        self.check_root()
        if self.check_procedure_exist('init_table'): return
        query = f'''
            create procedure init_table( 
                in name_ varchar(50), in description_ varchar(10000)
            )
            begin
                declare user_name varchar(50);
                declare done boolean;
                declare user_cur cursor for select name from _user where access='*';
                declare continue handler for not found set done = true;

                set @query = concat('create table ', name_, '(', description_, ')');
                prepare stmt from @query;
                execute stmt;
                deallocate prepare stmt;
                delete from _empty_table where name=name_;
                insert into _problem_info (name) values (name_);

                open user_cur;
                grant_access_loop: loop
                    fetch user_cur into user_name;
                    if done then
                        leave grant_access_loop;
                    end if;
                    set @query = concat('grant all privileges on {self.database}.', name_, ' to ', user_name, "@'%'");
                    prepare stmt from @query;
                    execute stmt;
                    deallocate prepare stmt;
                end loop;
                close user_cur;
            end
            '''
        self.execute(query)

    def init_table(self, name, description):
        '''
        '''
        query = f'''
            call init_table('{name}', "{description}")
            '''
        self.execute(query)

    def _create_procedure_update_problem(self):
        '''
        ROOT
        '''
        self.check_root()
        if self.check_procedure_exist('update_problem'): return
        query = f'''
            create procedure update_problem(
                in name_ varchar(50), in var_type_ varchar(20), in n_var_ int, in n_obj_ int, in n_constr_ int, in minimize_ varchar(100)
            )
            begin
                update _problem_info set var_type=var_type_, n_var=n_var_, n_obj=n_obj_, n_constr=n_constr_, minimize=minimize_ where name=name_;
            end
            '''
        self.execute(query)

    def update_problem(self, name, var_type, n_var, n_obj, n_constr, minimize):
        '''
        '''
        if isinstance(minimize, Iterable):
            minimize = [str(bool(m)) for m in minimize]
            minimize_str = ','.join(minimize)
        else:
            minimize_str = str(bool(minimize))
        query = f'''
            call update_problem('{name}', '{var_type}', '{n_var}', '{n_obj}', '{n_constr}', '{minimize_str}')
            '''
        self.execute(query)

    def _create_procedure_query_problem(self):
        '''
        ROOT
        '''
        self.check_root()
        if self.check_procedure_exist('query_problem'): return
        query = f'''
            create procedure query_problem(
                in name_ varchar(50)
            )
            begin
                select * from _problem_info where name=name_;
            end
            '''
        self.execute(query)

    def query_problem(self, name):
        '''
        '''
        query = f'''
            call query_problem('{name}')
            '''
        self.execute(query)
        result = self.fetchone()
        if result is None:
            var_type, n_var, n_obj, n_constr, minimize = [None] * 5
        else:
            var_type, n_var, n_obj, n_constr, minimize = result[1:]
            if minimize is None:
                pass
            elif ',' in minimize:
                minimize = [m for m in minimize.split(',')]
                for i in range(len(minimize)):
                    if minimize[i] == 'True':
                        minimize[i] = True
                    elif minimize[i] == 'False':
                        minimize[i] = False
                    else:
                        raise NotImplementedError
            else:
                if minimize == 'True':
                    minimize = True
                elif minimize == 'False':
                    minimize = False
                else:
                    raise NotImplementedError
        return {
            'name': name,
            'var_type': var_type,
            'n_var': n_var,
            'n_obj': n_obj,
            'n_constr': n_constr,
            'minimize': minimize,
        }

    def _create_function_check_entry(self):
        '''
        ROOT
        '''
        self.check_root()
        if self.check_function_exist('check_entry'): return
        query = f'''
            create function check_entry(
                name_ varchar(50), row_ int
            )
            returns boolean
            begin
                declare lock_exist boolean;
                select exists(select * from _lock where name=name_ and row=row_) into lock_exist;
                return lock_exist;
            end
            '''
        self.execute(query)

    def check_entry(self, name, row):
        '''
        '''
        query = f'''
            select check_entry('{name}', {row})
            '''
        self.execute(query)
        return self.fetchone()[0]

    def _create_procedure_lock_entry(self):
        '''
        ROOT
        '''
        self.check_root()
        if self.check_procedure_exist('lock_entry'): return
        query = f'''
            create procedure lock_entry(
                in name_ varchar(50), in row_ int
            )
            begin
                insert into _lock values (name_, row_);
            end
            '''
        self.execute(query)

    def lock_entry(self, name, row):
        '''
        '''
        query = f'''
            call lock_entry('{name}', {row})
            '''
        self.execute(query)

    def _create_procedure_release_entry(self):
        '''
        ROOT
        '''
        self.check_root()
        if self.check_procedure_exist('release_entry'): return
        query = f'''
            create procedure release_entry(
                in name_ varchar(50), in row_ int
            )
            begin
                delete from _lock where name=name_ and row=row_;
            end
            '''
        self.execute(query)

    def release_entry(self, name, row):
        '''
        '''
        query = f'''
            call release_entry('{name}', {row})
            '''
        self.execute(query)

    def _grant_function_access(self, func_name, user_name):
        '''
        ROOT
        '''
        self.check_root()
        self.execute(f"grant execute on function {self.database}.{func_name} to '{user_name}'@'%'")

    def _grant_procedure_access(self, proc_name, user_name):
        '''
        ROOT
        '''
        self.check_root()
        self.execute(f"grant execute on procedure {self.database}.{proc_name} to '{user_name}'@'%'")

    def check_db_exist(self, name):
        '''
        '''
        self.execute(f"show databases like '{name}'")
        return self.cursor.fetchone() != None

    def get_user_list(self, role=None):
        '''
        ROOT
        '''
        self.check_root()
        if role is None:
            self.execute('select name from _user')
        else:
            self.execute(f"select name from _user where role = '{role}'")
        user_list = [res[0] for res in self.cursor]
        return user_list

    def get_active_user_list(self, return_host=False, role=None):
        '''
        ROOT
        '''
        self.check_root()
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

    def check_user_exist(self, name):
        '''
        '''
        self.check_root()
        user_list = self.get_user_list()
        return name in user_list

    def create_user(self, name, passwd, role, access):
        '''
        ROOT
        '''
        self.check_root()
        assert not self.check_user_exist(name), f'user {name} already exists'

        # create user
        try:
            self.execute(f'drop user {name}')
            self.execute('flush privileges')
        except:
            pass
        self.execute(f"create user '{name}'@'%' identified by '{passwd}'")

        # grant table access
        table_list = self.get_table_list()
        if access == '*':
            for table in table_list:
                self.execute(f"grant all privileges on {self.database}.{table} to '{name}'@'%'")
        elif access == '':
            pass
        else:
            assert access in table_list, f"table {access} doesn't exist "
            self.execute(f"grant all privileges on {self.database}.{access} to '{name}'@'%'")

        # grant function & procedure access
        for func_name in ['login_verify', 'check_entry']:
            self._grant_function_access(func_name=func_name, user_name=name)
        for proc_name in ['query_problem', 'lock_entry', 'release_entry']:
            self._grant_procedure_access(proc_name=proc_name, user_name=name)
        if role == 'Scientist':
            for proc_name in ['init_table', 'update_problem']:
                self._grant_procedure_access(proc_name=proc_name, user_name=name)

        self.execute('flush privileges')

        self.insert_data(table='_user', column=None, data=(name, passwd, role, access))

    def update_user(self, name, passwd, role, access):
        '''
        ROOT
        '''
        self.check_root()
        assert self.check_user_exist(name), f"user {name} doesn't exist"

        self.execute(f"select name, passwd, role, access from _user where name = '{name}'")
        user_info = self.cursor.fetchone()
        if user_info == (name, passwd, role, access): return
        _, old_passwd, _, old_access = user_info

        if old_passwd != passwd:
            self.execute(f"alter user '{name}'@'%' identified by '{passwd}'")

        if old_access != access:
            table_list = self.get_table_list()
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

        self.update_data(table='_user', column=('passwd', 'role', 'access'), data=(passwd, role, access), condition=f"name = '{name}'")

    def remove_user(self, name):
        '''
        ROOT
        '''
        self.check_root()
        user_list = self.get_user_list()
        assert name in user_list, f"user {name} doesn't exist"
        assert name != 'root', 'cannot drop root user'

        self.execute(f'drop user {name}')
        self.execute('flush privileges')

        self.delete_data(table='_user', condition=f"name = '{name}'")

    def get_table_list(self):
        '''
        '''
        self.execute('show tables')
        table_list = [res[0] for res in self.cursor if res[0] not in self.reserved_tables]
        return table_list

    def check_table_exist(self, name):
        '''
        '''
        self.execute('show tables')
        table_list = [res[0] for res in self.cursor]
        return name in table_list

    def load_table(self, name):
        '''
        '''
        if not (self.check_table_exist(name) or self.check_empty_table_exist(name)):
            raise Exception(f"Table {name} doesn't exist")
        assert name not in self.reserved_tables, f'Cannot load reserved table {name}'

        if self.check_table_exist(name):
            self.execute(f'select * from {name}')
            return self.cursor.fetchall()
        else:
            return None

    def create_table(self, name, description):
        '''
        ROOT
        '''
        self.check_root()
        if self.check_table_exist(name):
            raise Exception(f'Table {name} exists')
        self.execute(f'create table {name} ({description})')
        if name not in self.reserved_tables:
            self.execute(f'insert into _problem_info (name) values ({name})')

    def import_table_from_file(self, name, file_path):
        '''
        '''
        # TODO
        raise NotImplementedError
        # self.check_root()
        # if not os.path.exists(file_path):
        #     raise Exception(f'Table file {file_path} does not exist')
        # self.create_table(name)

    def remove_table(self, name):
        '''
        ROOT
        '''
        self.check_root()
        if not self.check_table_exist(name):
            raise Exception(f'Table {name} does not exist')
        self.execute(f'drop table {name}')
        self.execute(f"update _user set access='' where access='{name}'")
        if name not in self.reserved_tables:
            self.execute(f"delete from _problem_info where name='{name}'")

    def get_empty_table_list(self):
        '''
        ROOT
        '''
        self.check_root()
        self.execute('select name from _empty_table')
        table_list = [res[0] for res in self.cursor]
        return table_list

    def get_all_table_list(self):
        '''
        ROOT
        '''
        self.check_root()
        return self.get_table_list() + self.get_empty_table_list()

    def check_empty_table_exist(self, name):
        '''
        ROOT
        '''
        self.check_root()
        return name in self.get_empty_table_list()

    def create_empty_table(self, name):
        '''
        ROOT
        '''
        self.check_root()
        if self.check_table_exist(name) or self.check_empty_table_exist(name):
            raise Exception(f'Table {name} exists')
        self.insert_data(table='_empty_table', column=None, data=[name])

    def remove_empty_table(self, name):
        '''
        ROOT
        '''
        self.check_root()
        if not self.check_empty_table_exist(name):
            raise Exception(f'Table {name} does not exist')
        self.delete_data(table='_empty_table', condition=f"name = '{name}'")

    def insert_data(self, table, column, data, transform=False):
        '''
        '''
        if transform:
            data = self.transform_data(data)
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

    def insert_multiple_data(self, table, column, data, transform=False):
        '''
        '''
        if transform:
            data = self.transform_multiple_data(data)
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

    def update_data(self, table, column, data, condition, transform=False):
        '''
        '''
        if transform:
            data = self.transform_data(data)
        if type(data) == np.ndarray:
            data = data.tolist()
        if type(column) == str:
            query = f"update {table} set {column}=%s where {condition}"
        else:
            # assert len(column) == len(data), 'length mismatch of keys and values'
            query = f"update {table} set {','.join([col + '=%s' for col in column])} where {condition}"
        self.execute(query, data)

    def update_multiple_data(self, table, column, data, condition, transform=False):
        '''
        '''
        if transform:
            data = self.transform_multiple_data(data)
        if type(data) == np.ndarray:
            data = data.tolist()
        if type(column) == str:
            query = f"update {table} set {column}=%s where {condition}"
        else:
            # assert len(column) == len(data[0]), 'length mismatch of keys and values'
            query = f"update {table} set {','.join([col + '=%s' for col in column])} where {condition}"
        self.executemany(query, data)

    def delete_data(self, table, condition):
        '''
        '''
        self.execute(f'delete from {table} where {condition}')
    
    def transform_data(self, data_list):
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

    def transform_multiple_data(self, data_list):
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

    def select_data(self, table, column, condition=None):
        '''
        '''
        if column is None:
            query = f'select * from {table}'
        elif type(column) == str:
            query = f"select {column} from {table}"
        else:
            query = f"select {','.join(column)} from {table}"
        if condition is not None:
            query += f' where {condition}'
        self.execute(query)
        return self.fetchall()

    def select_first_data(self, table, column, condition=None):
        '''
        '''
        if column is None:
            query = f'select * from {table}'
        elif type(column) == str:
            query = f"select {column} from {table}"
        else:
            query = f"select {','.join(column)} from {table}"
        if condition is not None:
            query += f' where {condition}'
        self.execute(query)
        return self.fetchone()
    
    def select_last_data(self, table, column, condition=None):
        '''
        '''
        if column is None:
            query = f'select * from {table} order by id desc limit 1'
        elif type(column) == str:
            query = f"select {column} from {table} order by id desc limit 1"
        else:
            query = f"select {','.join(column)} from {table} order by id desc limit 1"
        if condition is not None:
            query += f' where {condition}'
        self.execute(query)
        return self.fetchone()

    def get_column_names(self, table):
        '''
        '''
        query = f"select column_name from information_schema.columns where table_name = '{table}'"
        self.execute(query)
        column_names = [res[0] for res in self.cursor]
        return column_names

    # def _execute(self, func, query, data):
    #     '''
    #     '''
    #     self.connect() # TODO: check latency
    #     done = False
    #     curr_try, max_try = 0, 3
    #     while not done and curr_try <= max_try:
    #         try:
    #             if data is None:
    #                 func(query)
    #             else:
    #                 func(query, data)
    #             done = True
    #         except Exception as e:
    #             done = False
    #             curr_try += 1
    #             if curr_try < max_try:
    #                 print(f'Database execution error "{e}"", retrying {curr_try} times')
    #     if curr_try > max_try:
    #         print(f'Database execution error, exceeded max number of retry')

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

    def get_checksum(self, table):
        '''
        '''
        self.connect()
        self.execute(f'checksum table {table}')
        return self.cursor.fetchone()[1]

    def quit(self):
        '''
        '''
        self.conn.disconnect()