from abc import ABC, abstractmethod
import numpy as np


class Transformation(ABC):

    def __init__(self, config):
        self.config = config.copy()
        self.n_var = self.config['n_var']
        self.n_var_T = self.n_var
        self.n_obj = self.config['n_obj']

    def do(self, X):
        X = np.array(X, dtype=object)
        return self._do(X)

    def undo(self, X):
        X = np.array(X, dtype=float)
        return self._undo(X)

    def constr(self, X):
        X = np.array(X, dtype=float)
        return self._constr(X)

    @abstractmethod
    def _do(self, X):
        pass

    @abstractmethod
    def _undo(self, X):
        pass

    @abstractmethod
    def _constr(self, X):
        pass
    
class ContinuousTransformation(Transformation):
    
    def _do(self, X):
        return X.astype(float)

    def _undo(self, X):
        return X

    def _constr(self, X):
        return X


class IntegerTransformation(Transformation):

    def _do(self, X):
        return X.astype(float)

    def _undo(self, X):
        return np.round(X).astype(int)

    def _constr(self, X):
        return np.round(X)


class BinaryTransformation(Transformation):

    def _do(self, X):
        return X.astype(float)

    def _undo(self, X):
        return np.clip(np.round(X), 0, 1).astype(int)

    def _constr(self, X):
        return np.clip(np.round(X), 0, 1)


class CategoricalTransformation(Transformation):

    def __init__(self, config):
        super().__init__(config)
        if 'var' in config:
            self.n_var = len(config['var'])
            self.choices = np.array([np.array(var_info['choices'], dtype=object) for var_info in config['var'].values()], dtype=object)
        else:
            self.n_var = config['n_var']
            self.choices = np.array([config['var_choices']] * self.n_var, dtype=object)
        self.offsets = np.cumsum([0] + [len(choices) for choices in self.choices])
        self.n_var_T = self.offsets[-1]

    def _do(self, X):
        n_sample = X.shape[0]
        new_X = np.empty((n_sample, self.n_var_T), dtype=float)
        for i in range(self.n_var):
            idx_begin, idx_end = self.offsets[i], self.offsets[i + 1]
            new_X[:, idx_begin:idx_end] = (X[:, i][:, None] == np.repeat(self.choices[i][None, :], n_sample, axis=0))
        return new_X

    def _undo(self, X):
        n_sample = X.shape[0]
        new_X = np.empty((n_sample, self.n_var), dtype=object)
        for i in range(self.n_var):
            idx_begin, idx_end = self.offsets[i], self.offsets[i + 1]
            X_slice = X[:, idx_begin:idx_end]
            new_X[:, i] = self.choices[i][np.argmax(X_slice, axis=1)]
        return new_X

    def _constr(self, X):
        return np.clip(np.round(X), 0, 1)


class MixedTransformation(Transformation):

    def __init__(self, config):
        super().__init__(config)
        self.n_var = len(config['var'])
        self.types = [var_info['type'] for var_info in config['var'].values()]
        self.choices = []
        self.offsets = [0]
        for var_info in config['var'].values():
            if var_info['type'] == 'categorical':
                self.offsets.append(len(var_info['choices']))
                self.choices.append(np.array(var_info['choices'], dtype=object))
            else:
                self.offsets.append(1)
                self.choices.append(None)
        self.choices = np.array(self.choices, dtype=object)
        self.offsets = np.cumsum(self.offsets)
        self.n_var_T = self.offsets[-1]

    def _do(self, X):
        n_sample = X.shape[0]
        new_X = np.empty((n_sample, self.n_var_T), dtype=float)
        for i in range(self.n_var):
            idx_begin, idx_end = self.offsets[i], self.offsets[i + 1]
            if self.types[i] == 'categorical':
                X_slice = (X[:, i][:, None] == np.repeat(self.choices[i][None, :], n_sample, axis=0))
            else:
                X_slice = X[:, i][:, None].astype(float)
            new_X[:, idx_begin:idx_end] = X_slice
        return new_X

    def _undo(self, X):
        n_sample = X.shape[0]
        new_X = np.empty((n_sample, self.n_var), dtype=object)
        for i in range(self.n_var):
            idx_begin, idx_end = self.offsets[i], self.offsets[i + 1]
            X_slice = X[:, idx_begin:idx_end]
            if self.types[i] == 'categorical':
                new_X[:, i] = self.choices[i][np.argmax(X_slice, axis=1)]
            elif self.types[i] == 'continuous':
                new_X[:, i] = X_slice.T
            elif self.types[i] == 'integer':
                new_X[:, i] = np.round(X_slice.T).astype(int)
            elif self.types[i] == 'binary':
                new_X[:, i] = np.clip(np.round(X_slice.T), 0, 1).astype(int)
            else:
                raise Exception()
        return new_X

    def _constr(self, X):
        n_sample = X.shape[0]
        new_X = np.empty((n_sample, self.n_var_T), dtype=float)
        for i in range(self.n_var):
            idx_begin, idx_end = self.offsets[i], self.offsets[i + 1]
            if self.types[i] in ['categorical', 'binary']:
                X_slice = np.clip(np.round(X[:, idx_begin:idx_end]), 0, 1)
            elif self.types[i] == 'continuous':
                X_slice = X[:, idx_begin:idx_end]
            elif self.types[i] == 'integer':
                X_slice = np.round(X[:, idx_begin:idx_end])
            else:
                raise Exception()
            new_X[:, idx_begin:idx_end] = X_slice
        return new_X


def get_transformation(config):
    '''
    '''
    transformation_map = {
        'continuous': ContinuousTransformation,
        'integer': IntegerTransformation,
        'binary': BinaryTransformation,
        'categorical': CategoricalTransformation,
        'mixed': MixedTransformation,
    }
    return transformation_map[config['type']](config)
