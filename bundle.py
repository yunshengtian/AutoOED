import os, platform, shutil
from multiprocessing import Process, freeze_support
from argparse import ArgumentParser


def main():

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
    parser.add_argument(
        '--zip',
        default=False,
        action='store_true',
    )
    parser.add_argument(
        '--serial',
        default=False,
        action='store_true',
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

    for work_dir in [base_dir, build_dir, dist_dir, spec_dir]:
        os.makedirs(work_dir, exist_ok=True)

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

    sep = os.pathsep

    base_cmd = f'''
        pyinstaller --windowed --onedir \
        --add-data "../../problem/custom{sep}problem/custom" \
        --add-data "../../problem/data{sep}problem/data" \
        --add-data "../../problem/predefined{sep}problem/predefined" \
        --add-data "../../examples{sep}examples" \
        --add-data "../../system/static{sep}system/static" \
        --hidden-import "PIL._tkinter_finder" \
        --hidden-import "pymoo.cython.non_dominated_sorting" \
        --hidden-import "sklearn.neighbors._typedefs" \
        --hidden-import "sklearn.neighbors._quad_tree" \
        --hidden-import "sklearn.tree._utils" \
        --hidden-import "sklearn.utils._cython_blas" \
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

    if args.serial:
        for cmd in all_cmds:
            print('debug', cmd)
            os.system(cmd + ' > log.txt')
    else:
        processes = []
        for cmd in all_cmds:
            processes.append(Process(target=os.system, args=(cmd,)))

        [p.start() for p in processes]
        [p.join() for p in processes]

    system = platform.system()

    if args.zip:
        if type(name) == list:
            for curr_name in name:
                zip_dir = curr_name + '.app' if system == 'Darwin' else curr_name
                shutil.make_archive(os.path.join(base_dir, curr_name), 'zip', root_dir=dist_dir, base_dir=zip_dir)
        else:
            zip_dir = name + '.app' if system == 'Darwin' else name
            shutil.make_archive(os.path.join(base_dir, name), 'zip', root_dir=dist_dir, base_dir=zip_dir)


if __name__ == '__main__':
    freeze_support()
    main()
