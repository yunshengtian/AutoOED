'''
ParetoDiscovery multi-objective solver.
'''

import numpy as np
from scipy.optimize import minimize
from scipy.linalg import null_space
from pymoo.model.algorithm import Algorithm
from pymoo.model.duplicate import DefaultDuplicateElimination
from pymoo.model.individual import Individual
from pymoo.model.initialization import Initialization
from pymoo.optimize import minimize as minimize_ea
from multiprocess import Process, Queue, cpu_count

from autooed.utils.sampling import lhs
from autooed.utils.pareto import find_pareto_front
from autooed.mobo.solver.base import Solver
from autooed.mobo.solver.pareto_discovery.buffer import get_buffer
from autooed.mobo.solver.pareto_discovery.utils import propose_next_batch, propose_next_batch_without_label, get_sample_num_from_families


def _local_optimization(x, y, f, eval_func, bounds, constr_func, delta_s):
    '''
    Local optimization of generated stochastic samples by minimizing distance to the target, see section 6.2.3.
    Input:
        x: a design sample, shape = (n_var,)
        y: performance of x, shape = (n_obj,)
        f: relative performance to the buffer origin, shape = (n_obj,)
        eval_func: problem's evaluation function
        bounds: problem's lower and upper bounds, shape = (2, n_var)
        constr_func: problem's constraint evaluation function
        delta_s: scaling factor for choosing reference point in local optimization, see section 6.2.3
    Output:
        x_opt: locally optimized sample x
    '''
    # choose reference point z
    f_norm = np.linalg.norm(f)
    s = 2.0 * f / np.sum(f) - 1 - f / f_norm
    s /= np.linalg.norm(s)
    z = y + s * delta_s * np.linalg.norm(f)

    # optimization objective, see eq(4)
    def fun(x):
        fx = eval_func(x, return_values_of=['F'])
        return np.linalg.norm(fx - z)

    # constraint function
    if constr_func is not None:
        def fun_constr(x):
            return -constr_func(x)

    # jacobian of the objective
    dy = eval_func(x, return_values_of=['dF'])
    if dy is None:
        jac = None
    else:
        def jac(x):
            fx, dfx = eval_func(x, return_values_of=['F', 'dF'])
            return ((fx - z) / np.linalg.norm(fx - z)) @ dfx
    
    # do optimization
    if constr_func is None:
        res = minimize(fun, x, method='L-BFGS-B', jac=jac, bounds=np.array(bounds).T)
    else:
        res = minimize(fun, x, method='SLSQP', jac=jac, bounds=np.array(bounds).T, constraints=({'type': 'ineq', 'fun': fun_constr},))
    x_opt = res.x
    return x_opt


def _get_kkt_dual_variables(F, G, DF, DG):
    '''
    Optimizing for dual variables alpha and beta in KKT conditions, see section 4.2, proposition 4.5.
    Input:
        Given a design sample,
        F: performance value, shape = (n_obj,)
        G: active constraints, shape = (n_active_const,)
        DF: jacobian matrix of performance, shape = (n_obj, n_var)
        DG: jacobian matrix of active constraints, shape = (n_active_const, n_var)
        where n_var = D, n_obj = d, n_active_const = K' in the original paper
    Output:
        alpha_opt, beta_opt: optimized dual variables
    '''
    # NOTE: use min-norm solution for solving alpha then determine beta instead?
    n_obj = len(F)
    n_active_const = len(G) if G is not None else 0

    '''
    Optimization formulation:
        To optimize the last line of (2) in section 4.2, we change it to a quadratic optization problem by:
        find x to let Ax = 0 --> min_x (Ax)^2
        where x means [alpha, beta] and A means [DF, DG].
        Constraints: alpha >= 0, beta >= 0, sum(alpha) = 1.
        NOTE: we currently ignore the constraint beta * G = 0 because G will always be 0 with only box constraints, but add that constraint will result in poor optimization solution (?)
    '''
    if n_active_const > 0: # when there are active constraints

        def fun(x, n_obj=n_obj, DF=DF, DG=DG):
            alpha, beta = x[:n_obj], x[n_obj:]
            objective = alpha @ DF + beta @ DG
            return 0.5 * objective @ objective

        def jac(x, n_obj=n_obj, DF=DF, DG=DG):
            alpha, beta = x[:n_obj], x[n_obj:]
            objective = alpha @ DF + beta @ DG
            return np.vstack([DF, DG]) @ objective

        const = {'type': 'eq', 
            'fun': lambda x, n_obj=n_obj: np.sum(x[:n_obj]) - 1.0, 
            'jac': lambda x, n_obj=n_obj: np.concatenate([np.ones(n_obj), np.zeros_like(x[n_obj:])])}
    
    else: # when there's no active constraint
        
        def fun(x, DF=DF):
            objective = x @ DF
            return 0.5 * objective @ objective

        def jac(x, DF=DF):
            objective = x @ DF
            return DF @ objective

        const = {'type': 'eq', 
                'fun': lambda x: np.sum(x) - 1.0, 
                'jac': np.ones_like}

    # specify different bounds for alpha and beta
    bounds = np.array([[0.0, np.inf]] * (n_obj + n_active_const))
    
    # NOTE: we use random value to initialize alpha for now, maybe consider the location of F we can get a more accurate initialization
    alpha_init = np.random.random(len(F))
    alpha_init /= np.sum(alpha_init)
    beta_init = np.zeros(n_active_const) # zero initialization for beta
    x_init = np.concatenate([alpha_init, beta_init])

    # do optimization using SLSQP
    res = minimize(fun, x_init, method='SLSQP', jac=jac, bounds=bounds, constraints=const)
    x_opt = res.x
    alpha_opt, beta_opt = x_opt[:n_obj], x_opt[n_obj:]
    return alpha_opt, beta_opt


