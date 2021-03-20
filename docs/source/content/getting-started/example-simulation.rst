------------------------------
Example: Simulation Experiment
------------------------------

For a simulation example, we show how the software can interface with a MATLAB function to simulate and optimize a mechanical bracket's stiffness and weight using finite element analysis.


Problem Setup
-------------

.. figure:: ../../_static/getting-started/example-simulation/material.png
   :width: 500 px

The bracket, as an example is shown in the figure above, is used to transfer a normal load to the left surface of the bracket. 
The simulation's primary objective is to find an optimal geometry and material for the bracket to have maximal stiffness and minimal weight. 
To reduce the bracket's weight, three holes of radius, *d_3*, and two ellipses of height *d_2* and width *d_1*, are added to the bracket's cross-section. 
The bracket can also be made from 3 different materials that have different stiffness moduli and densities. 
AutoOED is used to suggest the design parameters of *d_1*, *d_2*, *d_3*, and the bracket material that have the designs with maximal stiffness and minimal weight.


Prerequisites
-------------

We encourage you to read `Basic Usage <basic-usage.html>`_ section first to familiarize yourself with some basic and important procedures of AutoOED.

Since our evaluation program is written in MATLAB, we need to first follow some additional `instructions <installation.html#matlab-extension>`_ 
in order to let AutoOED recognize the MATLAB software on our local computer. And you can find the source code of our evaluation program at 
`the bottom of this page <example-simulation.html#code-of-evaluation-program>`_ (less than 100 lines).

We will skip the illustration of how to start the software because it is very straightforward and has been previously described in the `Starting Software <basic-usage.html#step-1-starting-software>`_ section.


Step 1: Building Problem
------------------------


Step 2: Building Experiment
---------------------------


Step 3: Running Optimization
----------------------------


Code of Evaluation Program
--------------------------

.. code-block:: matlab

    % simulation.m
    function [md,mass] = simulation(d_1,d_2,d_3,mat)

        % Design parameters
        % d_1   % Range: 0.5 to 3.5
        % d_2   % Range: 0.5 to 7
        % d_3   % Range: 0.5 to 2.5
        % mat   % 1 = aluminum, 2 = steel, 3 = nylon

        % Aluminum
        if mat == 1
            d = 2700;   % density (kg/m^3)
            ym = 70e9;  % Young's Modulus (Pa)
            pr = 0.33;  % Poisson's Ratio (-)

        % Steel
        elseif mat == 2
            d = 7800;   % density (kg/m^3)
            ym = 205e9; % Young's Modulus (Pa)
            pr = 0.29;  % Poisson's Ratio (-)
        
        % Nylon
        elseif mat == 3
            d = 1150; % density (kg/m^3)
            ym = 2e9; % Young's Modulus (Pa)
            pr = 0.4; % Poisson's Ratio (-)
        
        end
        
        t = linspace(0,2*pi,500)';
        xin = 15*cos(t);
        yin = 9*sin(t);
        
        indices = find(xin>11);
        len = length(xin)-2*length(indices);
        x1 = zeros(1,len)';
        y1 = zeros(1,len)';
        i = 1;
        
        for n = 1:size(xin)
            if xin(n) < 11 && xin(n) > -11
                x1(i) = xin(n);
                y1(i) = yin(n);
                i = i+1; 
            end
        end
        
        x2 = 7+d_1*cos(t);
        y2 = d_2*sin(t); 
        
        x3 = d_1*cos(t)-7;
        y3 = d_2*sin(t);
        
        x4 = d_3*cos(t);
        y4 = 6+d_3*sin(t);
        
        x5 = d_3*cos(t);
        y5 = d_3*sin(t)-6;
        
        x6 = d_3*cos(t);
        y6 = d_3*sin(t);
        
        pgon = polyshape({x1, x2, x3, x4, x5, x6},{y1, y2, y3, y4, y5, y6});
        tr = triangulation(pgon);
        model = createpde('structural','static-planestress');
        tnodes = tr.Points';
        telements = tr.ConnectivityList';
        
        geometryFromMesh(model,tnodes,telements);
        generateMesh(model,'Hmax',0.25);

        structuralProperties(model,'YoungsModulus',ym,'PoissonsRatio',pr);
        structuralBC(model,'Edge',3,'Constraint','fixed');
        structuralBoundaryLoad(model,'Edge',2,'SurfaceTraction',[0;2000]);

        R = solve(model);
        
        mass = area(pgon)*d;
        md = max(R.Displacement.Magnitude);

    end