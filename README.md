# OpenMOBO

Open-source software for multi-objective Bayesian optimization (MOBO).

## Installation

Install by conda:

```
conda env create -f environment.yml
conda activate mobo
```

Or directly install major dependencies from pip:

```
pip install numpy scipy argparse autograd cma cython matplotlib pandas pygco pymoo pymop pyyaml sklearn tkintertable
```

Tested with Python 3.7 on Ubuntu 18.04.

## Getting Started

```
python run_server.py
python run_client.py
```

These commands correspond to running the server/client program respectively.
