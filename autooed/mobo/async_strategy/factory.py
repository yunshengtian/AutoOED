'''
Factory of different asynchronous strategies.
'''

from autooed.mobo.async_strategy import *


def get_async_strategy(name):

    async_strategy_map = {
        'kb': KrigingBeliever,
        'lp': LocalPenalizer,
        'bp': BelieverPenalizer,
    }

    if name in async_strategy_map:
        return async_strategy_map[name]
    else:
        raise Exception(f'Undefined asynchronous optimizer {name}')


def init_async_strategy(params, surrogate_model, acquisition):
    assert 'name' in params, 'Name of asynchronous strategy is not specified'
    if params['name'] == 'none': return None
    params = params.copy()
    async_strategy_cls = get_async_strategy(params['name'])
    params.pop('name')
    async_strategy = async_strategy_cls(surrogate_model, acquisition, **params)
    return async_strategy
