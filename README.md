<img width="400" src="docs/source/_static/logo.png">

![Platform](https://img.shields.io/badge/platform-windows|macos|linux-lightgrey) [![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/) [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE) 

**AutoOED: Automated Optimal Experimental Design Platform**

**[Paper](https://arxiv.org/abs/2104.05959) | [Website](https://autooed.org) | [Documentation](https://autooed.readthedocs.io) | [Contact](mailto:autooed@csail.mit.edu)** 

AutoOED is an optimal experimental design platform powered with automated machine learning to accelerate the discovery of optimal solutions. Our platform solves multi-objective optimization problems and automatically guides the design of experiment to be evaluated. 

*NOTE: The paper and the documentation are slightly outdated. The descriptions may differ from the latest version of the software. We will update them soon.*

## Overview

AutoOED is a powerful and easy-to-use tool written in Python for design parameter optimization with multiple objectives, which can be used for any kind of experiment settings (chemistry, material, physics, engineering, computer science…). AutoOED aims at improving the sample efficiency of optimization problems, i.e., using less number of samples to achieve the best performance, by applying state-of-the-art machine learning approaches, which is most powerful when the performance evaluation of your problem is expensive (for example, in terms of time or money). 

One of the most important features of AutoOED is an intuitive graphical user interface (GUI), which is provided to visualize and guide the experiments for users with little or no experience with coding, machine learning, or optimization. Furthermore, a distributed system is integrated to enable parallelized experimental evaluations by multiple processes on a single computer.

<p>
   	<img width="49%" src="docs/source/_static/manual/run-optimization/auto_control.png">
    <img width="49%" src="docs/source/_static/manual/database/database.png">
</p>

## Installation

AutoOED can be installed either directly from the links to the executable files, or from source code. AutoOED generally works across all Windows/MacOS/Linux operating systems. After installation, there are some extra steps to take if you want to link your own evaluation programs to AutoOED for fully automatic experimentation.


### Executable files

[**Windows**](https://drive.google.com/file/d/1bAPK3HPPxwXy1k-epYXmL5HgW7KkJigi/view) (Install using AutoOED-Setup.exe)

[**MacOS**](https://drive.google.com/file/d/1-XkUYi9M21gZ5bpsYAVbINJoYC7THu_U/view) (Install using AutoOED.dmg)

[**Linux**](https://drive.google.com/file/d/1fOF636a4fsKXBT3mZzjxh7lhghMc2jX5/view) (Unzip and find the executable at AutoOED_{version}/AutoOED_{version})


### Source code

#### Step 1: General (Required)

Install by conda with pip:

```
conda env create -f environment.yml
conda activate autooed
pip install -r requirements_extra.txt
```

Or install purely by pip:

```
pip install -r requirements.txt
pip install -r requirements_extra.txt
```

*Note: If you cannot properly run the programs after installation, please check if the version of these packages match our specifications.*

#### Step 2: Custom Evaluation Programs (Optional)

There is some more work to do if you want to link your own evaluation programs to AutoOED to achieve fully automated experimentation, please see our documentation for more details.

## Getting Started

After installation, please run the following command to start AutoOED with the GUI.

```bash
python run_gui.py
```

For more detailed usage and information of AutoOED, please checkout our documentation.

## Citation

If you find our work helpful to your research, please consider citing our [paper](https://arxiv.org/abs/2104.05959).

```
@misc{tian2021autooed,
    title={AutoOED: Automated Optimal Experiment Design Platform},
    author={Yunsheng Tian and Mina Konaković Luković and Timothy Erps and Michael Foshey and Wojciech Matusik},
    year={2021},
    eprint={2104.05959},
    archivePrefix={arXiv},
    primaryClass={cs.AI}
}
```

## Contributing

We highly welcome all kinds of contributions, including but not limited to bug fixes, new feature suggestions, more intuitive error messages, and so on.

Especially, [the algorithmic part](https://github.com/yunshengtian/AutoOED/tree/master/algorithm/mobo) of our code repository is written in a clean and modular way, facilitating extensions and tailoring the code, serving as a testbed for machine learning researchers to easily develop and evaluate their own multi-objective Bayesian optimization algorithms. We are looking forward to supporting more powerful optimization algorithms on our platform.

## Contact

If you experience any issues during installing or using the software, or if you want to contribute to AutoOED, please feel free to reach out to us either by creating issues on GitHub or sending emails to autooed@csail.mit.edu.
