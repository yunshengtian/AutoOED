# YAML Problem Specifications

Inside the *examples/* folder, we provide examples of problem specifications that belong to different problem types, including *continuous*, *integer*, *binary*, *categorical* and *mixed* types. Although the specification format might be slightly different for each type, generally they look like this:

```yaml
name: ... # your problem name*
# specify properties of design variables here (see sections below)
n_obj: ... # number of objectives*
obj_name: ... # name of objectives (default: f1, f2, ...)
obj_type: ... # type of objectives (choices: min/max) (default: min)
obj_func: ... # path to objective function (default: null)
n_constr: ... # number of constraints (default: 0)
constr_func: ... # path to constraint function (default: null)
# (required values are marked with *)
```

The configurations should be specified in a YAML file (.yml), which include all the necessary properties of a problem, for example, the name of the problem, the number of objectives and constraints, etc. See sections below for how to specify properties of design variables for different problem types.

## Continuous

Specify number, name, lower bound and upper bound of variables.

```yaml
type: continuous
n_var: ... # number of variables*
var_name: ... # name of variables (default: x1, x2, ...)
var_lb: ... # lower bound of variables*
var_ub: ... # upper bound of variables*
```

Here the lower/upper bound of variables could either be a single number (if all the variables share the same bounds) or a list of numbers (for each variable separately).

## Integer

Specify number, name, lower bound and upper bound of variables.

```yaml
type: integer
n_var: ... # number of variables*
var_name: ... # name of variables (default: x1, x2, ...)
var_lb: ... # lower bound of variables*
var_ub: ... # upper bound of variables*
```

Here the lower/upper bound of variables could either be a single number (if all the variables share the same bounds) or a list of numbers (for each variable separately).

## Binary

Specify number and name of variables.

```yaml
type: binary
n_var: ... # number of variables*
var_name: ... # name of variables (default: x1, x2, ...)
```

## Categorical

If value choices are the same for all variables, specify number, name and choices of variables.

```yaml
type: categorical
n_var: ... # number of variables*
var_name: ... # name of variables (default: x1, x2, ...)
var_choices: [choice_1, choice_2, ...]  # variable choices*
```

Otherwise, specify name and choices for each variable separately.

```yaml
type: categorical
var: # name and choices of each variable*
    name_1: [choice_1, choice_2, ...]
    name_2: [choice_3, choice_4, ...]
    ...
```

## Mixed

Specify different properties for each variable separately.

```yaml
type: mixed
var: # name, type and corresponding properties of each variable*
    name_1: # continuous variable specification
        type: continuous
        lb: ... # lower bound*
        ub: ... # upper bound*
    name_2: # integer variable specification
        type: integer
        lb: ... # lower bound*
        ub: ... # upper bound*
    name_3: # binary variable specification
        type: binary
    name_4: # categorical variable specification
        type: categorical
        choices: [choice_1, choice_2, ...] # variable choices*
    ...
```

