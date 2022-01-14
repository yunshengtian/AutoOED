------------
Installation
------------

AutoOED can be installed either directly from the links to the executable files, or from source code.
Source code is the most up-to-date version, while executable files are relatively stable.


Executable File
---------------

.. _Windows: https://drive.google.com/file/d/1bAPK3HPPxwXy1k-epYXmL5HgW7KkJigi/view
.. _MacOS: https://drive.google.com/file/d/1-XkUYi9M21gZ5bpsYAVbINJoYC7THu_U/view
.. _Linux: https://drive.google.com/file/d/1VUxXQrjC16_S2IzWJex4lSkYhIxGBAly/view

+--------------------+------------------------------------------------------------+
| Installation Link  | Instructions                                               |
+====================+============================================================+
| `Windows`_         | Install using AutoOED-Setup.exe                            |
+--------------------+------------------------------------------------------------+
| `MacOS`_           | Install using AutoOED.dmg                                  |
+--------------------+------------------------------------------------------------+
| `Linux`_           | Unzip and directly run AutoOED_{version}/AutoOED_{version} |
+--------------------+------------------------------------------------------------+


Source Code
-----------

Clone the github repository at https://github.com/yunshengtian/AutoOED, then follow the instructions in README to install.


Extra Steps for Custom Evaluation Programs
------------------------------------------

There is some more work to do if you want to link your own evaluation programs to AutoOED to achieve fully automated experimentation, 
and the type of work depends on which language your program is written in (we currently support Python, C/C++ and MATLAB). 
Otherwise, if your evaluation cannot be executed by programs, you can skip this part.

Python
''''''

There is no extra installation step for Python evaluation programs. But you may pay attention to the packages imported into your evaluation program. 
If you install AutoOED directly from executable files, make sure the packages are in the dependencies of AutoOED (by checking environment.yml or requirements.txt); 
otherwise, if you install AutoOED from source code, you need to make sure the packages exist in your python environment already to avoid import errors.

C/C++
'''''

To use C/C++ evaluation programs in AutoOED, you need to make sure you have gcc (for C) or g++ (for C++) pre-installed on your computer. 
Otherwise, AutoOED will fail to compile your evaluation programs without proper compilers.

MATLAB
''''''

To use MATLAB evaluation programs in AutoOED, you need to install AutoOED from source code, and of course, have MATLAB pre-installed on your computer.
Then, find the root folder of MATLAB. If you have trouble finding it, just start MATLAB and type matlabroot in the command window. Copy the path returned by matlabroot.

Next, you need to navigate to the folder:

- *matlabroot\\extern\\engines\\python* (for Windows)
- *matlabroot/extern/engines/python* (for MacOS and Linux)

and execute `python setup.py install`. By doing so, MATLAB python extension is installed and AutoOED is able to automatically call MATLAB programs.