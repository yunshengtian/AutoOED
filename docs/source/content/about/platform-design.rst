---------------
Platform Design
---------------

AutoOED is designed in a hierarchical and modular way. Overall the platform consists of four layers:

* **GUI**: the top layer that interacts directly with users, which is implemented by Tkinter and according to Model-View-Controller (MVC) architecture.
* **Optimization Algorithm**: the optimization algorithms running behind the screen, which is the core of AutoOED.
* **Agent**: a task scheduler that runs and monitors the optimization and evaluation tasks given by users or optimization algorithms, also interacts with the underlying database.
* **Database**: the bottom layer that stores all the history data. We use SQLite for the personal version and MySQL for the team version.

Though most of the layers are specifically designed for AutoOED, the algorithm layer is actually highly modular and easy to be extended with custom algorithms. See our API reference for more details.

AutoOED has personal version and team version to support different experiment scenarios.


Personal Version
----------------

The personal version of AutoOED has all the `supported features <platform-features.html>`_ except distributed collaboration. 
This version is cleaner and easier to work with, especially when the optimization and evaluation can be done on a single computer.
For data storage, this version uses SQLite, which is a built-in local database management system that comes with python.


Team Version
------------

The team version enables distributed collaboration around the globe by leveraging a centralized MySQL database that can be connected through internet. 
Using this version, the scientist can focus on controlling the optimization and data analysis, while the technicians can evaluate in a distributed fashion and synchronize the 
evaluated results with other members in the team in real-time, through our provided simple and intuitive user interface. 
This version provides different software for different roles of a team (manager, scientist and technician) with proper privilege control implemented.