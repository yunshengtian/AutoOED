'''
SQLite database operations (compatible with multiprocessing)
'''

import sqlite3
import numpy as np

from .utils import check_pareto


def db_create(db_path, config):
    '''
    Create database based on config file
    '''
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    n_var, n_obj = config['problem']['n_var'], config['problem']['n_obj']
    key_list = [f'x{i + 1} real' for i in range(n_var)] + \
        [f'f{i + 1} real' for i in range(n_obj)] + \
        [f'expected_f{i + 1} real' for i in range(n_obj)] + \
        [f'uncertainty_f{i + 1} real' for i in range(n_obj)] + \
        ['hv real', 'is_pareto boolean']
    cur.execute(f'create table data ({",".join(key_list)})')

    conn.commit()
    conn.close()


def db_init(db_path, hv, X, Y):
    '''
    Initialize database table with initial data X, Y
    '''
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    sample_len, n_var, n_obj = X.shape[0], X.shape[1], Y.shape[1]
    Y_expected = np.zeros((sample_len, n_obj))
    Y_uncertainty = np.zeros((sample_len, n_obj))

    hv_value = np.full(sample_len, hv.calc(Y))
    is_pareto = check_pareto(Y)
    data = np.column_stack([X, Y, Y_expected, Y_uncertainty, hv_value, is_pareto])
    cur.executemany(f'insert into data values ({",".join(["?"] * (n_var + 3 * n_obj + 2))})', data)
    
    conn.commit()
    conn.close()


def db_insert(db_path, hv, X, Y, Y_expected, Y_uncertainty):
    '''
    Insert data into rows of database table
    '''
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    sample_len, n_var, n_obj = X.shape[0], X.shape[1], Y.shape[1]

    Y_keys = [f'f{i + 1}' for i in range(n_obj)]
    cur.execute(f'select {",".join(Y_keys)} from data')
    old_Y = np.array(cur.fetchall())
    all_Y = np.vstack([old_Y, Y])

    hv_value = np.full(sample_len, hv.calc(all_Y))
    is_pareto = np.where(check_pareto(all_Y))[0] + 1
    data = np.column_stack([X, Y, Y_expected, Y_uncertainty, hv_value]).tolist()
    for i in range(len(data)):
        data[i].append(False)
    with conn:
        cur.executemany(f'insert into data values ({",".join(["?"] * (n_var + 3 * n_obj + 2))})', data)
        cur.execute(f'update data set is_pareto = false')
        cur.execute(f'update data set is_pareto = true where rowid in ({",".join(is_pareto.astype(str))})')
    
    conn.commit()
    conn.close()


def db_select(db_path, keys, dtype=float, rowid=None):
    '''
    Query data from database
    '''
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    if rowid is None:
        cur.execute(f'select {",".join(keys)} from data')
    else:
        cur.execute(f'select {",".join(keys)} from data where rowid = {rowid}')
    result = np.array(cur.fetchall(), dtype=dtype)
    
    conn.close()
    return result


def db_multiple_select(db_path, keys_list, dtype_list=None, rowid_list=None):
    '''
    Query multiple types of data from database
    '''
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    if dtype_list is None:
        dtype_list = [float] * len(keys_list)
    if rowid_list is None:
        rowid_list = [None] * len(keys_list)
    assert len(keys_list) == len(dtype_list) == len(rowid_list)

    with conn:
        result_list = []
        for keys, dtype, rowid in zip(keys_list, dtype_list, rowid_list):
            if rowid is None:
                cur.execute(f'select {",".join(keys)} from data')
            else:
                cur.execute(f'select {",".join(keys)} from data where rowid = {rowid}')
            result = np.array(cur.fetchall(), dtype=dtype)
            result_list.append(result)
    
    conn.close()
    return result_list