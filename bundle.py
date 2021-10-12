import os, platform, shutil
from argparse import ArgumentParser


def main():

    '''
    Parse bundle type from command input
    '''

    parser = ArgumentParser()
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
    Software names and scripts
    '''

    name, script = 'AutoOED', 'run.py'


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
        --add-data "../../autooed/problem/custom{sep}autooed/problem/custom" \
        --add-data "../../autooed/problem/data{sep}autooed/problem/data" \
        --add-data "../../autooed/problem/predefined{sep}autooed/problem/predefined" \
        --add-data "../../examples{sep}examples" \
        --add-data "../../static{sep}static" \
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

    cmd = base_cmd + f'-y -n {name} {script}'


    '''
    Bundle operations
    '''

    os.system(cmd)

    if args.zip:
        if platform.system() == 'Darwin':
            os.system(f"cd {dist_dir} && zip -r {os.path.join('..', name)}.zip ./{name}.app")
        else:
            shutil.make_archive(os.path.join(base_dir, name), 'zip', root_dir=dist_dir, base_dir=name)


if __name__ == '__main__':
    main()
