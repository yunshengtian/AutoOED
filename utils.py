import os
import warnings
from pymoo.configuration import Configuration


def set_environment():
    '''
    Set environment variables
    '''
    os.environ['OMP_NUM_THREADS'] = '1'
    warnings.filterwarnings('ignore')
    Configuration.show_compile_hint = False