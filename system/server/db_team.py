import os
import mysql.connector
import requests
import ipaddress


class Database:
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

        # connect mysql
        self.conn = mysql.connector.connect(**self.login_info)
        self.cursor = self.conn.cursor()
        self.database = 'openmobo'

        # connect database
        if self.check_db_exist(self.database):
            self.cursor.execute(f'use {self.database}')
        else:
            self.cursor.execute(f'create database {self.database}')
            self.cursor.execute(f'use {self.database}')
            
        if not self.check_table_exist('user'):
            self.create_table(name='user', description='\
                name varchar(20) not null primary key,\
                passwd varchar(20),\
                role varchar(10) not null,\
                access varchar(20) not null')

        if not self.check_table_exist('empty_table'):
            self.create_table(name='empty_table', description='name varchar(20) not null')

        self.reserved_tables = ['user', 'empty_table']
        
    def check_root(self):
        '''
        '''
        assert self.login_info['user'] == 'root', 'root previlege is needed'

    def check_db_exist(self, name):
        '''
        '''
        self.cursor.execute(f"show databases like '{name}'")
        return self.cursor.fetchone() != None

    def get_user_list(self, role=None):
        '''
        ROOT
        '''
        self.check_root()
        if role is None:
            self.cursor.execute('select name from user')
        else:
            self.cursor.execute(f"select name from user where role = '{role}'")
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
        self.cursor.execute(f"select user, host from information_schema.processlist where db = '{self.database}'")
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

        try:
            self.cursor.execute(f'drop user {name}')
            self.cursor.execute('flush privileges')
        except:
            pass
        self.cursor.execute(f"create user '{name}'@'%' identified by '{passwd}'")

        table_list = self.get_table_list()
        if access == '*':
            for table in table_list:
                self.cursor.execute(f"grant all privileges on {self.database}.{table} to '{name}'@'%'")
        else:
            assert access in table_list, f"table {access} doesn't exist "
            self.cursor.execute(f"grant all privileges on {self.database}.{access} to '{name}'@'%'")
        self.cursor.execute('flush privileges')

        self.insert_data(table='user', column=None, data=(name, passwd, role, access))

    def update_user(self, name, passwd, role, access):
        '''
        ROOT
        '''
        self.check_root()
        assert self.check_user_exist(name), f"user {name} doesn't exist"

        self.cursor.execute(f"select name, passwd, role, access from user where name = '{name}'")
        user_info = self.cursor.fetchone()
        if user_info == (name, passwd, role, access): return
        _, old_passwd, _, old_access = user_info

        if old_passwd != passwd:
            self.cursor.execute(f"alter user '{name}'@'%' identified by '{passwd}'")

        if old_access != access:
            table_list = self.get_table_list()
            if access == '*':
                for table in table_list:
                    self.cursor.execute(f"grant all privileges on {self.database}.{table} to '{name}'@'%'")
            else:
                if old_access == '*':
                    for table in table_list:
                        self.cursor.execute(f"revoke all privileges on {self.database}.{table} from '{name}'@'%'")
                else:
                    self.cursor.execute(f"revoke all privileges on {self.database}.{old_access} from '{name}'@'%'")
                self.cursor.execute(f"grant all privileges on {self.database}.{access} to '{name}'@'%'")
            self.cursor.execute('flush privileges')

        self.update_data(table='user', column=('passwd', 'role', 'access'), data=(passwd, role, access), condition=f"name = '{name}'")

    def remove_user(self, name):
        '''
        ROOT
        '''
        self.check_root()
        user_list = self.get_user_list()
        assert name in user_list, f"user {name} doesn't exist"
        assert name != 'root', 'cannot drop root user'

        self.cursor.execute(f'drop user {name}')
        self.cursor.execute('flush privileges')

        self.delete_data(table='user', condition=f"name = '{name}'")

    def get_table_list(self):
        '''
        ROOT
        '''
        self.check_root()
        self.cursor.execute('show tables')
        table_list = [res[0] for res in self.cursor if res[0] not in self.reserved_tables]
        return table_list

    def check_table_exist(self, name):
        '''
        ROOT
        '''
        self.check_root()
        self.cursor.execute('show tables')
        table_list = [res[0] for res in self.cursor]
        return name in table_list

    def load_table(self, name):
        '''
        '''
        if not (self.check_table_exist(name) or self.check_empty_table_exist(name)):
            raise Exception(f"Table {name} doesn't exist")
        assert name != 'user', 'cannot load user table'

        if self.check_table_exist(name):
            self.cursor.execute(f'select * from {name}')
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
        self.cursor.execute(f'create table {name} ({description})')

        if self.check_empty_table_exist(name):
            self.remove_empty_table(name)

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
        self.cursor.execute(f'drop table {name}')

    def get_empty_table_list(self):
        '''
        ROOT
        '''
        self.check_root()
        self.cursor.execute('select name from empty_table')
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
        self.insert_data(table='empty_table', column=None, data=[name])

    def remove_empty_table(self, name):
        '''
        ROOT
        '''
        self.check_root()
        if not self.check_empty_table_exist(name):
            raise Exception(f'Table {name} does not exist')
        self.delete_data(table='empty_table', condition=f"name = '{name}'")

    def insert_data(self, table, column, data):
        '''
        '''
        if column is None:
            query = f"insert into {table} values ({','.join(['%s'] * len(data))})"
        else:
            assert len(column) == len(data), 'length mismatch of keys and values'
            query = f"insert into {table} ({','.join(column)}) values ({','.join(['%s'] * len(data))})"
        self.cursor.execute(query, data)
        self.conn.commit()

    def insert_multiple_data(self, table, column, data):
        '''
        '''
        if column is None:
            query = f"insert into {table} values ({','.join(['%s'] * len(data[0]))})"
        else:
            assert len(column) == len(data[0]), 'length mismatch of keys and values'
            query = f"insert into {table} ({','.join(column)}) values ({','.join(['%s'] * len(data[0]))})"
        self.cursor.executemany(query, data)
        self.conn.commit()

    def update_data(self, table, column, data, condition):
        '''
        '''
        assert len(column) == len(data), 'length mismatch of keys and values'
        query = f"update {table} set {','.join([col + '=%s' for col in column])} where {condition}"
        self.cursor.execute(query, data)
        self.conn.commit()

    def delete_data(self, table, condition):
        '''
        '''
        self.cursor.execute(f'delete from {table} where {condition}')
        self.conn.commit()
    
    def execute(self, query):
        '''
        '''
        self.cursor.execute(query)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def get_checksum(self, table):
        '''
        '''
        self.cursor.execute(f'checksum table {table}')
        return self.cursor.fetchone()[1]