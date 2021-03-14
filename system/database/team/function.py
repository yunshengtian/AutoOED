def get_function_queries(database_name):
    '''
    '''
    queries = {

        'login_verify': f'''
            create function login_verify( 
                name_ varchar(50), role_ varchar(10), access_ varchar(50)
            )
            returns boolean
            begin
                declare user_exist, inited_table_exist, empty_table_exist boolean;
                select exists(select * from _user where name=name_ and role=role_ and (access=access_ or access='*')) into user_exist;
                select exists(select * from information_schema.tables where table_schema='{database_name}' and table_name=access_) into inited_table_exist;
                select exists(select * from _empty_table where name=access_) into empty_table_exist;
                return user_exist and (inited_table_exist or empty_table_exist);
            end
            ''',

        'check_table_exist': f'''
            create function check_table_exist(
                name_ varchar(50)
            )
            returns boolean
            begin
                declare inited_table_exist, empty_table_exist boolean;
                select exists(select * from information_schema.tables where table_schema='{database_name}' and table_name=name_) into inited_table_exist;
                select exists(select * from _empty_table where name=name_) into empty_table_exist;
                return inited_table_exist or empty_table_exist;
            end
            ''',

        'check_inited_table_exist': f'''
            create function check_inited_table_exist(
                name_ varchar(50)
            )
            returns boolean
            begin
                return (select exists(select * from information_schema.tables where table_schema='{database_name}' and table_name=name_));
            end
            ''',

        'query_config': f'''
            create function query_config(
                name_ varchar(50)
            )
            returns text
            begin
                return (select config from _config where name=name_ order by id desc limit 1);
            end
            ''',

        'check_entry': f'''
            create function check_entry(
                name_ varchar(50), rowid_ int
            )
            returns boolean
            begin
                return (select exists(select * from _lock where name=name_ and rowid=rowid_));
            end
            ''',
    }

    return queries


def get_function_access():
    '''
    '''
    access = {
        'login_verify': 'all',
        'check_table_exist': 'all',
        'check_inited_table_exist': 'all',
        'query_config': 'all',
        'check_entry': 'all',
    }

    for key, value in access.items():
        access[key] = value.lower()
        assert access[key] in ['all', 'scientist', 'technician']
        
    return access