def get_trigger_queries(table_name, n_var, n_obj):
    '''
    '''
    
    trigger_update_status = f'''
        create trigger update_status_{table_name}
        before update
        on {table_name} for each row
        begin
            declare changed, evaluated boolean;
            declare i int;
            set changed = false, evaluated = true;
        '''

    for i in range(1, n_obj + 1):
        trigger_update_status += f'''
            if (old.f{i} != new.f{i}) then
                set changed = true;
            end if;
            if (new.f{i} is null) then
                set evaluated = false;
            end if;
            '''

    trigger_update_status += f'''
            if changed and evaluated then
                set new.status='evaluated';
            end if;
        end
        '''

    queries = [
        trigger_update_status,
    ]

    return queries

