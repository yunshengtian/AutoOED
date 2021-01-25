import os, sys
root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.append(root_dir)

import warnings
warnings.filterwarnings('ignore')

from system.server import ServerController


def main():
    ServerController().run()


if __name__ == '__main__':
    main()