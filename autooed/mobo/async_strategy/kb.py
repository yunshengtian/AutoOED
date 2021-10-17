'''
'''

from autooed.mobo.async_strategy.base import AsyncStrategy


class KrigingBeliever(AsyncStrategy):
    
    def fit(self, X, Y, X_busy):
        # fit surrogate models based on true data
        self.surrogate_model.fit(X, Y)

        # aggregate believed data
        Y_busy = self.surrogate_model.predict(X_busy)
        X = np.vstack([X, X_busy])
        Y = np.vstack([Y, Y_busy])

        # fit surrogate models based on believed data
        self.surrogate_model.fit(X, Y)

        # fit acquisition functions
        self.acquisition.fit(X, Y)

        return X, Y, self.acquisition
