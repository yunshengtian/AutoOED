------------
Installation
------------

AutoOED can be installed either directly from the links to the executable files, or from source code.
Source code is the most up-to-date version, while executable files are relatively stable.


Executable File
---------------

Personal Version
''''''''''''''''

Follow the links below to install a zip file, unzip it and find the executable file at the corresponding location.

.. _Windows: http://people.csail.mit.edu/yunsheng/autooed/windows/AutoOED.zip
.. _MacOS: http://people.csail.mit.edu/yunsheng/autooed/macos/AutoOED.zip
.. _Linux: http://people.csail.mit.edu/yunsheng/autooed/linux/AutoOED.zip

+--------------------+--------------------------+
| Installation Link  | Executable File Location |
+====================+==========================+
| `Windows`_         | AutoOED\\AutoOED.exe     |
+--------------------+--------------------------+
| `MacOS`_           | AutoOED.app              |
+--------------------+--------------------------+
| `Linux`_           | AutoOED/AutoOED          |
+--------------------+--------------------------+


Team Version
''''''''''''

There are three executable files for different roles of the team: AutoOED_Manager, AutoOED_Scientist and AutoOED_Technician.

Before installing AutoOED, `MySQL <https://www.mysql.com/>`_ database management system needs to be installed on computers that will use AutoOED.

After installing MySQL, follow the links below to install a zip file, unzip it and find the executable file at the corresponding location.

.. _Windows Manager: http://people.csail.mit.edu/yunsheng/autooed/windows/AutoOED_Manager.zip
.. _Windows Scientist: http://people.csail.mit.edu/yunsheng/autooed/windows/AutoOED_Scientist.zip
.. _Windows Technician: http://people.csail.mit.edu/yunsheng/autooed/windows/AutoOED_Technician.zip
.. _MacOS Manager: http://people.csail.mit.edu/yunsheng/autooed/macos/AutoOED_Manager.zip
.. _MacOS Scientist: http://people.csail.mit.edu/yunsheng/autooed/macos/AutoOED_Scientist.zip
.. _MacOS Technician: http://people.csail.mit.edu/yunsheng/autooed/macos/AutoOED_Technician.zip
.. _Linux Manager: http://people.csail.mit.edu/yunsheng/autooed/linux/AutoOED_Manager.zip
.. _Linux Scientist: http://people.csail.mit.edu/yunsheng/autooed/linux/AutoOED_Scientist.zip
.. _Linux Technician: http://people.csail.mit.edu/yunsheng/autooed/linux/AutoOED_Technician.zip

+-----------------------------+--------------------------------+
| Installation Link           | Executable File Location       |
+=============================+================================+
| `Windows Manager`_          | AutoOED\\AutoOED_Manager.exe   |
+-----------------------------+--------------------------------+
| `Windows Scientist`_        | AutoOED\\AutoOED_Scientist.exe |
+-----------------------------+--------------------------------+
| `Windows Technician`_       | AutoOED\\AutoOED_Technician.exe|
+-----------------------------+--------------------------------+
| `MacOS Manager`_            | AutoOED_Manager.app            |
+-----------------------------+--------------------------------+
| `MacOS Scientist`_          | AutoOED_Scientist.app          |
+-----------------------------+--------------------------------+
| `MacOS Technician`_         | AutoOED_Technician.app         |
+-----------------------------+--------------------------------+
| `Linux Manager`_            | AutoOED/AutoOED_Manager        |
+-----------------------------+--------------------------------+
| `Linux Scientist`_          | AutoOED/AutoOED_Scientist      |
+-----------------------------+--------------------------------+
| `Linux Technician`_         | AutoOED/AutoOED_Technician     |
+-----------------------------+--------------------------------+


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

- *matlabroot\extern\engines\python* (for Windows)
- *matlabroot/extern/engines/python* (for MacOS and Linux)

and execute `python setup.py install`. By doing so, MATLAB python extension is installed and AutoOED is able to automatically call MATLAB programs.