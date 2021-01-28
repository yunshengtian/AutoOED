def get_table_descriptions():
    '''
    '''
    descriptions = {

        '_empty_table': '''
            name varchar(50) not null primary key
            ''',

        '_problem_info': '''
            name varchar(50) not null primary key,
            problem_name varchar(50) not null
            ''',

        '_config': '''
            name varchar(50) not null,
            config text not null
            ''',

    }

    return descriptions
