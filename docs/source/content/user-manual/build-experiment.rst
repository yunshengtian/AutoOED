.. raw:: html

    <style> .red {color:red} </style>


-------------------
Building Experiment
-------------------

After created the problem to optimize, we need to build an experiment configuration which includes the information required by optimization, for example, batch size, choice of algorithm, and so on.
Similar to the problem configuration, the experiment configuration could also be created in two ways: through interactions with GUI or through a configuration file.


Build from GUI
--------------

To build an experiment interactively from GUI, first click ``Config->Create`` from the menu, then the software will enter this window:

.. figure:: ../../_static/placeholder.png

First of all, you need to select which problem to optimize on the top, where you can see the whole list of created problems.

:red:`(**TODO**: explain what are samples)`

Next, since the optimization rely on a set of initial samples (more than 1), you need to provide either: 
a number of initial samples that AutoOED could randomly generate for you, or the path to the file storing existing initial samples.

:red:`(**TODO**: add more detailed instructions on how to operate through the GUI)`

Then, we can select the specific algorithm to use for optimization. More detailed description of all the supported algorithms can be found in **TODO**.

:red:`(**TODO**: add algorithm illustrations, and provide a default choice)`


Build from Configuration File
-----------------------------