def _get_active_box_const(x, bounds):
    '''
    Getting the indices of active box constraints.
    Input:
        x: a design sample, shape = (n_var,)
        bounds: problem's lower and upper bounds, shape = (2, n_var)
    Output:
        active_idx: indices of all active constraints
        upper_active_idx: indices of upper active constraints
        lower_active_idx: indices of lower active constraints
    '''
    eps = 1e-8 # epsilon value to determine 'active'
    upper_active = bounds[1] - x < eps
    lower_active = x - bounds[0] < eps
    active = np.logical_or(upper_active, lower_active)
    active_idx, upper_active_idx, lower_active_idx = np.where(active)[0], np.where(upper_active)[0], np.where(lower_active)[0]
    return active_idx, upper_active_idx, lower_active_idx


def _get_box_const_value_jacobian_hessian(x, bounds):
    '''
    Getting the value, jacobian and hessian of active box constraints.
    Input:
        x: a design sample, shape = (n_var,)
        bounds: problem's lower and upper bounds, shape = (2, n_var)
    Output:
        G: value of active box constraints (always 0), shape = (n_active_const,)
        DG: jacobian matrix of active box constraints (1/-1 at active locations, otherwise 0), shape = (n_active_const, n_var)
        HG: hessian matrix of active box constraints (always 0), shape = (n_active_const, n_var, n_var)
    '''
    # get indices of active constraints
    active_idx, upper_active_idx, _ = _get_active_box_const(x, bounds)
    n_active_const, n_var = len(active_idx), len(x)

    if n_active_const > 0:
        G = np.zeros(n_active_const)
        DG = np.zeros((n_active_const, n_var))
        for i, idx in enumerate(active_idx):
            constraint = np.zeros(n_var)
            if idx in upper_active_idx:
                constraint[idx] = 1 # upper active
            else:
                constraint[idx] = -1 # lower active
            DG[i] = constraint
        HG = np.zeros((n_active_const, n_var, n_var))
        return G, DG, HG
    else:
        # no active constraints
        return None, None, None


