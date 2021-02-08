.. raw:: html

    <style> .red {color:red} </style>


----------------
Building Problem
----------------

To build a problem to optimize in AutoOED, we need to create a problem configuration by either of the following ways: 
through interactions with GUI or through a configuration file.
Basically, a valid problem configuration should include necessary information of the design space and the performance space.


Build from GUI
--------------

To build a problem interactively from GUI, first click ``Problem->Manage`` from the menu, then the software will enter this window:

.. figure:: ../../_static/placeholder.png

The list of the current problems that have been created is shown on the left. You can click the ``Create`` button under that list to start creating the problem.
And the basic information of the current selected problem is shown on the right.
It is also possible to update the information of the problem after it is created or delete the problem, by clicking ``Update`` and ``Delete`` on the right respectively.

After clicking the ``Create`` button, the window will pop up like this, where you can enter the name and type of the problem 
(here type means the type of the design variables). 

.. figure:: ../../_static/placeholder.png

For different types of problem, the window for entering design space information would be different.
You need to click ``Next`` to enter the information for the design space, and see the following subsections for different problem types respectively.


Design Space
''''''''''''

Continuous / Integer
""""""""""""""""""""

If the design variables are continuous or integer, first you need to set the number of design variables by entering the number in the top entry and clicking the ``Set`` button.
Next, after the window is refreshed, you need to specify the name, lower bound and upper bound of the variables.
For example:

.. figure:: ../../_static/placeholder.png

Then click ``Next`` to move forward.


Binary
""""""

If the design variables are binary, first you need to set the number of design variables by entering the number in the top entry and clicking the ``Set`` button.
Next, after the window is refreshed, you need to specify only the name of the variables.
For example:

.. figure:: ../../_static/placeholder.png

Then click ``Next`` to move forward.


Categorical
"""""""""""

If the design variables are categorical, first you need to set the number of design variables by entering the number in the top entry and clicking the ``Set`` button.
Next, after the window is refreshed, you need to specify only the choices of the variables, where the different choices are separated by commas.
For example:

.. figure:: ../../_static/placeholder.png

Then click ``Next`` to move forward.


Mixed
"""""

If the problem type is mixed, which means the problem involves different types of design variables,
the window looks different than the above ones because you need to specify each design variable separately.
Here is the initial window when no design variable is specified, where the variable list is on the left and the selected variable information is displayed on the right:

.. figure:: ../../_static/placeholder.png

Next, to create a design variable, you can click the ``Create`` button on the left, and entering corresponding information on the right, 
then click ``Save`` to save this variable. You can also delete some created variables through clicking the ``Delete`` button.
Finally it might look like this, for example:

.. figure:: ../../_static/placeholder.png

After all the design variables are specified correctly, click ``Next`` to move forward.


Performance Space
'''''''''''''''''

Now let us specify the information of the performance space. First you need to set the number of objectives by entering the number in the top entry and clicking the ``Set`` button.
Next, after the window is refreshed, you can specify the name, type and reference point of each objective, which are all optional.

.. figure:: ../../_static/placeholder.png

Here the type means whether the objective needs to be minimized or maximized. So the possible values are "min" and "max", and the default value is "min".

The reference point is a point in the performance space based on which to calculate the hypervolume. 
By default if the values are not provided, the reference point will be calculated as the maximal objective value of the initial samples (or minimal if the objectives are being maximized).

Next, if you can provide a script that contains the evaluation function of the objectives, you can link this script to AutoOED by clicking ``Browse`` and select the script at the correct location.
After this, the platform is able to automatically call the evaluation script whenever some points proposed by the optimization algorithm need to be evaluated.

.. role:: red

:red:`(**TODO**: illustrate on how should the performance script be written)`

Otherwise, AutoOED could also work without a written script for performance evaluation, just instead of automatically calling the script, 
the platform will expose the unevaluated design variables directly to you and you will have to do the evaluation manually, and later input the evaluation results back to AutoOED for further optimization.

Then, click ``Next`` to move forward.


Constraints
'''''''''''

Finally, as the last step of building a problem configuration, you need to provide the constraints of the problem if it has constraints, or just click ``Finish`` if there is no constraints.
(For now we only support constraints on the design variables.)

.. figure:: ../../_static/placeholder.png


.. role:: red

:red:`(**TODO**: illustrate on how should the constraint script be written)`

The process of specifying constraints is very straightfoward: first, you only need to input the number of constraints to the top entry, 
then click the ``Browse`` button to link the script that contains the evaluation function of the constraints to AutoOED, 
such that AutoOED will be able to call the evaluation script during the optimization when it needs to evaluate whether the design variables are feasible.

After the constraint information is specified, click ``Finish`` to complete building the problem.


Build from Configuration File
-----------------------------

As an alternative way of building the problem configuration, the configurations could be specified in a YAML file (.yml), which include all the necessary properties of a problem, 
for example, the name of the problem, the number of objectives and constraints, etc. (required values are marked with \*)

.. code-block:: yaml

    name: ... # your problem name*
    # specify properties of design variables here (see sections below)
    n_obj: ... # number of objectives*
    obj_name: ... # name of objectives (default: f1, f2, ...)
    obj_type: ... # type of objectives (choices: min/max) (default: min)
    obj_func: ... # path to objective function (default: null)
    ref_point: ... # reference point of performance space (default: null)
    n_constr: ... # number of constraints (default: 0)
    constr_func: ... # path to constraint function (default: null)

You might notice in the above YAML file it does not include specifications for design space information. 
That is because AutoOED supports multiple different types of design variables including continuous, integer, binary, categorical and mixed variables.
See below for how to specify properties of design variables for different problem types to complete this configuration file.

.. role:: red

:red:`(**TODO**: where to load this YAML file to AutoOED)`


Continuous Problem
''''''''''''''''''

Specify number, name, lower bound and upper bound of variables.

.. code-block:: yaml

    type: continuous
    n_var: ... # number of variables*
    var_name: ... # name of variables (default: x1, x2, ...)
    var_lb: ... # lower bound of variables*
    var_ub: ... # upper bound of variables*

Here the lower/upper bound of variables could either be a single number (if all the variables share the same bounds) or a list of numbers (for each variable separately).


Integer Problem
'''''''''''''''

Specify number, name, lower bound and upper bound of variables.

.. code-block:: yaml

    type: integer
    n_var: ... # number of variables*
    var_name: ... # name of variables (default: x1, x2, ...)
    var_lb: ... # lower bound of variables*
    var_ub: ... # upper bound of variables*

Here the lower/upper bound of variables could either be a single number (if all the variables share the same bounds) or a list of numbers (for each variable separately).


Binary Problem
''''''''''''''

Specify number and name of variables.

.. code-block:: yaml

    type: binary
    n_var: ... # number of variables*
    var_name: ... # name of variables (default: x1, x2, ...)


Categorical Problem
'''''''''''''''''''

If value choices are the same for all variables, specify number, name and choices of variables.

.. code-block:: yaml

    type: categorical
    n_var: ... # number of variables*
    var_name: ... # name of variables (default: x1, x2, ...)
    var_choices: [choice_1, choice_2, ...]  # variable choices*

Otherwise, specify name and choices for each variable separately.

.. code-block:: yaml

    type: categorical
    var: # name and choices of each variable*
        name_1: [choice_1, choice_2, ...]
        name_2: [choice_3, choice_4, ...]
        ...


Mixed Problem
'''''''''''''

Specify different properties for each variable separately.

.. code-block:: yaml

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


Examples
''''''''

Please see more concrete examples of problem configuration files in our github: https://github.com/yunshengtian/AutoOED/tree/master/problem/custom/yaml/examples.