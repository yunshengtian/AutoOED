import os
import warnings
warnings.filterwarnings('ignore')

from system.server import ServerController


def main():
    ServerController().run()


if __name__ == '__main__':
    main()