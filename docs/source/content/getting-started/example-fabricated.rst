------------------------------
Example: Fabricated Experiment
------------------------------

A physical experimental setup was used to demonstrate the integration of an automated testing apparatus with the software pipeline.
The setup comprises of a brushless DC motor, with an indicator wheel connected to an arduino for remote control.
Data collection was implemented using computer vision and a USB camera, allowing for the location of the indicator wheel to be measured.
Design space parameters comprised of the amount of time of the motor being on, the amount of power delivered to the motor, the amount of power used to stop the motor, and the amount of time required for stopping the motor.
For performance, both power usage and error in the intended rotation were measured and optimized. 

.. image:: placeHolder.png

The system is designed so that design space parameters can be passed directly to the microcontroller to be processed.
Python code has been implemented to take the array of design parameters requested by the algorithm, and format it in a method that the microcontroller can understand.
In the case of our implementation, this is a string comprised of the four potential parameters, passed along via a serial connection to the Arduino.
These commands are processed by the Arduino and sent to the motor controller, which applies appropriate pulse width modulation to modify the amount of energy the motor recieves.
A single cycle of the motor is then processed based on these parameters. 

In addition to the system for processing commands and moving the motor, an image processing system is layered ontop of the control software.
When processing a command, an initial image is taken for the starting location of the indicator wheel. 
The location of the wheel is computed using openCV, which detects the location of the outer circle of the indicator, and the indicating mark as well.
With the outer circle detected, the center of the wheel can be located and used for calculating the angle of the indicating mark.
Images are taken until the movement of the motor has stopped, and the total displacement of the angle can be calculated. 
This value is then returned from the software stack to openMOBO, and the process can be repeated.