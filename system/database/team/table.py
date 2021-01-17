def get_table_descriptions():
    '''
    '''
    descriptions = {

        '_user': '''
            name varchar(50) not null primary key,
            passwd varchar(20),
            role varchar(10) not null,
            access varchar(50) not null
            ''',

        '_empty_table': '''
            name varchar(50) not null primary key
            ''',

        '_problem_info': '''
            name varchar(50) not null primary key,
            var_type varchar(20),
            n_var int,
            n_obj int,
            n_constr int,
            obj_type varchar(100)
            ''',

        '_config': '''
            id int auto_increment primary key,
            name varchar(50) not null,
            config text not null
            ''',

        '_lock': '''
            name varchar(50) not null,
            row int not null
            ''',
    }

    return descriptions


def get_table_post_processes():
    '''
    '''
    post_processes = {

        '_lock': '''
            alter table _lock add unique index(name, row)
            ''',
    }
    
    return post_processes