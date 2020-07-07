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
python run_interactive_db.py
```

This command will run MOBO optimization using configurations specified from GUI interaction, with interactive tkinter-based GUI and SQLite database for data storage.

```
python run_interactive_csv.py
```

This command will run MOBO optimization using configurations specified from GUI interaction, with interactive tkinter-based GUI and csv file for data storage.

```
python run_cmd_db.py
```

This command will run MOBO optimization using configurations specified from command line, with simple tkinter-based GUI and SQLite database for data storage.

```
python run_cmd_csv.py
```

This command will run MOBO optimization using configurations specified from command line, with simple tkinter-based GUI and csv file for data storage.

## GUI

### Interactive GUI

![gui_interactive](data/gui_interactive_main.png)

![gui_interactive](data/gui_interactive_config.png)

### Simple GUI

![gui_interactive](data/gui_simple.png)