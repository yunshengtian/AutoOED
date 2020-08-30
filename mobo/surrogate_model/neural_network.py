import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from mobo.surrogate_model.base import SurrogateModel


class MLP(nn.Module):
    '''
    Multi-layer perceptron
    '''
    def __init__(self, n_in, n_out, hidden_sizes, activation):
        '''
        Input:
            n_in: input dimension
            n_out: output dimension
            hidden_sizes: list of sizes of hidden layers
            activation: type of activation function, [relu, tanh] are supported
        '''
        super().__init__()
        
        self.fc = nn.ModuleList()
        last_size = n_in
        for size in hidden_sizes:
            self.fc.append(nn.Linear(last_size, size))
            last_size = size
        self.fc.append(nn.Linear(last_size, n_out))

        ac_map = {
            'relu': F.relu,
            'tanh': F.tanh,
        }
        assert activation in ac_map, f"activation type {activation} doesn't supported"
        self.ac = ac_map[activation]

    def forward(self, x):
        for fc in self.fc[:-1]:
            x = self.ac(fc(x))
        x = self.fc[-1](x)
        return x


def jacobian(outputs, inputs, create_graph=False):
    '''
    Compute the jacobian of `outputs` with respect to `inputs`
    NOTE: here the `outputs` and `inputs` are batched data, meaning that there's no correlation between individuals in a batch
    '''
    batch_size, output_shape, input_shape = outputs.shape[0], outputs.shape[1:], inputs.shape[1:]
    jacs = []
    for i in range(batch_size):
        for output in outputs[i].view(-1):
            jac = torch.autograd.grad(output, inputs, grad_outputs=None, allow_unused=True, retain_graph=True, create_graph=create_graph)[0][i]
            jacs.append(jac)
    return torch.stack(jacs).reshape((batch_size,) + output_shape + input_shape)


def hessian(outputs, inputs):
    '''
    Compute the hessian of `outputs` with respect to `inputs`
    '''
    grad_inputs = jacobian(outputs, inputs, create_graph=True)
    return jacobian(grad_inputs, inputs)


class NeuralNetwork(SurrogateModel):
    '''
    Simple neural network
    '''
    def __init__(self, n_var, n_obj, hidden_sizes=(64, 64), activation='relu', lr=1e-3, weight_decay=1e-4, n_epoch=100, **kwargs):
        super().__init__(n_var, n_obj)

        self.net = [MLP(n_in=n_var, n_out=1, hidden_sizes=hidden_sizes, activation=activation) for _ in range(n_obj)]
        self.criterion = nn.MSELoss()
        self.optimizer = [optim.Adam(net.parameters(), lr=lr, weight_decay=weight_decay) for net in self.net]
        self.n_epoch = n_epoch

    def fit(self, X, Y):
        X, Y = torch.FloatTensor(X), torch.FloatTensor(Y)
        for i in range(self.n_obj):
            for _ in range(self.n_epoch):
                Y_pred = self.net[i](X).squeeze()
                loss = self.criterion(Y_pred, Y[:, i])
                self.optimizer[i].zero_grad()
                loss.backward()
                self.optimizer[i].step()

    def evaluate(self, X, std=False, calc_gradient=False, calc_hessian=False):
        F, dF, hF = [], [], []
        n_sample = X.shape[0] if len(X.shape) > 1 else 1
        X = torch.FloatTensor(X)
        X.requires_grad = True

        F = [self.net[i](X).squeeze() for i in range(self.n_obj)]

        if calc_gradient:
            dF = [jacobian(f, X).numpy() for f in F]
        
        if calc_hessian:
            hF = [hessian(f, X).numpy() for f in F]

        F = [f.detach().numpy() for f in F]
        
        F = np.stack(F, axis=1)
        dF = np.stack(dF, axis=1) if calc_gradient else None
        hF = np.stack(hF, axis=1) if calc_hessian else None

        S = np.zeros((n_sample, self.n_obj)) if std else None
        dS = np.zeros((n_sample, self.n_obj, self.n_var)) if std and calc_gradient else None
        hS = np.zeros((n_sample, self.n_obj, self.n_var, self.n_var)) if std and calc_hessian else None
        
        out = {'F': F, 'dF': dF, 'hF': hF, 'S': S, 'dS': dS, 'hS': hS}
        return out
