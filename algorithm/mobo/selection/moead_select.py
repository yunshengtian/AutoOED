import numpy as np
from sklearn.cluster import KMeans
from .base import Selection


class MOEADSelect(Selection):
    '''
    Selection method for MOEA/D-EGO algorithm.
    '''
    def select(self, solution, surrogate_model, normalization, curr_pset, curr_pfront): 
        X, G, algo = solution['x'], solution['y'], solution['algo']
        ref_dirs = algo.ref_dirs

        G_s = algo._decomposition.do(G, weights=ref_dirs, ideal_point=algo.ideal_point) # scalarized acquisition value

        # build candidate pool Q
        Q_x, Q_dir, Q_g = [], [], []
        X_added = curr_pset.copy()
        for x, ref_dir, g in zip(X, ref_dirs, G_s):
            if (x != X_added).any(axis=1).all():
                Q_x.append(x)
                Q_dir.append(ref_dir)
                Q_g.append(g)
                X_added = np.vstack([X_added, x])
        Q_x, Q_dir, Q_g = np.array(Q_x), np.array(Q_dir), np.array(Q_g)

        batch_size = min(self.batch_size, len(Q_x)) # in case Q is smaller than batch size

        if batch_size == 0:
            X_next = X[np.random.choice(len(X), self.batch_size, replace=False)]
            X_next = normalization.undo(x=X_next)
            return X_next, None
        
        # k-means clustering on X with weight vectors
        labels = KMeans(n_clusters=batch_size).fit_predict(np.column_stack([Q_x, Q_dir]))

        # select point in each cluster with lowest scalarized acquisition value
        X_next = []
        for i in range(batch_size):
            indices = np.where(labels == i)[0]
            top_idx = indices[np.argmin(Q_g[indices])]
            top_x = normalization.undo(x=Q_x[top_idx])
            X_next.append(top_x)
        X_next = np.array(X_next)

        # when Q is smaller than batch size
        if batch_size < self.batch_size:
            X_rest = X[np.random.choice(len(X), self.batch_size - batch_size, replace=False)]
            X_next = np.vstack([X_next, normalization.undo(x=X_rest)])

        return X_next, None
