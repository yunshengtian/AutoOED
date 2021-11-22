import os
import warnings
from pymoo.configuration import Configuration
from multiprocessing import freeze_support

from autooed.system.gui import GUIController


def set_environment():
    '''
    Set environment variables
    '''
    os.environ['OMP_NUM_THREADS'] = '1'
    warnings.filterwarnings('ignore')
    Configuration.show_compile_hint = False


def main():
    set_environment()
    GUIController()


if __name__ == '__main__':
    freeze_support()
    main()
