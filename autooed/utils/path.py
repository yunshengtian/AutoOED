import os


def get_root_dir():
    '''
    Get the root path of the repository
    '''
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    system_dir = os.path.dirname(utils_dir)
    root_dir = os.path.dirname(system_dir)
    return root_dir


def get_static_dir():
    return os.path.join(get_root_dir(), 'static')


def get_logo_path():
    return os.path.join(get_static_dir(), 'logo.png')


def get_icon_path():
    return os.path.join(get_static_dir(), 'icon.png')


def get_version():
    with open(os.path.join(get_root_dir(), 'version.txt'), 'r') as fp:
        version = fp.readline()
    return version
