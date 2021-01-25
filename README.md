# AutoOED: Automated Optimal Experiment Design Platform

An Optimal Experiment Design platform powered with automated machine learning to accelerate the discovery of optimal solutions. Our platform solves multi-objective optimization problems and automatically guides the design of experiment to be evaluated.

## Installation

Install by conda:

```
conda env create -f environment.yml
conda activate autooed
```

Or install by pip:

```
pip install -r requirements.txt
```

Finally, install the following packages by pip:

```
pip install pymoo==0.4.1 pygco==0.0.16
```

Tested with Python 3.7 on Ubuntu 18.04.

## Getting Started

### Personal Version

```bash
python scripts/personal/run.py
```

### Team Version

```bash
python scripts/team/run_server.py
python scripts/team/run_scientist.py
python scripts/team/run_worker.py
```