def _get_optimization_directions(x_opt, eval_func, bounds):
    '''
    Getting the directions to explore local pareto manifold.
    Input:
        x_opt: locally optimized design sample, shape = (n_var,)
        eval_func: problem's evaluation function
        bounds: problem's lower and upper bounds, shape = (2, n_var)
    Output:
        directions: local exploration directions for alpha, beta and x (design sample)
    '''
    # evaluate the value, jacobian and hessian of performance
    F, DF, HF = eval_func(x_opt, return_values_of=['F', 'dF', 'hF'])
    
    # evaluate the value, jacobian and hessian of box constraint (NOTE: assume no other types of constraints)
    G, DG, HG = _get_box_const_value_jacobian_hessian(x_opt, bounds)
    
    # KKT dual variables optimization
    alpha, beta = _get_kkt_dual_variables(F, G, DF, DG)

    n_obj, n_var, n_active_const = len(F), len(x_opt), len(G) if G is not None else 0

    # compute H in eq(3) (NOTE: the two forms below are equivalent for box constraint since HG = 0)
    if n_active_const > 0:
        H = HF.T @ alpha + HG.T @ beta
    else:
        H = HF.T @ alpha

    # compute exploration directions (unnormalized) by taking the null space of image in eq(3)
    # TODO: this part is mainly copied from Adriana's implementation, to be checked
    # NOTE: seems useless to solve for d_alpha and d_beta, maybe need to consider all possible situations in null_space computation
    alpha_const = np.concatenate([np.ones(n_obj), np.zeros(n_active_const + n_var)])
    if n_active_const > 0:
        comp_slack_const = np.column_stack([np.zeros((n_active_const, n_obj + n_active_const)), DG])
        DxHx = np.vstack([alpha_const, comp_slack_const, np.column_stack([DF.T, DG.T, H])])
    else:
        DxHx = np.vstack([alpha_const, np.column_stack([DF.T, H])])
    directions = null_space(DxHx)

    # eliminate numerical error
    eps = 1e-8
    directions[np.abs(directions) < eps] = 0.0
    return directions


def _first_order_approximation(x_opt, directions, bounds, constr_func, n_grid_sample):
    '''
    Exploring new samples from local manifold (first order approximation of pareto front).
    Input:
        x_opt: locally optimized design sample, shape = (n_var,)
        directions: local exploration directions for alpha, beta and x (design sample)
        bounds: problem's lower and upper bounds, shape = (2, n_var)
        constr_func: problem's constraint evaluation function
        n_grid_sample: number of samples on local manifold (grid), see section 6.3.1
    Output:
        x_samples: new valid samples from local manifold (grid)
    '''
    n_var = len(x_opt)
    lower_bound, upper_bound = bounds[0], bounds[1]
    active_idx, _, _ = _get_active_box_const(x_opt, bounds)
    n_active_const = len(active_idx)
    n_obj = len(directions) - n_var - n_active_const

    x_samples = np.array([x_opt])

    # TODO: check why unused d_alpha and d_beta here
    d_alpha, d_beta, d_x = directions[:n_obj], directions[n_obj:n_obj + n_active_const], directions[-n_var:]
    eps = 1e-8
    if np.linalg.norm(d_x) < eps: # direction is a zero vector
        return x_samples
    direction_dim = d_x.shape[1]

    if direction_dim > n_obj - 1:
        # more than d-1 directions to explore, randomly choose d-1 sub-directions
        indices = np.random.choice(np.arange(direction_dim), n_obj - 1)
        while np.linalg.norm(d_x[:, indices]) < eps:
            indices = np.random.choice(np.arange(direction_dim), n_obj - 1)
        d_x = d_x[:, indices]
    elif direction_dim < n_obj - 1:
        # less than d-1 directions to explore, do not expand the point
        return x_samples
    
    # normalize direction
    d_x /= np.linalg.norm(d_x)

    # NOTE: Adriana's code also checks if such direction has been expanded, but maybe unnecessary

    # grid sampling on expanded surface (NOTE: more delicate sampling scheme?)
    bound_scale = np.expand_dims(upper_bound - lower_bound, axis=1)
    d_x *= bound_scale
    loop_count = 0 # avoid infinite loop when it's hard to get valid samples
    while len(x_samples) < n_grid_sample:
        # compute expanded samples
        curr_dx_samples = np.sum(np.expand_dims(d_x, axis=0) * np.random.random((n_grid_sample, 1, n_obj - 1)), axis=-1)
        curr_x_samples = np.expand_dims(x_opt, axis=0) + curr_dx_samples
        # check validity of samples
        flags = np.logical_and((curr_x_samples <= upper_bound).all(axis=1), (curr_x_samples >= lower_bound).all(axis=1))
        if constr_func is not None:
            flags = np.logical_and(flags, constr_func(curr_x_samples) <= 0)
        valid_idx = np.where(flags)[0]
        x_samples = np.vstack([x_samples, curr_x_samples[valid_idx]])
        loop_count += 1
        if loop_count > 10:
            break
    x_samples = x_samples[:n_grid_sample]
    return x_samples


