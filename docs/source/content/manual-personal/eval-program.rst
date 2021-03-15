------------------
Evaluation Program
------------------

AutoOED supports linking to custom evaluation programs such that the whole optimization process can be fully automated without human.
If the evaluation programs are provided and written in a specific way, AutoOED can automatically call it to evaluate the performance or
constraints for some design samples proposed by the optimization algorithm.

In this section, we introduce how should these programs be written (in Python/C/C++/MATLAB) in order to be compatible with AutoOED.
And the format is slightly different for performance evaluation and constraint evaluation.


Performance Evaluation
----------------------

Python
''''''


C/C++
'''''


MATLAB
''''''


Constraint Evaluation
---------------------

Before writing a constraint evaluation program, note that:

- AutoOED only supports constraints on design variables rather than performance values, so make sure your constraint values can be computed directly and only from design variables.

- If your problem does not have constraints other than upper and lower bounds, it is not necessary to write this program. Instead, you should specify clearly your upper and lower bounds of the design variables when you create the problem.


Python
''''''


C/C++
'''''


MATLAB
''''''
