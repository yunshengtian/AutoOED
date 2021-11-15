import numpy as np

from autooed.problem import build_problem
from autooed.mobo import build_algorithm
from autooed.utils.seed import set_seed
from autooed.utils.initialization import generate_random_initial_samples
from autooed.utils.plot import plot_performance_space, plot_performance_metric

from arguments import get_args


if __name__ == '__main__':

    # load arguments
    args, module_cfg = get_args()

    # set random seed
    set_seed(args.seed)

    # build problem
    problem = build_problem(args.problem)
    print(problem)

    # build algorithm
    algorithm = build_algorithm(args.algo, problem, module_cfg)
    print(algorithm)

    # generate initial random samples
    X = generate_random_initial_samples(problem, args.n_init_sample)
    Y = np.array([problem.evaluate_objective(x) for x in X])

    # optimization
    while len(X) < args.n_total_sample:

        # propose design samples
        X_next = algorithm.optimize(X, Y, None, args.batch_size)

        # evaluate proposed samples
        Y_next = np.array([problem.evaluate_objective(x) for x in X_next])

        # combine into dataset
        X = np.vstack([X, X_next])
        Y = np.vstack([Y, Y_next])

        print(f'{len(X)}/{args.n_total_sample} complete')

    # plot
    plot_performance_space(Y)
    plot_performance_metric(Y, problem.obj_type)
