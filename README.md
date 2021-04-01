<div style="text-align:center">
<img width="500" height="180" src="docs/source/_static/logo.png">
</div>

Website | Documentation | [Contact](mailto:autooed-help@csail.mit.edu)

AutoOED is an optimal experiment design platform powered with automated machine learning to accelerate the discovery of optimal solutions. Our platform solves multi-objective optimization problems and automatically guides the design of experiment to be evaluated.

AutoOED is developed by [Yunsheng Tian](https://www.yunshengtian.com/), [Mina Konaković Luković](http://people.csail.mit.edu/mina/), [Timothy Erps](https://www.linkedin.com/in/timothy-erps-15622a49/), [Michael Foshey](https://www.linkedin.com/in/michael-foshey/) and [Wojciech Matusik](https://cdfg.mit.edu/wojciech) from [Computational Design & Fabrication Group](https://cdfg.mit.edu/) at [MIT Computer Science and Artificial Intelligence Laboratory](https://www.csail.mit.edu/).

## Overview

AutoOED is a powerful and easy-to-use tool for design parameter optimization with multiple objectives, which can be used for any kind of experiment settings (chemistry, material, physics, engineering, computer science…), and is generalizable to any performance evaluation mechanism (through computer programs or real experiments).

AutoOED aims at improving the sample efficiency of optimization problems, i.e., using less number of samples to achieve the best performance, by applying state-of-the-art machine learning approaches. So AutoOED is most powerful when the performance evaluation of your problem is expensive (for example, in terms of time or money).

## Installation

AutoOED can be installed either directly from the links to the executable files, or from source code. Source code is the most up-to-date version, while executable files are relatively stable. Our software generally works across all Windows/MacOS/Linux operating systems.

### Executable files

Please see the instructions for directly installing executable files in our documentation.

### Source code

We recommend to install with Python 3.7+.

Install by conda with pip:

```
conda env create -f environment.yml
conda activate autooed
pip install pymoo==0.4.1 pygco==0.0.16
```

Or install purely by pip:

```
pip install -r requirements.txt
pip install pymoo==0.4.1 pygco==0.0.16
```

*Note: If you cannot properly run the programs after installation, please check if the version of these packages match our specifications.*

## Getting Started

After installing from source code, please run the following commands to start AutoOED for different versions respectively.

### Personal Version

The personal version of AutoOED has all the supported features except distributed collaboration. This version is cleaner and easier to work with, especially when the optimization and evaluation can be done on a single computer.

```bash
python run_personal.py
```

### Team Version

The team version enables distributed collaboration around the globe by leveraging a centralized MySQL database that can be connected through the Internet. Using this version, the scientist can focus on controlling the optimization and data analysis, while the technicians can evaluate in a distributed fashion and synchronize the evaluated results with other members of the team in real-time, through our provided simple and intuitive user interface. This version provides different software for different roles of a team (manager, scientist, and technician) with proper privilege control implemented. Below are the scripts for different roles respectively:

```bash
python run_team_manager.py
python run_team_scientist.py
python run_team_technician.py
```

For more detailed usage and information of AutoOED, please checkout our documentation.

## Citation

If you find our work helpful to your research, please consider citing our paper (to be appeared).

## Contributing

We highly welcome all kinds of contributions, including but not limited to bug fixes, new feature suggestions, more intuitive error messages, and so on.

## Contact

If you experience any issues during installing or using the software, or if you want to contribute to AutoOED, please feel free to reach out to us either by creating issues on GitHub or sending emails to autooed-help@csail.mit.edu.