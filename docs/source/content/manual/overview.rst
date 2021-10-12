--------
Overview
--------

In this section, we provide a detailed user manual that covers how you should use AutoOED for
setting up, running, and checking status of your optimization problems. 
Here is the overview for the content in these subsections, and please follow the order of these steps:

To start the software and create/load/remove experiments, please refer to `Software Entry <software-entry.html>`_.

After the software is started, to build an optimization problem and let AutoOED recognizes it, you need to go through steps in `Building Problem <build-problem.html>`_. 

If there is an evaluation program available for your problem (written in Python/C/C++/MATLAB) whether for evaluating performance or constraints,
the interface of the evaluation function in your program should be written in a specific way such that it can be automatically called by AutoOED during optimization.
You can see the detailed instructions in `Evaluation Program <eval-program.html>`_.

After the optimization problem has been built, now you are able to create an experiment configuration by following `Building Experiment <build-experiment.html>`_,
which basically tells you how to specify some necessary experiment settings.

Finally, after the experiment configuration has been set, you should be able to run the real optimization. 
Your optimization can be controlled at your own pace, and there are many useful visualization tools that help you understand the optimization status.
See more details in `Running Optimization <run-optimization.html>`_. And for interpreting the optimization statistics, see `Statistics <statistics.html>`_.

Of course, there is also a database interface where you can see all the history data, as described in `Database <database.html>`_.
Besides, you also have the full ability to manipulate the data, e.g., adding new design samples or manually evaluating existing samples.