def _pareto_discover(xs, eval_func, bounds, constr_func, delta_s, origin, origin_constant, n_grid_sample, queue):
    '''
    Local optimization and first-order approximation.
    (We move these functions out from the ParetoDiscovery class for parallelization)
    Input:
        xs: a batch of samples x, shape = (batch_size, n_var)
        eval_func: problem's evaluation function
        bounds: problem's lower and upper bounds, shape = (2, n_var)
        constr_func: problem's constraint evaluation function
        delta_s: scaling factor for choosing reference point in local optimization, see section 6.2.3
        origin: origin of performance buffer
        origin_constant: when evaluted value surpasses the buffer origin, adjust the origin accordingly and subtract this constant
        n_grid_sample: number of samples on local manifold (grid), see section 6.3.1
        queue: the queue storing results from all processes
    Output (stored in queue):
        x_samples_all: all valid samples from local manifold (grid)
        patch_ids: patch ids for all valid samples (same id when expanded from same x)
        sample_num: number of input samples (needed for counting global patch ids)
        new_origin: new origin point for performance buffer
    '''
    # evaluate samples x and adjust origin accordingly
    ys = eval_func(xs, return_values_of=['F'])
    new_origin = np.minimum(origin, np.min(ys, axis=0))
    if (new_origin != origin).any():
        new_origin -= origin_constant
    fs = ys - new_origin

    x_samples_all = []
    patch_ids = []
    for i, (x, y, f) in enumerate(zip(xs, ys, fs)):

        # local optimization by optimizing eq(4)
        x_opt = _local_optimization(x, y, f, eval_func, bounds, constr_func, delta_s)

        # get directions to expand in local manifold
        directions = _get_optimization_directions(x_opt, eval_func, bounds)

        # get new valid samples from local manifold
        x_samples = _first_order_approximation(x_opt, directions, bounds, constr_func, n_grid_sample)
        x_samples_all.append(x_samples)
        patch_ids.extend([i] * len(x_samples))

    queue.put([np.vstack(x_samples_all), patch_ids, len(xs), new_origin])


