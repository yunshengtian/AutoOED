---------------
Platform Design
---------------

AutoOED is designed in a hierarchical and modular way. Overall the platform consists of four layers:

* **GUI**: the top layer that interacts directly with users, which is implemented by Tkinter and according to Model-View-Controller (MVC) architecture.
* **Optimization Algorithm**: the optimization algorithms running behind the screen, which is the core of AutoOED.
* **Scheduler**: the scheduler that runs and monitors the optimization and evaluation, also interacts with the underlying database.
* **Database**: the bottom layer that stores all the history data, which is based on SQLite.

Though most of the layers are specifically designed for AutoOED, the algorithm layer is actually highly modular and easy to be extended with custom algorithms. See our API reference for more details.
