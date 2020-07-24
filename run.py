'''
Run with local tkinter GUI and SQLite for data storage, having more GUI interactions for configurations, control and logging
'''

import os
from problems.common import build_problem
from system.core import optimize, predict, evaluate
from system.utils import check_pareto, calc_pred_error
from system.database import Database
from system.agent import Agent
from system.gui import GUI


# global agent object, controlling database-related operations
agent = None


def init_command(config, result_dir):
    '''
    Data storage & agent initialization
    '''
    global agent
    db_path = os.path.join(result_dir, 'data.db')

    # initialize database
    db = Database(db_path)

    # build problem and initial data
    problem, X_init, Y_init = build_problem(config['problem'], get_init_samples=True)

    # initialize agent
    agent = Agent(db, problem)
    agent.init(X_init, Y_init)


def predict_command(config, X_next):
    '''
    Performance prediction of given design variables
    '''
    # read current data from database
    X, Y = agent.select(['X', 'Y'])

    # predict performance of given input X_next
    Y_expected, Y_uncertainty = predict(config, X, Y, X_next)

    return Y_expected, Y_uncertainty


def update_command(config, X_next, Y_expected, Y_uncertainty, config_id):
    '''
    Update given data to database
    '''
    # insert optimization and prediction result to database
    rowids = agent.insert(X_next, Y_expected, Y_uncertainty, config_id)
    
    # run evaluation
    Y_next = evaluate(config, X_next)
    
    # update evaluation result to database
    agent.update(Y_next, rowids)


def optimize_command(config, config_id):
    '''
    Automatic execution of optimization workflow
    '''
    # run several iterations
    for _ in range(config['general']['n_iter']):

        # read current data from database
        X, Y = agent.select(['X', 'Y'])

        # optimize for best X_next
        X_next = optimize(config, X, Y)

        # predict performance of X_next
        Y_expected, Y_uncertainty = predict_command(config, X_next)

        # update X_next related data to database
        update_command(config, X_next, Y_expected, Y_uncertainty, config_id)


def load_command(keys):
    '''
    Data loading command linked to GUI figure refresh
    '''
    # read current data from database
    return agent.select(keys)


def quit_command():
    '''
    Command triggered when GUI quit
    '''
    if agent is not None:
        agent.quit()


def main():
    os.environ['OMP_NUM_THREADS'] = '1'
    gui = GUI(init_command, optimize_command, predict_command, update_command, load_command, quit_command)
    gui.mainloop()


if __name__ == '__main__':
    main()