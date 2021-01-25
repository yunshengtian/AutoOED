import os, sys
root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.append(root_dir)

import warnings
warnings.filterwarnings('ignore')

from system.scientist.controller.team import ScientistController


def main():
    os.environ['OMP_NUM_THREADS'] = '1'
    ScientistController().run()


if __name__ == '__main__':
    main()