% simulation.m
function [md,mass] = simulation(d1,d2,d3,mat)

    % Design parameters
    % d1   % Range: 0.5 to 3.5
    % d2   % Range: 0.5 to 7
    % d3   % Range: 0.5 to 2.5
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

    x2 = 7+d1*cos(t);
    y2 = d2*sin(t);

    x3 = d1*cos(t)-7;
    y3 = d2*sin(t);

    x4 = d3*cos(t);
    y4 = 6+d3*sin(t);

    x5 = d3*cos(t);
    y5 = d3*sin(t)-6;

    x6 = d3*cos(t);
    y6 = d3*sin(t);

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