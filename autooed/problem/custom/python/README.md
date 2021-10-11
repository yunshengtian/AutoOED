# Python Problem Specifications

Inside the *examples/* folder, we provide examples of problem specifications that belong to different problem types, including *continuous*, *integer*, *binary*, *categorical* and *mixed* types. Although the specification format might be slightly different for each type, generally they look like this:

```python
class YourProblemName(Problem):
	config = {
		'name': ..., # your problem name (default: class name)
        '''
        specify properties of design variables here (see sections below)
        '''
        'n_obj': ..., # number of objectives*
        'obj_name': ..., # name of objectives (default: f1, f2, ...)
        'obj_type': ..., # type of objectives (choices: min/max) (default: min)
        'obj_func': ..., # path to objective function (default: None)
        'n_constr': ..., # number of constraints (default: 0)
        'constr_func': ..., # path to constraint function (default: None)
	}
# (required values are marked with *)
```

When you define a new problem, you would inherit the base **Problem** class from *problem/problem.py*, then specify problem configurations in a single *config* dictionary shown as above. The configurations should include all the necessary properties of a problem, for example, the name of the problem, the number of objectives and constraints, etc. See sections below for how to specify properties of design variables for different problem types.

## Continuous

Specify number, name, lower bound and upper bound of variables.

```python
'type': 'continuous',
'n_var': ..., # number of variables*
'var_name': ..., # name of variables (default: x1, x2, ...)
'var_lb': ..., # lower bound of variables*
'var_ub': ..., # upper bound of variables*
```

Here the lower/upper bound of variables could either be a single number (if all the variables share the same bounds) or a list of numbers (for each variable separately).

## Integer

Specify number, name, lower bound and upper bound of variables.

```python
'type': 'integer',
'n_var': ..., # number of variables*
'var_name': ..., # name of variables (default: x1, x2, ...)
'var_lb': ..., # lower bound of variables*
'var_ub': ..., # upper bound of variables*
```

Here the lower/upper bound of variables could either be a single number (if all the variables share the same bounds) or a list of numbers (for each variable separately).

## Binary

Specify number and name of variables.

```python
'type': 'binary',
'n_var': ..., # number of variables*
'var_name': ..., # name of variables (default: x1, x2, ...)
```

## Categorical

If value choices are the same for all variables, specify number, name and choices of variables.

```python
'type': 'categorical',
'n_var': ..., # number of variables*
'var_name': ..., # name of variables (default: x1, x2, ...)
'var_choices': [choice_1, choice_2, ...] # variable choices*
```

Otherwise, specify name and choices for each variable separately.

```python
'type': 'categorical',
'var': {
    name_1: [choice_1, choice_2, ...],
    name_2: [choice_3, choice_4, ...],
    ...
}, # name and choices of each variable*
```

## Mixed

Specify different properties for each variable separately.

```python
'type': 'mixed',
'var': {
    name_1: {
        'type': 'continuous',
        'lb': ..., # lower bound*
        'ub': ..., # upper bound*
    }, # continuous variable specification
    name_2: {
        'type': 'integer',
        'lb': ..., # lower bound*
        'ub': ..., # upper bound*
    }, # integer variable specification
    name_3: {
        'type': 'binary',
    }, # binary variable specification
    name_4: {
        'type': 'categorical',
        'choices': [choice_1, choice_2, ...], # variable choices*
    }, # categorical variable specification
    ...
}, # name, type and corresponding properties of each variable*
```

