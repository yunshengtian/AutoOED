--------
Overview
--------

In this section, we provide a detailed user manual that covers how you should use AutoOED (team version) for
your optimization problems. 

Unlike personal version of AutoOED, the team version has three independent software applications including AutoOED Manager,
AutoOED Scientist and AutoOED Technician, with the following responsibilities:

- **Manager**: Managing the database and the user access
- **Scientist**: Building problems and experiments, running optimization
- **Technician**: Performance evaluation

The main difference between personal version and team version is: personal version
is only for optimization and evaluation on a single computer which suits personal use, while team version has
all the capabilities of the personal version in AutoOED Scientist and also extra supports for team collaboration.

Note that since we use `MySQL <https://www.mysql.com/>`_ for data storage of the team version, before using any of the applications please make sure
that MySQL is preinstalled on your local computer.

So in this manual, we will introduce all the useful tools for `Manager <manager.html>`_, `Scientist <scientist.html>`_ and `Technician <technician.html>`_.
Finally we will show you how they would interact and collaborate with each other.
