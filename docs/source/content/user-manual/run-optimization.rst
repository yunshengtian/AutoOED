--------------------
Running Optimization
--------------------

After setting up the experiment configurations, you should be able to see the initial samples in the performance space from the main window.

.. figure:: ../../_static/placeholder.png

Now you are ready to run the optimization, based on this initial set of data.

There are two modes of optimization: manual mode and auto mode.


Manual Mode
'''''''''''

Manual mode runs optimization only for a single iteration, which suits the scenario when user do not have the performance evaluation script linked to AutoOED.

In each iteration, the user need to first set the proper batch size, then click the ``Optimize`` button to start the algorithm.

.. figure:: ../../_static/placeholder.png

Then after the algorithm proposes a batch of samples to evaluate, the user manually evaluate the performance of these samples, and put the evaluated result back to AutoOED.

.. figure:: ../../_static/placeholder.png


Auto Mode
'''''''''

Auto mode could run optimization for multiple iterations, and is recommended when user have the performance evalaution script linked to AutoOED.

First, the user need to set the proper batch size and the stopping criterion for optimization. The stopping criterion could be:
* a maximum number of iterations
* a maximum amount of time
* a maximum number of samples evaluated
* a maximum value of hypervolume
* a maximum number of iterations that hypervolume stops to improve

.. figure:: ../../_static/placeholder.png

Then, the user can click the ``Optimize`` button to start the automatic iterative optimization and evaluation, which stops until one of the stopping criteria satisfies.


Interrupt
'''''''''

Under either mode, at any time, the user can stop the optimizationby just clicking the ``Stop`` button.