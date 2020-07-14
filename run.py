'''
Run with local tkinter GUI and SQLite for data storage, having more GUI interactions for configurations, control and logging
'''

import os
from problems.common import build_problem
from system.optimize import optimize
from system.evaluate import evaluate
from system.utils import check_pareto, calc_pred_error
from system.database import Database
from system.agent import Agent
from system.gui import GUI


# global agent object, controlling database-related operations
agent = None


def init_command(problem, X, Y, result_dir):
    '''
    Data storage initialization command linked to GUI button click
    '''
    global agent
    db_path = os.path.join(result_dir, 'data.db')

    db = Database(db_path)
    agent = Agent(db, problem)
    agent.init(X, Y)


def optimize_command(worker_id, problem, config, config_id):
    '''
    Optimization command linked to GUI button click
    Worker process of optimization algorithm execution
    '''
    # run several iterations of algorithm
    for _ in range(config['general']['n_iter']):

        # read current data from database
        X, Y = agent.select(['X', 'Y'])

        # run optimization
        result_df = optimize(config, X, Y, seed=worker_id)
        # run evaluation
        result_df = evaluate(problem, result_df)
        
        # insert optimized data to database
        agent.insert(result_df, config_id)


def load_command():
    '''
    Data loading command linked to GUI figure refresh
    '''    
    X, Y, hv, pred_error, is_pareto = agent.select(['X', 'Y', 'hv', 'pred_error', 'is_pareto'])
    return X, Y, Y[is_pareto], hv, pred_error


def quit_command():
    '''
    Command triggered when GUI quit
    '''
    if agent is not None:
        agent.quit()


def main():
    gui = GUI(init_command, optimize_command, load_command, quit_command)
    gui.mainloop()


if __name__ == '__main__':
    main()