def get_procedure_queries(database_name):
    '''
    '''
    queries = {

        'init_table': f'''
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
                insert into _config (name) values (name_);

                open user_cur;
                grant_access_loop: loop
                    fetch user_cur into user_name;
                    if done then
                        leave grant_access_loop;
                    end if;
                    set @query = concat('grant all privileges on {database_name}.', name_, ' to ', user_name, "@'%'");
                    prepare stmt from @query;
                    execute stmt;
                    deallocate prepare stmt;
                end loop;
                close user_cur;
            end
            ''',
        
        'update_problem': f'''
            create procedure update_problem(
                in name_ varchar(50), in var_type_ varchar(20), in n_var_ int, in n_obj_ int, in n_constr_ int, in minimize_ varchar(100)
            )
            begin
                update _problem_info set var_type=var_type_, n_var=n_var_, n_obj=n_obj_, n_constr=n_constr_, minimize=minimize_ where name=name_;
            end
            ''',
        
        'query_problem': f'''
            create procedure query_problem(
                in name_ varchar(50)
            )
            begin
                select * from _problem_info where name=name_;
            end
            ''',

        'update_config': f'''
            create procedure update_config(
                in name_ varchar(50), in config_ text
            )
            begin
                update _config set config=config_ where name=name_;
            end
            ''',

        'lock_entry': f'''
            create procedure lock_entry(
                in name_ varchar(50), in row_ int
            )
            begin
                insert into _lock values (name_, row_);
            end
            ''',

        'release_entry': f'''
            create procedure release_entry(
                in name_ varchar(50), in row_ int
            )
            begin
                delete from _lock where name=name_ and row=row_;
            end
            ''',
    }
    
    return queries


def get_procedure_access():
    '''
    '''
    access = {
        'init_table': 'scientist',
        'update_problem': 'scientist',
        'query_problem': 'all',
        'update_config': 'scientist',
        'lock_entry': 'all',
        'release_entry': 'all',
    }

    for key, value in access.items():
        access[key] = value.lower()
        assert access[key] in ['all', 'scientist', 'worker']

    return access