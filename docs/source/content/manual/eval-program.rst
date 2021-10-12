------------------
Evaluation Program
------------------

AutoOED supports linking to custom evaluation programs such that the whole optimization process can be fully automated without human.
If the evaluation programs are provided and written in a specific way, AutoOED can automatically call it to evaluate the performance or
constraints for some design samples proposed by the optimization algorithm.

In this section, we introduce how should these programs be written (in Python/C/C++/MATLAB) in order to be compatible with AutoOED.
And the format is slightly different for performance evaluation and constraint evaluation.

Note that as a prerequisite for MATLAB programs to work, please follow the additional but necessary `instructions <../getting-started/installation.html#matlab-extension>`_.


Performance Evaluation
----------------------

Suppose our problem has 3 continuous design variables and 2 objectives, the performance evalution program should look like
(note the variable names can be arbitrary):


Python
''''''

.. code-block:: python

   def evaluate_objective(x): # x is a numpy array with length equals to 3
       # some computation goes here
       # f1 = ...
       # f2 = ...
       return f1, f2 # values of the 2 objectives

Note that the name of the function should be exactly **evaluate_objective**.


C/C++
'''''

.. code-block:: c

    float* evaluate_objective(float* x) { // x is a float array with length equals to 3
        static float y[2] = {};
        // some computation goes here
        // y[0] = ...;
        // y[1] = ...;
        return y; // values of the 2 objectives
    }

Note that the name of the function should be exactly **evaluate_objective**.


MATLAB
''''''

.. code-block:: matlab

    function [f1, f2] = your_func_name(x1, x2, x3)
        % some computation goes here
        % f1 = ...;
        % f2 = ...;
    end


Constraint Evaluation
---------------------

Before writing a constraint evaluation program, note that:

- Having a non-positive value means satisfying the constraint, while a positive value means violating the cosntraint.

- AutoOED only supports constraints on design variables rather than performance values, so make sure your constraint values can be computed directly and only from design variables.

- If your problem does not have constraints other than upper and lower bounds, it is not necessary to write this program. Instead, you should specify clearly your upper and lower bounds of the design variables when you create the problem.

Suppose our problem has 3 continuous design variables and 2 constraints, the constraint evalution program should look like
(note the variable names can be arbitrary):


Python
''''''

.. code-block:: python

   def evaluate_constraint(x): # x is a numpy array with length equals to 3
       # some computation goes here
       # g1 = ...
       # g2 = ...
       return g1, g2 # values of the 2 constraints

Note that the name of the function should be exactly **evaluate_constraint**.

C/C++
'''''

.. code-block:: c

    float* evaluate_constraint(float* x) { // x is a float array with length equals to 3
        static float g[2] = {};
        // some computation goes here
        // y[0] = ...;
        // y[1] = ...;
        return g; // values of the 2 constraints
    }

Note that the name of the function should be exactly **evaluate_constraint**.

MATLAB
''''''

.. code-block:: matlab

    function [g1, g2] = your_func_name(x1, x2, x3)
        % some computation goes here
        % g1 = ...;
        % g2 = ...;
    end

