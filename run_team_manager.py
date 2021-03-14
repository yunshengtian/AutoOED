import os
import warnings
warnings.filterwarnings('ignore')

from system.manager import ManagerController


def main():
    ManagerController().run()


if __name__ == '__main__':
    main()