# MOBO-System

## Installation

Install by conda:

```
conda env create -f environment.yml
conda activate mobo
```

Or directly install major dependencies from pip:

```
pip install numpy scipy argparse autograd cma cython matplotlib pandas pymoo pymop pyyaml
```

Tested with Python 3.7.

## Getting Started

```
python optimize.py
```

This command will run 1 iteration of MOBO optimization using configurations specified in experiment_config.yml (will add a doc on the parameter settings in this yml file later).

The main function is optimize() in optimize.py, where it takes (problem, X_init, Y_init) as input and output a dataframe X_next_df.