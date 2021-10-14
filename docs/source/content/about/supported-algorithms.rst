--------------------
Supported Algorithms
--------------------

Here are the list of optimization algorithms that AutoOED currently supports including the most sample-efficient multi-objective Bayesian optimization algorithms.


Multi-Objective Bayesian Optimization
-------------------------------------

AutoOED supports many popular and state-of-the-art algorithms for multi-objective Bayesian optimization, including:
DGEMO, TSEMO, USeMO, MOEA/D-EGO, ParEGO.

+-----------------+--------------------------------------------------------+-------------------+
| Algorithm       | Publication Name                                       | Publication Venue |
+=================+========================================================+===================+
| DGEMO [1]_      | Diversity-guided multi-objective bayesian optimization | NeurIPS 2020      |
|                 |                                                        |                   |
|                 | with batch evaluations                                 |                   |
+-----------------+--------------------------------------------------------+-------------------+
| USeMO [2]_      | Uncertainty-aware search framework for multi-objective | AAAI 2020         |
|                 |                                                        |                   |
|                 | bayesian optimization                                  |                   |
+-----------------+--------------------------------------------------------+-------------------+
| TSEMO [3]_      | Efficient multiobjective optimization employing        | Journal of Global |
|                 |                                                        |                   |
|                 | gaussian processes, spectral sampling and              | Optimization 2018 |
|                 |                                                        |                   |
|                 | a genetic algorithm                                    |                   |
+-----------------+--------------------------------------------------------+-------------------+
| MOEA/D-EGO [4]_ | Expensive multiobjective optimization by moea/d with   | TEVC 2009         |
|                 |                                                        |                   |
|                 | gaussian process model                                 |                   |
+-----------------+--------------------------------------------------------+-------------------+
| ParEGO [5]_     | Parego: a hybrid algorithm with on-line landscape      | TEVC 2006         |
|                 |                                                        |                   |
|                 | approximation for expensive multiobjective             |                   |
|                 |                                                        |                   |
|                 | optimization problems                                  |                   |
+-----------------+--------------------------------------------------------+-------------------+


References
----------

.. [1] Mina Konaković Luković, Yunsheng Tian, and Wojciech Matusik. Diversity-guided multi-objective bayesian optimization with batch evaluations. In Advances in Neural Information Processing Systems 33, NeurIPS 2020, December 6-12, 2020, virtual, 2020.

.. [2] Syrine Belakaria and Aryan Deshwal. Uncertainty-aware search framework for multi-objective bayesian optimization. In AAAI Conference on Artificial Intelligence (AAAI), 2020.

.. [3] Eric Bradford, Artur M Schweidtmann, and Alexei Lapkin. Efficient multiobjective optimization employing gaussian processes, spectral sampling and a genetic algorithm. Journal of global optimization, 71(2):407–438, 2018.

.. [4] Qingfu Zhang, Wudong Liu, Edward Tsang, and Botond Virginas. Expensive multiobjective optimization by moea/d with gaussian process model. IEEE Transactions on Evolutionary Computation, 14(3):456–474, 2009.

.. [5] Joshua Knowles. Parego: a hybrid algorithm with on-line landscape approximation for expensive multiobjective optimization problems. IEEE Transactions on Evolutionary Computation, 10(1):50–66, 2006.
