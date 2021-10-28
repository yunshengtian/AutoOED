'''
Stopping criteria of the optimization.
'''

from time import time


class StopCriterion:
    '''
    Base class of stopping criterion.
    '''
    def __init__(self, agent, *args, **kwargs):
        '''
        Parameters
        ----------
        agent: autooed.system.agent.LoadAgent
            Agent that talks to algorithms and database.
        '''
        self.agent = agent
        self.started = False

    def start(self):
        '''
        Enable the criterion checking.
        '''
        self.started = True

    def check(self):
        '''
        Check whether the criterion is reached.
        '''
        return False

    def load(self):
        '''
        Load the progress of the criterion.
        '''
        return None


class TimeStopCriterion(StopCriterion):
    '''
    Stopping criterion based on max time.
    '''
    def __init__(self, agent, max_time):
        '''
        Parameters
        ----------
        agent: autooed.system.agent.LoadAgent
            Agent that talks to algorithms and database.
        max_time: float
            Maximum time (in seconds).
        '''
        super().__init__(agent)
        self.start_time = None
        self.max_time = max_time

    def start(self):
        super().start()
        self.start_time = time()

    def check(self):
        if not self.started:
            return False
        return (time() - self.start_time) >= self.max_time

    def load(self):
        if not self.started:
            return self.max_time
        return self.max_time - (time() - self.start_time)


class NIterStopCriterion(StopCriterion):
    '''
    Stopping criterion based on max iteration.
    '''
    def __init__(self, agent, max_iter):
        '''
        Parameters
        ----------
        agent: autooed.system.agent.LoadAgent
            Agent that talks to algorithms and database.
        max_iter: int
            Maximum iteration of optimization.
        '''
        super().__init__(agent)
        self.n_iter = None
        self.max_iter = max_iter

    def start(self):
        super().start()
        self.n_iter = 0

    def check(self):
        if not self.started:
            return False
        self.n_iter += 1
        return self.n_iter >= self.max_iter

    def load(self):
        if not self.started:
            return self.max_iter
        return self.max_iter - self.n_iter


class NSampleStopCriterion(StopCriterion):
    '''
    Stopping criterion based on max number of samples.
    '''
    def __init__(self, agent, max_sample):
        '''
        Parameters
        ----------
        agent: autooed.system.agent.LoadAgent
            Agent that talks to algorithms and database.
        max_sample: int
            Maximum number of samples.
        '''
        super().__init__(agent)
        self.max_sample = max_sample

    def check(self):
        if not self.started:
            return False
        n_sample = self.agent.get_n_valid_sample()
        return n_sample >= self.max_sample

    def load(self):
        return self.max_sample


class HVStopCriterion(StopCriterion):
    '''
    Stopping criterion based on max hypervolume.
    '''
    def __init__(self, agent, max_hv):
        '''
        Parameters
        ----------
        agent: autooed.system.agent.LoadAgent
            Agent that talks to algorithms and database.
        max_hv: float
            Maximum hypervolume.
        '''
        super().__init__(agent)
        self.max_hv = max_hv

    def check(self):
        if not self.started:
            return False
        hv = self.agent.get_max_hv()
        if hv is None: return False
        return hv >= self.max_hv

    def load(self):
        return self.max_hv


class HVConvStopCriterion(StopCriterion):
    '''
    Stopping criterion based on hypervolume convergence.
    '''
    def __init__(self, agent, max_iter):
        '''
        Parameters
        ----------
        agent: autooed.system.agent.LoadAgent
            Agent that talks to algorithms and database.
        max_iter: int
            Maximum iteration for measuring the hypervolume convergence. 
            I.e., convergence happens if hypervolume stops to improve for max_iter iterations.
        '''
        super().__init__(agent)
        self.last_hv = None
        self.n_iter = None
        self.max_iter = max_iter

    def start(self):
        super().start()
        self.last_hv = None
        self.n_iter = 0

    def check(self):
        if not self.started:
            return False
        hv = self.agent.get_max_hv()
        if hv is None: return False
        if hv == self.last_hv:
            self.n_iter += 1
            return self.n_iter >= self.max_iter
        else:
            self.last_hv = hv
            self.n_iter = 0
            return False

    def load(self):
        return self.max_iter


def get_stop_criterion(name):
    '''
    Get stopping criterion by name.
    '''
    stop_criterion = {
        'time': TimeStopCriterion,
        'n_iter': NIterStopCriterion,
        'n_sample': NSampleStopCriterion,
        'hv': HVStopCriterion,
        'hv_conv': HVConvStopCriterion,
    }
    return stop_criterion[name]

def get_name(stop_criterion):
    '''
    Get name of the stopping criterion.
    '''
    name = {
        TimeStopCriterion: 'time',
        NIterStopCriterion: 'n_iter',
        NSampleStopCriterion: 'n_sample',
        HVStopCriterion: 'hv',
        HVConvStopCriterion: 'hv_conv',
    }
    return name[stop_criterion]
