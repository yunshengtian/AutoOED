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
python local_file_run.py
```

This command will run MOBO optimization using configurations specified in config/example_config.yml, with local tkinter-based GUI and csv file as data storage.

```
python local_db_run.py
```

This command will run MOBO optimization using configurations specified in config/example_config.yml, with local tkinter-based GUI and SQLite database as data storage.