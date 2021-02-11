def get_procedure_queries(database_name):
    '''
    '''
    queries = {

        'init_table': f'''
            create procedure init_table( 
                in name_ varchar(50), in problem_name_ varchar(50), in var_type_ varchar(20), in n_var_ int, in n_obj_ int, in var_ varchar(10000)
            )
            begin
                declare i int;
                declare user_name varchar(50);
                declare done boolean;
                declare user_cur cursor for select name from _user where access='*' or access=name_;
                declare continue handler for not found set done = true;

                set @query = concat('create table ', name_, '(rowid int auto_increment primary key,
                    status varchar(20) not null default "unevaluated",');

                if strcmp(var_type_, 'mixed') = 0 then
                    set i = 1;
                    while i <= n_var_ do
                        set @var_type = replace(substring(substring_index(var_, ',', i), length(substring_index(var_, ',', i - 1)) + 1), ',', '');
                        if strcmp(@var_type, 'continuous') = 0 then
                            set @data_type = 'double';
                        elseif strcmp(@var_type, 'integer') = 0 then
                            set @data_type = 'int';
                        elseif strcmp(@var_type, 'binary') = 0 then
                            set @data_type = 'boolean';
                        else
                            set @data_type = 'varchar(50)';
                        end if;
                        set @query = concat(@query, 'x', i, ' ', @data_type, ' not null,');
                        set i = i + 1;
                    end while;
                else
                    if strcmp(var_type_, 'continuous') = 0 then
                        set @data_type = 'double';
                    elseif strcmp(var_type_, 'integer') = 0 then
                        set @data_type = 'int';
                    elseif strcmp(var_type_, 'binary') = 0 then
                        set @data_type = 'boolean';
                    else
                        set @data_type = 'varchar(50)';
                    end if;
                    set i = 1;
                    while i <= n_var_ do
                        set @query = concat(@query, 'x', i, ' ', @data_type, ' not null,');
                        set i = i + 1;
                    end while;
                end if;

                set i = 1;
                while i <= n_obj_ do
                    set @query = concat(@query, 'f', i, ' double,');
                    set i = i + 1;
                end while;

                set i = 1;
                while i <= n_obj_ do
                    set @query = concat(@query, 'f', i, '_expected double,');
                    set i = i + 1;
                end while;

                set i = 1;
                while i <= n_obj_ do
                    set @query = concat(@query, 'f', i, '_uncertainty double,');
                    set i = i + 1;
                end while;

                set @query = concat(@query, 'pareto boolean, config_id int not null, batch_id int not null)');

                prepare stmt from @query;
                execute stmt;
                deallocate prepare stmt;

                delete from _empty_table where name=name_;
                insert into _problem_info values (name_, problem_name_);

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
                select problem_name from _problem_info where name=name_;
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
                in name_ varchar(50), in rowid_ int
            )
            begin
                insert into _lock values (name_, rowid_);
            end
            ''',

        'release_entry': f'''
            create procedure release_entry(
                in name_ varchar(50), in rowid_ int
            )
            begin
                delete from _lock where name=name_ and rowid=rowid_;
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