from abc import ABC, abstractmethod
from sklearn.preprocessing import StandardScaler
import numpy as np

'''
Data transformations (normalizations) for fitting surrogate model
'''


### 1-dim scaler

class Scaler(ABC):
    
    def fit(self, X):
        return self

    @abstractmethod
    def transform(self, X):
        pass

    @abstractmethod
    def inverse_transform(self, X):
        pass


class BoundedScaler(Scaler):
    '''
    Scale data to [0, 1] according to bounds
    '''
    def __init__(self, bounds):
        self.bounds = bounds

    def transform(self, X):
        return np.clip((X - self.bounds[0]) / (self.bounds[1] - self.bounds[0]), 0, 1)

    def inverse_transform(self, X):
        return np.clip(X, 0, 1) * (self.bounds[1] - self.bounds[0]) + self.bounds[0]


### 2-dim transformation

class Transformation:

    def __init__(self, x_scaler, y_scaler):
        self.x_scaler = x_scaler
        self.y_scaler = y_scaler

    def fit(self, x, y):
        self.x_scaler = self.x_scaler.fit(x)
        self.y_scaler = self.y_scaler.fit(y)
    
    def do(self, x=None, y=None):
        if x is not None and y is not None:
            return self.x_scaler.transform(x), self.y_scaler.transform(y)
        elif x is not None:
            return self.x_scaler.transform(x)
        elif y is not None:
            return self.y_scaler.transform(y)
        else:
            return None

    def undo(self, x=None, y=None):
        if x is not None and y is not None:
            return self.x_scaler.inverse_transform(x), self.y_scaler.inverse_transform(y)
        elif x is not None:
            return self.x_scaler.inverse_transform(x)
        elif y is not None:
            return self.y_scaler.inverse_transform(y)
        else:
            return None
    

class StandardTransform(Transformation):

    def __init__(self, x_bound):
        super().__init__(
            BoundedScaler(x_bound),
            StandardScaler()
        )

