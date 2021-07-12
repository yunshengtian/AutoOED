-------
Manager
-------

As the manager of the team, this application is responsible for managing the database and user access, 
also has the ability of checking the optimization status.


Login
-----

If you directly installed the executable file of the software, then simply double-click the executable file to start.
Otherwise, if you installed the software through source code, please run 

.. code-block::

   python run_team_manager.py

The software will start with this login window:

.. figure:: ../../_static/manual-team/manager/login.png
   :width: 400 px

where you need to input username and password of the MySQL database to proceed.


Main Interface
--------------

After login, the main interface appears, where you can manage experiments and access. 

.. figure:: ../../_static/manual-team/manager/main.png
   :width: 500 px


Managing Experiments
--------------------

As a manager, you are the only role in the team that has the privilege of creating and removing experiments.
Also, you can load experiments to check the current optimization status.


Creating Experiments
''''''''''''''''''''

After clicking ``Create Experiment``, this window will pop up:

.. figure:: ../../_static/manual-team/manager/create.png
   :width: 350 px

You need to input a name for your new experiment, which cannot be the same as existing experiments. Then, click ``Create`` to create the experiment.


Loading Experiments
'''''''''''''''''''

After clicking ``Load Experiment``, this window will pop up:

.. figure:: ../../_static/manual-team/manager/load.png
   :width: 350 px

You need to input the name of your existing experiments. Then, click ``Load`` to load that experiment.


Removing Experiments
''''''''''''''''''''

After clicking ``Remove Experiment``, this window will pop up:

.. figure:: ../../_static/manual-team/manager/remove.png
   :width: 350 px

You need to input the name of the experiments you want to remove. Then, click ``Remove`` to remove that experiment.


Experiment Interface
''''''''''''''''''''

After creating or loading a experiment, the experiment interface will appear, which displays the whole database,
problem information, and user information of the active scientist and technicians. For example:

.. figure:: ../../_static/manual-team/manager/experiment.png
   :width: 700 px


Managing User Access
--------------------

You can manage user access by clicking ``Manage User Access`` and entering this interface:

.. figure:: ../../_static/manual-team/manager/user_access.png
   :width: 500 px

Initially, only you will have the access to all the experiments, 
but you cannot do any optimization or evaluation because these are the jobs of scientists and technicians. 
In order to let them in, you need to create users for them in this interface by clicking ``Create`` and entering 
corresponding information. 

When you are specifying the experiment access for users, the options include the access for the current experiments, 
empty for no access at all and \* for all experiments' access.

After the user is created, that user can login to AutoOED using the username and the password you specified through 
Scientist or Technican application.
