------------
Installation
------------

AutoOED can be installed either directly from the links to the executable files, or from source code.


Executable File (Outdated)
--------------------------

Personal Version
''''''''''''''''

Follow the links below to install a zip file, unzip it and find the executable file at the corresponding location.

.. _Windows (82 MB): https://drive.google.com/file/d/1UvOP_X6wPPAiCaYAtkRVwzxRzQfOhWcF/view?usp=sharing
.. _MacOS (190 MB): https://drive.google.com/file/d/1zmR47kgkCWAxl7JsNoQydPrFyGq4i1Wa/view?usp=sharing
.. _Linux (98 MB): https://drive.google.com/file/d/1eZnNn603-hjmVZXkwOua0po8jprFlAub/view?usp=sharing

+--------------------+--------------------------+
| Installation Link  | Executable File Location |
+====================+==========================+
| `Windows (82 MB)`_ | AutoOED\\AutoOED.exe     |
+--------------------+--------------------------+
| `MacOS (190 MB)`_  | AutoOED.app              |
+--------------------+--------------------------+
| `Linux (98 MB)`_   | AutoOED/AutoOED          |
+--------------------+--------------------------+


Team Version
''''''''''''

There are three executable files for different roles of the team: AutoOED_Manager, AutoOED_Scientist and AutoOED_Technician.

Before installing AutoOED, `MySQL <https://www.mysql.com/>`_ database management system needs to be installed on computers that will use AutoOED.

After installing MySQL, follow the links below to install a zip file, unzip it and find the executable file at the corresponding location.

.. _Windows Manager (0 MB): TODO
.. _Windows Scientist (0 MB): TODO
.. _Windows Technician (0 MB): TODO
.. _MacOS Manager (0 MB): TODO
.. _MacOS Scientist (0 MB): TODO
.. _MacOS Technician (0 MB): TODO
.. _Linux Manager (0 MB): TODO
.. _Linux Scientist (0 MB): TODO
.. _Linux Technician (0 MB): TODO

+-----------------------------+--------------------------------+
| Installation Link           | Executable File Location       |
+=============================+================================+
| `Windows Manager (0 MB)`_   | AutoOED\\AutoOED_Manager.exe   |
+-----------------------------+--------------------------------+
| `Windows Scientist (0 MB)`_ | AutoOED\\AutoOED_Scientist.exe |
+-----------------------------+--------------------------------+
| `Windows Technician (0 MB)`_| AutoOED\\AutoOED_Technician.exe|
+-----------------------------+--------------------------------+
| `MacOS Manager (0 MB)`_     | AutoOED_Manager.app            |
+-----------------------------+--------------------------------+
| `MacOS Scientist (0 MB)`_   | AutoOED_Scientist.app          |
+-----------------------------+--------------------------------+
| `MacOS Technician (0 MB)`_  | AutoOED_Technician.app         |
+-----------------------------+--------------------------------+
| `Linux Manager (0 MB)`_     | AutoOED/AutoOED_Manager        |
+-----------------------------+--------------------------------+
| `Linux Scientist (0 MB)`_   | AutoOED/AutoOED_Scientist      |
+-----------------------------+--------------------------------+
| `Linux Technician (0 MB)`_  | AutoOED/AutoOED_Technician     |
+-----------------------------+--------------------------------+


Installing from Source Code
---------------------------

Clone the github repository at https://github.com/yunshengtian/AutoOED, then follow the instructions in README to install.


MATLAB Extension
----------------

To use MATLAB evaluation programs in AutoOED, you need to install AutoOED from source code, and of course, have MATLAB pre-installed on your computer. 
Then, find the root folder of MATLAB. If you have trouble finding it, just start MATLAB and type matlabroot in the command window. Copy the path returned by matlabroot.

Next, you need to copy the folder:

- *matlabroot\extern\engines\python\dist\matlab* (for Windows)
- *matlabroot/extern/engines/python/dist/matlab* (for MacOS and Linux)

and paste it (the *matlab* folder) directly in the root directory of AutoOED.
By doing so, AutoOED is able to recognize MATLAB on your computer and automatically call MATLAB programs.
