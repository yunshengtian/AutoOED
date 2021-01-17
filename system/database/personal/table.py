def get_table_descriptions():
    '''
    '''
    descriptions = {

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
            name varchar(50) not null,
            config text not null
            ''',

    }

    return descriptions
