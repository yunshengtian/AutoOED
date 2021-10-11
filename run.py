import os
import warnings
from pymoo.configuration import Configuration

from system.scientist.controller.personal import ScientistController
from multiprocessing import freeze_support


def set_environment():
    '''
    Set environment variables
    '''
    os.environ['OMP_NUM_THREADS'] = '1'
    warnings.filterwarnings('ignore')
    Configuration.show_compile_hint = False


def main():
    set_environment()
    ScientistController().run()


if __name__ == '__main__':
    freeze_support()
    main()