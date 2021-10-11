'''
Direct selection.
'''

from autooed.mobo.selection.base import Selection


class Direct(Selection):
    '''
    Directly use candidate designs as selected designs.
    '''
    def _select(self, X_candidate, Y_candidate, X, Y, batch_size):
        assert len(X_candidate) == batch_size, f'Candidate size {len(X_candidate)} != batch size {batch_size}, cannot use direct selection'
        return X_candidate
