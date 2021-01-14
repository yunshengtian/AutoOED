def get_procedure_queries(database_name):
    '''
    '''
    queries = {

        'init_table': f'''
            create procedure init_table( 
                in name_ varchar(50), in var_type_ varchar(20), in n_var_ int, in n_obj_ int, in n_constr_ int, in minimize_ varchar(100)
            )
            begin
                declare i int;
                declare user_name varchar(50);
                declare done boolean;
                declare user_cur cursor for select name from _user where access='*' or access=name_;
                declare continue handler for not found set done = true;

                set @query = concat('create table ', name_, '(rowid int auto_increment primary key,
                    status varchar(20) not null default "unevaluated",');

                set i = 1;
                while i <= n_var_ do
                    set @query = concat(@query, 'x', i, ' float not null,');
                    set i = i + 1;
                end while;

                set i = 1;
                while i <= n_obj_ do
                    set @query = concat(@query, 'f', i, ' float,');
                    set i = i + 1;
                end while;

                set i = 1;
                while i <= n_obj_ do
                    set @query = concat(@query, 'f', i, '_expected float,');
                    set i = i + 1;
                end while;

                set i = 1;
                while i <= n_obj_ do
                    set @query = concat(@query, 'f', i, '_uncertainty float,');
                    set i = i + 1;
                end while;

                set @query = concat(@query, 'is_pareto boolean, config_id int not null, batch_id int not null)');

                prepare stmt from @query;
                execute stmt;
                deallocate prepare stmt;

                delete from _empty_table where name=name_;
                insert into _problem_info values (name_, var_type_, n_var_, n_obj_, n_constr_, minimize_);

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
                insert into _config (name, config) values (name_, config_);
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
        'query_problem': 'all',
        'update_config': 'scientist',
        'lock_entry': 'all',
        'release_entry': 'all',
    }

    for key, value in access.items():
        access[key] = value.lower()
        assert access[key] in ['all', 'scientist', 'worker']

    return access