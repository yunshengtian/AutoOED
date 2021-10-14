-----------------
Platform Features
-----------------

Intuitive GUI
-------------

An easy-to-use graphical user interface (GUI) is provided to directly visualize and guide the optimization progress and facilitate 
the operation for users with little or no experience with coding, optimization, or machine learning. The interface is built using the 
Tkinter GUI package with model-view-controller (MVC) architecture.


Modular Structure
-----------------

A highly modularized code base and built-in visualization enable easy extensions and replacements of MOBO algorithm components. 
The platform can serve as a testbed for machine learning researchers to easily develop and evaluate their own MOBO algorithms.


Automation of Experimental Design
---------------------------------

The platform is designed to enable straightforward integration into an automatic experimental design optimization pipeline. 
The pipeline may include both `physical experiments <../getting-started/example-physical.html>`_
and `an expensive simulation setup <../getting-started/example-simulation.html>`_. The user can provide an evaluation program (written in Python/C/C++/MATLAB) 
and link it to our platform. The evaluation program needs to either collect the values from physical experiments or perform 
the simulation and retrieve the performance. Our platform will automatically call the evaluation program during the optimization workflow.


Sequential and batch evaluations
--------------------------------

A standard feature supports evaluating a single experiment in each optimization iteration. To further reduce the optimization time, 
the platform parallelizes the evaluation process by enabling synchronous and asynchronous batch evaluations. 
Asynchronous batch evaluations are instrumental when multiple workers are running experiments, but their evaluations drastically vary in time.


Data-Efficient Experimentation
------------------------------

As the platform aims to solve multi-objective optimization problems with expensive to evaluate or black-box objective functions, 
the number of experiments is limited to an order of several dozens. The platform employs an optimization strategy that rapidly 
advances the Pareto front with a small set of evaluated experiments.