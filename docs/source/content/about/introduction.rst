------------
Introduction
------------

AutoOED is an Optimal Experiment Design platform powered with automated
machine learning to accelerate the discovery of optimal solutions. The platform solves
multi-objective optimization problems and automatically guides the design of experiments
to be evaluated. 

To automate the optimization process, we implement several multiobjective Bayesian optimization algorithms with state-of-the-art performance.
AutoOED is open-source and written in python. The codebase is modular, facilitating extensions and
tailoring the code, serving as a testbed for machine learning researchers to easily develop
and evaluate their own multi-objective Bayesian optimization algorithms. An intuitive
graphical user interface (GUI) is provided to visualize and guide the experiments for users
with little or no experience with coding, machine learning, or optimization.


Applications
''''''''''''

AutoOED is a powerful and easy-to-use tool for design parameter optimization, 
which can be used for any kind of experiment settings (chemistry, material, physics, engineering, computer science ...), 
and is generalizable to any performance evaluation mechanism (through computer programs or real experiments).

AutoOED aims at improving the sample efficiency of optimization problems, i.e., using less number of samples to achieve the best performance, 
by applying state-of-the-art machine learning approaches. 
So AutoOED is most powerful when the performance evaluation of your problem is expensive (for example, in terms of time or money).


Requirements
''''''''''''

Generally there is no hardware or software requirement for AutoOED to run on your computer, and a modern laptop with Windows/MacOS/Linux operating system would be enough.

The speed of optimization is mainly determined by which algorithm you choose, and the number of evaluated samples in the dataset. 
But most of our optimization algorithms run very fast, and should be on the magnitude of seconds with hundreds of samples for each iteration.
And the speed could be further boosted if you have a powerful CPU or enable parallelization in AutoOED.

However, there are some requirements for your optimization problem that you should pay attention to:

- AutoOED only supports problems with 2 or 3 objectives at the moment, but we are working on supporting higher dimensional performance space.
- The problem constraints should depend only on design variables. AutoOED does not support constraints on objectives.


Citation
''''''''

If you find our work helpful to your research, please consider citing our `paper <https://arxiv.org/abs/2104.05959>`_.

.. code-block:: bib

    @misc{tian2021autooed,
        title={AutoOED: Automated Optimal Experiment Design Platform},
        author={Yunsheng Tian and Mina Konaković Luković and Timothy Erps and Michael Foshey and Wojciech Matusik},
        year={2021},
        eprint={2104.05959},
        archivePrefix={arXiv},
        primaryClass={cs.AI}
    }


Contributing
''''''''''''

We highly welcome all kinds of contributions, including but not limited to bug fixes, new feature suggestions, more intuitive error messages, and so on.

Especially, `the algorithmic part <https://github.com/yunshengtian/AutoOED/tree/master/algorithm/mobo>`_ 
of our code repository is written in a clean and modular way, 
facilitating extensions and tailoring the code, serving as a testbed for machine learning researchers to 
easily develop and evaluate their own multi-objective Bayesian optimization algorithms. 
We are looking forward to supporting more powerful optimization algorithms on our platform.


Contact
'''''''

If you experience any issues during installing or using the software or have any feature suggestions,
please feel free to reach out to us either by creating issues on `GitHub <https://github.com/yunshengtian/AutoOED>`_
or sending emails to autooed@csail.mit.edu.
