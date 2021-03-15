-------------------
Building Experiment
-------------------

After the problem has been created for optimization, we need to build an experiment configuration which includes the information required by optimization, for example, batch size, choice of algorithm, and so on.
The experiment configuration can be either created through interactive GUI or loaded from a configuration file.


Creating Configuration through GUI
----------------------------------

To build an experiment interactively through GUI, first click ``Config->Create`` from the menu, then this window will show:

.. figure:: ../../_static/manual-personal/build-experiment/create.png
   :width: 400 px


Problem
'''''''

First of all, you need to select which problem to optimize on the top, where you can see the whole list of created problems,
along with many predefined test problems.


Algorithm
'''''''''

Next, we can select the specific algorithm to use for optimization. More detailed description of all the supported algorithms can be found in 
`Supported Algorithms <../about/supported-algorithms.html>`_.

In general, although the performance of each algorithm varies greatly depending on the problem, we suggest using DGEMO
for most of the cases since it exhibits a relatively better and stabler performance. And you are also able to customize
the parameters of the algorithms by clicking ``Advanced Settings``, if you are not satisfied with the default choices. For example:

.. figure:: ../../_static/manual-personal/build-experiment/algorithm_advanced.png
   :width: 500 px


Initialization
''''''''''''''

Then, since the optimization rely on a set of initial samples (more than 1), you need to provide either: 
a number of initial samples that AutoOED will randomly generate for you, or the path to the file storing existing initial samples.

For initialization with random samples, make sure the ``Random`` choice is selected and you have to input the number of random initial
samples you want. For initialization with provided existing samples, the ``Provided`` choice has to be selected and you have to specify
the file location of existing samples by clicking the ``Browse`` buttons. For example:

.. figure:: ../../_static/manual-personal/build-experiment/initialize_provided.png
   :width: 400 px

In this case, the initial design samples must be provided, either with or without corresponding initial performance values.


Experiment
''''''''''

Finally, you need to specify how many number of evaluation workers can be run in parallel.
For example, if you only have one experimental setup that can only do one evaluation at a time, then the number of 
evaluation workers should be specified as 1. Otherwise, AutoOED will try to launch parallel evaluations with the maximum number of workers as you specified,
when there are multiple design samples proposed by the algorithm to be evaluated.


Loading from Configuration File
-------------------------------

