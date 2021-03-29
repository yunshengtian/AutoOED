import os, shutil
from multiprocessing import Process
from argparse import ArgumentParser


'''
Parse bundle type from command input
'''

parser = ArgumentParser()
parser.add_argument(
    '--type', 
    type=str, 
    choices=['all', 'personal', 'team', 'team_manager', 'team_scientist', 'team_technician'],
    default='all',
)
args = parser.parse_args()


'''
Software names and scripts for different bundle types
'''

names = {
    'personal': 'AutoOED',
    'team_manager': 'AutoOED_Manager',
    'team_scientist': 'AutoOED_Scientist',
    'team_technician': 'AutoOED_Technician',
}
names['team'] = [names['team_manager'], names['team_scientist'], names['team_technician']]
names['all'] = [names['personal']] + names['team']

scripts = {
    'personal': 'run_personal.py',
    'team_manager': 'run_team_manager.py',
    'team_scientist': 'run_team_scientist.py',
    'team_technician': 'run_team_technician.py',
}
scripts['team'] = [scripts['team_manager'], scripts['team_scientist'], scripts['team_technician']]
scripts['all'] = [scripts['personal']] + scripts['team']

name, script = names[args.type], scripts[args.type]


'''
Bundle directories
'''

base_dir = './bundle'
build_dir = os.path.join(base_dir, 'build')
dist_dir = os.path.join(base_dir, 'dist')
spec_dir = os.path.join(base_dir, 'spec')

for work_dir in [build_dir, dist_dir]:
    if type(name) == list:
        for curr_name in name:
            curr_work_dir = os.path.join(work_dir, curr_name)
            if os.path.exists(curr_work_dir):
                shutil.rmtree(curr_work_dir)
            os.makedirs(curr_work_dir)
    else:
        curr_work_dir = os.path.join(work_dir, name)
        if os.path.exists(curr_work_dir):
            shutil.rmtree(curr_work_dir)
        os.makedirs(curr_work_dir)


'''
Bundle commands
'''

base_cmd = f'''
    pyinstaller --windowed --onedir \
    --add-data '../../problem/custom:problem/custom' \
    --add-data '../../problem/data:problem/data' \
    --add-data '../../problem/predefined:problem/predefined' \
    --add-data '../../examples:examples' \
    --add-data '../../system/static:system/static' \
    --hidden-import='PIL._tkinter_finder' \
    --hidden-import='pymoo.cython.non_dominated_sorting' \
    --hidden-import='sklearn.neighbors._typedefs' \
    --hidden-import='sklearn.neighbors._quad_tree' \
    --hidden-import='sklearn.tree._utils' \
    --hidden-import='sklearn.utils._cython_blas' \
    --workpath {build_dir} \
    --distpath {dist_dir} \
    --specpath {spec_dir} \
    '''

if type(name) == list:
    all_cmds = [base_cmd + f'-y -n {curr_name} {curr_script}' for curr_name, curr_script in zip(name, script)]
else:
    all_cmds = [base_cmd + f'-y -n {name} {script}']


'''
Bundle operations
'''

processes = []
for cmd in all_cmds:
    processes.append(Process(target=os.system, args=(cmd,)))

[p.start() for p in processes]
try:
    [p.join() for p in processes]
except KeyboardInterrupt:
    exit()
