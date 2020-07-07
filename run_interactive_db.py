'''
Run with local tkinter GUI and SQLite for data storage, having more GUI interactions for configurations, control and logging
'''

from problems.common import build_problem
from system.optimize import optimize
from system.evaluate import evaluate
from system.utils import check_pareto, calc_pred_error
from system.database import Database
from system.gui_interactive import InteractiveGUI


# database object
db = None


def init_command(config, data_path):
    '''
    Problem initialization command linked to GUI button click
    '''
    # build problem
    problem, true_pfront, X, Y = build_problem(config['problem'], get_pfront=True, get_init_samples=True)

    # init database
    global db
    db = Database(data_path, problem)
    db.init(X, Y)

    return problem, true_pfront


def optimize_command(worker_id, config, data_path, problem):
    '''
    Optimization command linked to GUI button click
    Worker process of optimization algorithm execution
    '''
    n_var, n_obj = problem.n_var, problem.n_obj

    # run several iterations of algorithm
    for _ in range(config['general']['n_iter']):

        # read current data from database
        select_result = db.select_multiple(
            keys_list=[[f'x{i + 1}' for i in range(n_var)], [f'f{i + 1}' for i in range(n_obj)]])
        X, Y = select_result[0], select_result[1]

        # run optimization
        result_df = optimize(config, X, Y, seed=worker_id)
        # run evaluation
        result_df = evaluate(problem, result_df)
        
        # write optimized data to database
        X = result_df[[f'x{i + 1}' for i in range(n_var)]].to_numpy()
        Y = result_df[[f'f{i + 1}' for i in range(n_obj)]].to_numpy()
        Y_expected = result_df[[f'expected_f{i + 1}' for i in range(n_obj)]].to_numpy()
        Y_uncertainty = result_df[[f'uncertainty_f{i + 1}' for i in range(n_obj)]].to_numpy()
        db.insert(X, Y, Y_expected, Y_uncertainty)


def load_command(config, data_path):
    '''
    Data loading command linked to GUI figure refresh
    '''
    n_var, n_obj = config['problem']['n_var'], config['problem']['n_obj']

    select_result = db.select_multiple(
        keys_list=[[f'x{i + 1}' for i in range(n_var)] + [f'f{i + 1}' for i in range(n_obj)] + ['hv', 'pred_error'], ['is_pareto']],
        dtype_list=[float, bool])
    X, Y, hv_value, pred_error, is_pareto = \
        select_result[0][:, :n_var], \
        select_result[0][:, n_var:n_var + n_obj], \
        select_result[0][:, n_var + n_obj].squeeze(), \
        select_result[0][:, n_var + n_obj + 1].squeeze(), \
        select_result[1].squeeze()
    return X, Y, Y[is_pareto], hv_value, pred_error


def quit_command():
    '''
    Command triggered when GUI quit
    '''
    if db is not None:
        db.quit()


def main():
    gui = InteractiveGUI('db', init_command, optimize_command, load_command, quit_command)
    gui.mainloop()


if __name__ == '__main__':
    main()