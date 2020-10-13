from abc import ABC, abstractmethod
import numpy as np
from scipy.spatial import Delaunay
from copy import deepcopy
from pygco import cut_from_graph

from .utils import generate_weights_batch


class BufferBase(ABC):
    '''
    Base class of performance buffer.
    '''
    def __init__(self, cell_num, cell_size=None, origin=None, origin_constant=1e-2, delta_b=0.2, label_cost=0):
        '''
        Input:
            cell_num: number of discretized cells
            cell_size: max sample number within each cell, None means no limit
            origin: the origin point (minimum utopia)
            origin_constant: when the origin point is surpassed by new inserted samples, adjust the origin point and substract this constant
            delta_b: normalization constaint for calculating unary energy in sparse approximation (NOTE: in the paper they also use this to determine appending to buffer or rejection)
            label_cost: for reducing number of unique labels in sparse approximation
        '''
        self.cell_num = cell_num
        self.cell_size = cell_size if cell_size is not None and cell_size > 0 else None
        self.origin = origin
        self.origin_constant = origin_constant

        # sparse approximation related
        self.C_inf = 10
        self.delta_b = delta_b
        self.label_cost = label_cost
        
        # buffer element arrays
        # NOTE: below initializations without prior size could be inefficient in memory access
        self.buffer_x = [[] for _ in range(self.cell_num)]
        self.buffer_y = [[] for _ in range(self.cell_num)]
        self.buffer_dist = [[] for _ in range(self.cell_num)] # stores distance to origin for each sample, exactly the same size as self.buffer
        self.buffer_patch_id = [[] for _ in range(self.cell_num)] # stores the index of manifold (patch) that each sample belongs to
        
        self.sample_count = 0
        
    @abstractmethod
    def _find_cell_id(self, F):
        '''
        Find corresponding cell indices given normalized performance.
        Input:
            F: a batch of normalized performance
        Output:
            cell_ids: a batch of cell indices
        '''
        pass

    def insert(self, X, Y, patch_ids):
        '''
        Insert samples (X, Y) into buffer, which come from manifolds (patches) indexed by 'patch_ids'
        '''
        # normalize performance
        X, Y = np.array(X), np.array(Y)
        self.move_origin(np.min(Y, axis=0))
        F = Y - self.origin

        # calculate corresponding cell index
        dists = np.linalg.norm(F, axis=1)
        cell_ids = self._find_cell_id(F)

        # insert into buffer
        for x, y, cell_id, dist, patch_id in zip(X, Y, cell_ids, dists, patch_ids):
            self.buffer_x[cell_id].append(x)
            self.buffer_y[cell_id].append(y)
            self.buffer_dist[cell_id].append(dist)
            self.buffer_patch_id[cell_id].append(patch_id)
        self.sample_count += len(X)

        # update cells
        for cell_id in np.unique(cell_ids):
            self._update_cell(cell_id)

    def sample_old(self, n):
        '''
        Sample n samples in current buffer with best performance. (Deprecated)
        '''
        # TODO: check if it's proper to repeatedly sample the best one without considering others
        selected_cell_ids = []
        nonempty_cell_ids = [i for i in range(self.cell_num) if len(self.buffer_dist[i]) > 0]
        n_nonempty_cells = len(nonempty_cell_ids) # number of non-empty cells

        # while n >= n_nonempty_cells, we select all non-empty cells
        selected_cell_ids.extend((n // n_nonempty_cells) * nonempty_cell_ids)
        # when n < n_nonempty_cells, we select non-empty cells randomly
        selected_cell_ids.extend(list(np.random.choice(nonempty_cell_ids, size=n % n_nonempty_cells, replace=False)))

        # get the best solution in each cell
        selected_cells = np.array(self.buffer_x)[np.array(selected_cell_ids)]
        selected_samples = [cell[0] for cell in selected_cells]

        return np.array(selected_samples)

    def sample(self, n):
        '''
        Sample n samples in current buffer with best performance. (Active)
        '''
        nonempty_cell_ids = [i for i in range(self.cell_num) if len(self.buffer_dist[i]) > 0]

        # when n is less than number of non-empty cells, randomly pick the 1st samples in cells
        if n <= len(nonempty_cell_ids):
            selected_cell_ids = np.random.choice(nonempty_cell_ids, size=n, replace=False)
            selected_samples = [cell[0] for cell in np.array(self.buffer_x)[selected_cell_ids]]
        
        # when n is greater, pick samples in cells round by round (1st, 2nd, ...)
        else:
            k = 0
            selected_samples = []
            while len(selected_samples) < n:
                # find cells need to be sampled in current round
                nonempty_cell_ids = [i for i in range(self.cell_num) if len(self.buffer_dist[i]) > k]

                if len(nonempty_cell_ids) == 0: # when total number of samples in buffer is less than sample number
                    random_indices = np.random.choice(np.arange(len(selected_samples)), size=(n - len(selected_samples)))
                    selected_samples = np.vstack([selected_samples, np.array(selected_samples)[random_indices]])
                    break
                
                curr_selected_samples = [cell[k] for cell in np.array(self.buffer_x)[nonempty_cell_ids]]
                selected_samples.extend(np.random.permutation(curr_selected_samples))
            selected_samples = np.array(selected_samples[:n])
        return selected_samples

    def move_origin(self, y_min):
        '''
        Move the origin point when y_min surpasses it, redistribute current buffer storage accordingly
        '''
        if (y_min >= self.origin).all() and not (y_min == self.origin).any(): return

        self.origin = np.minimum(self.origin, y_min) - self.origin_constant

        old_buffer_x, old_buffer_y = deepcopy(self.buffer_x), deepcopy(self.buffer_y)
        old_buffer_patch_id = deepcopy(self.buffer_patch_id)
        self.buffer_x, self.buffer_y, self.buffer_dist, self.buffer_patch_id = [[[] for _ in range(self.cell_num)] for _ in range(4)]
        self.sample_count = 0

        for cell_x, cell_y, cell_patch_id in zip(old_buffer_x, old_buffer_y, old_buffer_patch_id):
            if len(cell_x) > 0:
                self.insert(cell_x, cell_y, cell_patch_id)

    def _update_cell(self, cell_id):
        '''
        Sort particular cell according to distance to origin, and only keep self.cell_size samples in the cell
        '''
        if len(self.buffer_dist[cell_id]) == 0: return

        idx = np.argsort(self.buffer_dist[cell_id])
        if self.cell_size is not None:
            self.sample_count -= max(len(idx) - self.cell_size, 0)
            idx = idx[:self.cell_size]

        # TODO: check if time-consuming here
        self.buffer_x[cell_id], self.buffer_y[cell_id], self.buffer_dist[cell_id], self.buffer_patch_id[cell_id] = \
            map(lambda x: list(np.array(x)[idx]), 
                [self.buffer_x[cell_id], self.buffer_y[cell_id], self.buffer_dist[cell_id], self.buffer_patch_id[cell_id]])

    @abstractmethod
    def _get_graph_edges(self, valid_cells):
        '''
        Get the edge information of connectivity graph of buffer cells for graph-cut.
        Used for sparse_approximation(), see section 6.4.
        Input:
            valid_cells: non-empty cells that can be formulated as vertices in the graph
        Output:
            edges: edge array of the input vertices, where an edge is represented by two vertices, shape = (n_edges, 2)
        '''
        pass

    def sparse_approximation(self):
        '''
        Use a few manifolds to sparsely approximate the pareto front by graph-cut, see section 6.4.
        Output:
            labels: the optimized labels (manifold index) for each non-empty cell (the cells also contain the corresponding labeled sample), shape = (n_label,)
            approx_x: the labeled design samples, shape = (n_label, n_var)
            approx_y: the labeled performance values, shape = (n_label, n_obj)
        '''
        # update patch ids, remove non-existing ids previously removed from buffer
        mapping = {}
        patch_id_count = 0
        for cell_id in range(self.cell_num):
            if self.buffer_patch_id[cell_id] == []: continue
            curr_patches = self.buffer_patch_id[cell_id]
            for i in range(len(curr_patches)):
                if curr_patches[i] not in mapping:
                    mapping[curr_patches[i]] = patch_id_count
                    patch_id_count += 1
                self.buffer_patch_id[cell_id][i] = mapping[curr_patches[i]]

        # construct unary and pairwise energy (cost) matrix for graph-cut
        # NOTE: delta_b should be set properly
        valid_cells = np.where([self.buffer_dist[cell_id] != [] for cell_id in range(self.cell_num)])[0] # non-empty cells
        n_node = len(valid_cells)
        n_label = patch_id_count
        unary_cost = self.C_inf * np.ones((n_node, n_label))
        pairwise_cost = -self.C_inf * np.eye(n_label)

        for i, idx in enumerate(valid_cells):
            patches, distances = np.array(self.buffer_patch_id[idx]), np.array(self.buffer_dist[idx])
            min_dist = np.min(distances)
            unary_cost[i, patches] = np.minimum((distances - min_dist) / self.delta_b, self.C_inf)
        
        # get edge information (graph structure)
        edges = self._get_graph_edges(valid_cells)

        # NOTE: pygco only supports int32 as input, due to potential numerical error
        edges, unary_cost, pairwise_cost, label_cost = \
            edges.astype(np.int32), unary_cost.astype(np.int32), pairwise_cost.astype(np.int32), np.int32(self.label_cost)
        
        # do graph-cut, optimize labels for each valid cell
        labels_opt = cut_from_graph(edges, unary_cost, pairwise_cost, label_cost)

        # find corresponding design and performance values of optimized labels for each valid cell
        approx_xs, approx_ys = [], []
        labels = [] # for a certain cell, there could be no sample belongs to that label, probably due to the randomness of sampling or improper energy definition
        for idx, label in zip(valid_cells, labels_opt):
            for cell_patch_id, cell_x, cell_y in zip(self.buffer_patch_id[idx], self.buffer_x[idx], self.buffer_y[idx]):
                # since each buffer element array is sorted based on distance to origin
                if cell_patch_id == label:
                    approx_xs.append(cell_x)
                    approx_ys.append(cell_y)
                    labels.append(label)
                    break
            else: # TODO: check
                approx_xs.append(self.buffer_x[idx][0])
                approx_ys.append(self.buffer_y[idx][0])
                labels.append(label)
        approx_xs, approx_ys = np.array(approx_xs), np.array(approx_ys)

        # NOTE: uncomment code below to show visualization of graph cut
        # import matplotlib.pyplot as plt
        # from matplotlib import cm
        # cmap = cm.get_cmap('tab20', patch_id_count)
        # fig, axs = plt.subplots(1, 2, sharex=True, sharey=True)
        # buffer_ys = np.vstack([np.vstack(cell_y) for cell_y in self.buffer_y if cell_y != []])
        # buffer_patch_ids = np.concatenate([cell_patch_id for cell_patch_id in np.array(self.buffer_patch_id)[valid_cells]])
        # colors = [cmap(patch_id) for patch_id in buffer_patch_ids]
        # axs[0].scatter(*buffer_ys.T, s=10, c=colors)
        # axs[0].set_title('Before graph cut')
        # colors = [cmap(label) for label in labels]
        # axs[1].scatter(*approx_ys.T, s=10, c=colors)
        # axs[1].set_title('After graph cut')
        # fig.suptitle(f'Sparse approximation, # patches: {patch_id_count}, # families: {len(np.unique(labels))}')
        # plt.show()

        return labels, approx_xs, approx_ys

    def flattened(self):
        '''
        Return flattened x and y arrays from all the cells.
        '''
        flattened_x, flattened_y = [], []
        for cell_x, cell_y in zip(self.buffer_x, self.buffer_y):
            if cell_x != []:
                flattened_x.append(cell_x)
            if cell_y != []:
                flattened_y.append(cell_y)
        return np.concatenate(flattened_x), np.concatenate(flattened_y)


class Buffer2D(BufferBase):
    '''
    2D performance buffer.
    '''
    def __init__(self, cell_num, *args, **kwargs):
        if cell_num is None: cell_num = 100
        super().__init__(cell_num, *args, **kwargs)
        if self.origin is None:
            self.origin = np.zeros(2)
        self.dtheta = np.pi / 2.0 / self.cell_num

    def _find_cell_id(self, F):
        dist = np.linalg.norm(F, axis=1)
        theta = np.arccos(F[:, 0] / dist)
        cell_ids = theta / self.dtheta
        cell_ids = np.minimum(cell_ids.astype(int), self.cell_num - 1)
        return cell_ids

    def _get_graph_edges(self, valid_cells):
        # get edges by connecting neighbor cells
        edges = np.array([[i, i + 1] for i in range(len(valid_cells) - 1)])
        return edges


class Buffer3D(BufferBase):
    '''
    3D performance buffer.
    '''
    def __init__(self, cell_num, *args, origin=None, **kwargs):
        if cell_num is None: cell_num = 1000
        super().__init__(cell_num, *args, origin=origin, **kwargs)
        if self.origin is None:
            self.origin = np.zeros(3)
        # it's really hard to generate evenly distributed unit vectors in 3d space, use some tricks here
        edge_cell_num = int(np.sqrt(2 * cell_num + 0.25) + 0.5) - 1
        cell_vecs = generate_weights_batch(n_dim=3, delta_weight=1.0 / (edge_cell_num - 1))
        if len(cell_vecs) < cell_num:
            random_vecs = np.random.random((cell_num - len(cell_vecs), 3))
            cell_vecs = np.vstack([cell_vecs, random_vecs])
        self.cell_vecs = cell_vecs / np.linalg.norm(cell_vecs, axis=1)[:, None]

    def _find_cell_id(self, F):
        dots = F @ self.cell_vecs.T
        cell_ids = np.argmax(dots, axis=1)
        return cell_ids

    def _get_graph_edges(self, valid_cells):

        # NOTE: uncomment code below to show visualization of buffer
        # import matplotlib.pyplot as plt
        # from mpl_toolkits.mplot3d import Axes3D
        # fig = plt.figure()
        # ax = fig.add_subplot(111, projection='3d')
        # ax.view_init(azim=45)
        # for vec in self.cell_vecs:
        #     ax.plot(*np.array([self.origin, self.origin + vec]).T, color='gray', linewidth=1, alpha=0.5)
        # for cell_y in self.buffer_y:
        #     if cell_y == []: continue
        #     ax.scatter(*np.array(cell_y).T)
        # plt.title(f'# samples: {self.sample_count}, # valid cells: {len(valid_cells)}')
        # plt.show()

        # TODO: corner cases, need to check why they happen
        if len(valid_cells) == 1:
            raise Exception('only 1 non-empty cell in buffer, cannot do graph cut')
        elif len(valid_cells) == 2:
            return np.array([[0, 1]])
        elif len(valid_cells) == 3:
            return np.array([[0, 1], [0, 2], [1, 2]])

        # triangulate endpoints of cell vectors to form a mesh, then get edges from this mesh
        vertices = self.cell_vecs[valid_cells]

        # check if vertices fall on a single line
        check_equal = (vertices == vertices[0]).all(axis=0)
        if check_equal.any():
            indices = np.argsort(vertices[:, np.where(np.logical_not(check_equal))[0][0]])
            edges = np.array([indices[:-1], indices[1:]]).T
            edges = np.ascontiguousarray(edges)
            return edges

        tri = Delaunay(vertices)
        ind, all_neighbors = tri.vertex_neighbor_vertices
        edges = []
        for i in range(len(vertices)):
            neighbors = all_neighbors[ind[i]:ind[i + 1]]
            for j in neighbors:
                edges.append(np.sort([i, j]))
        edges = np.unique(edges, axis=0)
        return edges


def get_buffer(n_obj, *args, **kwargs):
    '''
    Select buffer according to n_obj.
    '''
    buffer_map = {2: Buffer2D, 3: Buffer3D}
    if n_obj in buffer_map:
        return buffer_map[n_obj](*args, **kwargs)
    else:
        raise NotImplementedError
