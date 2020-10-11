import os


def get_root_dir():
    '''
    Get the root path of the repository
    '''
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    system_dir = os.path.dirname(utils_dir)
    root_dir = os.path.dirname(system_dir)
    return root_dir