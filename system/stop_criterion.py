from time import time


class StopCriterion:

    def __init__(self, agent, *args, **kwargs):
        self.agent = agent

    def start(self):
        '''
        '''
        pass

    def check(self):
        '''
        '''
        return False


class TimeStopCriterion(StopCriterion):

    def __init__(self, agent, max_time):
        super().__init__(agent)
        self.start_time = None
        self.max_time = max_time

    def start(self):
        self.start_time = time()

    def check(self):
        return (time() - self.start_time) >= self.max_time


class NIterStopCriterion(StopCriterion):

    def __init__(self, agent, max_iter):
        super().__init__(agent)
        self.n_iter = None
        self.max_iter = max_iter

    def start(self):
        self.n_iter = 0

    def check(self):
        self.n_iter += 1
        return self.n_iter >= self.max_iter


class NSampleStopCriterion(StopCriterion):

    def __init__(self, agent, max_sample):
        super().__init__(agent)
        self.max_sample = max_sample

    def check(self):
        n_sample = self.agent.get_n_valid_sample()
        return n_sample >= self.max_sample


class HVStopCriterion(StopCriterion):

    def __init__(self, agent, max_hv):
        super().__init__(agent)
        self.max_hv = max_hv

    def check(self):
        hv = self.agent.get_max_hv()
        if hv is None: return False
        return hv >= self.max_hv


class HVConvStopCriterion(StopCriterion):

    def __init__(self, agent, max_iter):
        super().__init__(agent)
        self.last_hv = None
        self.n_iter = None
        self.max_iter = max_iter

    def start(self):
        self.last_hv = None
        self.n_iter = 0

    def check(self):
        hv = self.agent.get_max_hv()
        if hv is None: return False
        if hv == self.last_hv:
            self.n_iter += 1
            return self.n_iter >= self.max_iter
        else:
            self.last_hv = hv
            self.n_iter = 0
            return False


def get_stop_criterion(name):
    '''
    '''
    stop_criterion = {
        'time': TimeStopCriterion,
        'n_iter': NIterStopCriterion,
        'n_sample': NSampleStopCriterion,
        'hv': HVStopCriterion,
        'hv_conv': HVConvStopCriterion,
    }
    return stop_criterion[name]