class ParetoDiscoveryAlgorithm(Algorithm):
    '''
    The Pareto discovery algorithm introduced by: Schulz, Adriana, et al. "Interactive exploration of design trade-offs." ACM Transactions on Graphics (TOG) 37.4 (2018): 1-14.
    '''
    def __init__(self,
                pop_size=None,
                sampling=None,
                survival=None,
                eliminate_duplicates=DefaultDuplicateElimination(),
                repair=None,
                individual=Individual(),
                n_cell=None,
                cell_size=10,
                buffer_origin=None,
                buffer_origin_constant=1e-2,
                delta_b=0.2,
                label_cost=10,
                delta_p=10,
                delta_s=0.3,
                n_grid_sample=100,
                n_process=cpu_count(),
                **kwargs
                ):
        '''
        Inputs (essential parameters):
            pop_size: population size
            sampling: initial sample data or sampling method to obtain initial population
            n_cell: number of cells in performance buffer
            cell_size: maximum number of samples inside each cell of performance buffer
            buffer_origin: origin of performance buffer
            buffer_origin_constant: when evaluted value surpasses the buffer origin, adjust the origin accordingly and subtract this constant
            delta_b: unary energy normalization constant for sparse approximation, see section 6.4
            label_cost: for reducing number of unique labels in sparse approximation, see section 6.4
            delta_p: factor of perturbation in stochastic sampling, see section 6.2.2
            delta_s: scaling factor for choosing reference point in local optimization, see section 6.2.3
            n_grid_sample: number of samples on local manifold (grid), see section 6.3.1
            n_process: number of processes for parallelization
        '''
        super().__init__(**kwargs)
        
        self.pop_size = pop_size
        self.survival = survival
        self.individual = individual

        if isinstance(eliminate_duplicates, bool):
            if eliminate_duplicates:
                self.eliminate_duplicates = DefaultDuplicateElimination()
            else:
                self.eliminate_duplicates = None
        else:
            self.eliminate_duplicates = eliminate_duplicates

        self.initialization = Initialization(sampling,
                                            individual=individual,
                                            repair=repair,
                                            eliminate_duplicates=self.eliminate_duplicates)

        self.n_gen = None
        self.pop = None
        self.off = None

        self.approx_set = None
        self.approx_front = None
        self.fam_lbls = None
        
        self.buffer = None
        if n_cell is None:
            n_cell = self.pop_size
        self.buffer_args = {'cell_num': n_cell,
                            'cell_size': cell_size,
                            'origin': buffer_origin,
                            'origin_constant': buffer_origin_constant,
                            'delta_b': delta_b,
                            'label_cost': label_cost}

        self.delta_p = delta_p
        self.delta_s = delta_s
        self.n_grid_sample = n_grid_sample
        self.n_process = n_process
        self.patch_id = 0

        self.constr_func = None

    def _initialize(self):
        # create the initial population
        pop = self.initialization.do(self.problem, self.pop_size, algorithm=self)
        pop_x = pop.get('X').copy()

        # check if problem has constraints other than bounds
        pop_constr = self.problem.evaluate_constraint(pop_x)
        if pop_constr is not None:
            self.constr_func = self.problem.evaluate_constraint
            pop = pop[pop_constr <= 0]

            while len(pop) < self.pop_size:
                new_pop = self.initialization.do(self.problem, self.pop_size, algorithm=self)
                new_pop_x = new_pop.get('X').copy()
                new_pop = new_pop[self.problem.evaluate_constraint(new_pop_x) <= 0]
                pop = pop.merge(new_pop)
        
            pop = pop[:self.pop_size]
            pop_x = pop.get('X').copy()

        pop_f = self.problem.evaluate(pop_x, return_values_of=['F'])

        # initialize buffer
        self.buffer = get_buffer(self.problem.n_obj, **self.buffer_args)
        patch_ids = np.full(self.pop_size, self.patch_id) # NOTE: patch_ids here might not make sense
        self.patch_id += 1
        self.buffer.insert(pop_x, pop_f, patch_ids)

        # update population by the best samples in the buffer
        pop = pop.new('X', self.buffer.sample(self.pop_size))

        # evaluate population using the objective function
        self.evaluator.eval(self.problem, pop, algorithm=self)

        # NOTE: check if need survival here
        if self.survival:
            pop = self.survival.do(self.problem, pop, len(pop), algorithm=self)

        self.pop = pop

        # sys.stdout.write('ParetoDiscovery optimizing: generation %i' % self.n_gen)
        # sys.stdout.flush()

    def _next(self):
        '''
        Core algorithm part in each iteration, see algorithm 1.
        --------------------------------------
        xs = stochastic_sampling(B, F, X)
        for x in xs:
            D = select_direction(B, x)
            x_opt = local_optimization(D, F, X)
            M = first_order_approximation(x_opt, F, X)
            update_buffer(B, F(M))
        --------------------------------------
        where F is problem evaluation, X is design constraints
        '''
        # update optimization progress
        # sys.stdout.write('\b' * len(str(self.n_gen - 1)) + str(self.n_gen))
        # sys.stdout.flush()

        # stochastic sampling by adding local perturbance
        xs = self._stochastic_sampling()

        # parallelize core pareto discovery process by multiprocess, see _pareto_discover()
        # including select_direction, local_optimization, first_order_approximation in above algorithm illustration
        x_batch = np.array_split(xs, self.n_process)
        queue = Queue()
        process_count = 0
        for x in x_batch:
            if len(x) > 0:
                p = Process(target=_pareto_discover, 
                    args=(x, self.problem.evaluate, [self.problem.xl, self.problem.xu], self.constr_func, self.delta_s, 
                        self.buffer.origin, self.buffer.origin_constant, self.n_grid_sample, queue))
                p.start()
                process_count += 1

        # gather results (new samples, new patch ids, new origin of performance buffer) from parallel discovery
        new_origin = self.buffer.origin
        x_samples_all = []
        patch_ids_all = []
        for _ in range(process_count):
            x_samples, patch_ids, sample_num, origin = queue.get()
            if x_samples is not None:
                x_samples_all.append(x_samples)
                patch_ids_all.append(np.array(patch_ids) + self.patch_id) # assign corresponding global patch ids to samples
                self.patch_id += sample_num
            new_origin = np.minimum(new_origin, origin)

        # evalaute all new samples and adjust the origin point of buffer
        x_samples_all = np.vstack(x_samples_all)
        y_samples_all = self.problem.evaluate(x_samples_all, return_values_of=['F'])
        new_origin = np.minimum(np.min(y_samples_all, axis=0), new_origin)
        patch_ids_all = np.concatenate(patch_ids_all)

        # update buffer
        self.buffer.move_origin(new_origin)
        self.buffer.insert(x_samples_all, y_samples_all, patch_ids_all)

        # update population by the best samples in the buffer
        self.pop = self.pop.new('X', self.buffer.sample(self.pop_size))
        self.evaluator.eval(self.problem, self.pop, algorithm=self)

    def _stochastic_sampling(self):
        '''
        Stochastic sampling around current population to initialize each iteration to avoid local minima, see section 6.2.2
        '''
        xs = self.pop.get('X').copy()

        # sampling loop
        num_target = xs.shape[0]
        xs_final = np.zeros((0, xs.shape[1]), xs.dtype)

        while xs_final.shape[0] < num_target:
            # generate stochastic direction
            d = np.random.random(xs.shape)
            d /= np.expand_dims(np.linalg.norm(d, axis=1), axis=1)

            # generate random scaling factor
            delta = np.random.random() * self.delta_p

            # generate new stochastic samples
            xs_perturb = xs + 1.0 / (2 ** delta) * d # NOTE: is this scaling form reasonable? maybe better use relative scaling?
            xs_perturb = np.clip(xs_perturb, self.problem.xl, self.problem.xu)

            if self.constr_func is None:
                xs_final = xs_perturb
            else:
                # check constraint values
                constr = self.constr_func(xs_perturb)
                flag = constr <= 0
                if np.any(flag):
                    xs_final = np.vstack((xs_final, xs_perturb[flag]))

        return xs_final[:num_target]

    def propose_next_batch(self, curr_pfront, ref_point, batch_size):
        '''
        Propose next batch to evaluate for active learning. 
        Greedely propose sample with max HV until all families ar visited. Allow only samples with max HV from unvisited family.
        '''
        approx_x, approx_y = self.approx_set, self.approx_front
        labels = self.fam_lbls

        X_next = []
        Y_next = []
        family_lbls = []
        
        if len(approx_x) >= batch_size:
            # approximation result is enough to propose all candidates
            curr_X_next, curr_Y_next, labels_next = propose_next_batch(curr_pfront, ref_point, approx_y, approx_x, batch_size, labels)
            X_next.append(curr_X_next)
            Y_next.append(curr_Y_next)
            family_lbls.append(labels_next)

        else:
            # approximation result is not enough to propose all candidates
            # so propose all result as candidates, and propose others from buffer
            # NOTE: may consider re-expanding manifolds to produce more approximation result, but may not be necessary
            X_next.append(approx_x)
            Y_next.append(approx_y)
            family_lbls.extend(labels)
            remain_batch_size = batch_size - len(approx_x)
            buffer_xs, buffer_ys = self.buffer.flattened()
            prop_X_next, prop_Y_next = propose_next_batch_without_label(curr_pfront, ref_point, buffer_ys, buffer_xs, remain_batch_size)
            X_next.append(prop_X_next)
            Y_next.append(prop_Y_next)
            family_lbls.extend(np.full(remain_batch_size, -1))

        X_next = np.vstack(X_next)
        Y_next = np.vstack(Y_next)
        return X_next, Y_next, family_lbls

    def get_sparse_front(self):
        '''
        Get sparse approximation of Pareto front and set
        '''
        approx_x, approx_y = self.approx_set, self.approx_front
        labels = self.fam_lbls

        return labels, approx_x, approx_y

    def _finalize(self):
        # set population as all samples in performance buffer
        pop_x, pop_y = self.buffer.flattened()
        self.pop = self.pop.new('X', pop_x, 'F', pop_y)
        # get sparse front approximation
        self.fam_lbls, self.approx_set, self.approx_front = self.buffer.sparse_approximation()
        # print()


class ParetoDiscovery(Solver):
    '''
    Solver based on ParetoDiscovery [Schulz et al. 2018].
    NOTE: only compatible with direct selection.
    '''
    def __init__(self, problem, n_gen=10, pop_size=100, n_process=cpu_count(), **kwargs): # TODO: check n_gen
        super().__init__(problem)
        self.n_gen = n_gen
        self.algo = ParetoDiscoveryAlgorithm(pop_size=pop_size, n_process=n_process)

    def _solve(self, X, Y, batch_size):
        # initialize population
        X = np.vstack([X, lhs(X.shape[1], batch_size)])
        self.algo.initialization.sampling = X

        res = minimize_ea(self.problem, self.algo, ('n_gen', self.n_gen))

        X_candidate, Y_candidate = res.pop.get('X'), res.pop.get('F')
        algo = res.algorithm
        
        curr_pfront = find_pareto_front(Y)
        ref_point = np.max(np.vstack([Y, Y_candidate]), axis=0)
        X_candidate, Y_candidate, _ = algo.propose_next_batch(curr_pfront, ref_point, batch_size)

        return X_candidate, Y_candidate
