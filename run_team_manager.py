from utils import set_environment
from system.manager import ManagerController
from multiprocessing import freeze_support


def main():
    set_environment()
    ManagerController().run()


if __name__ == '__main__':
    freeze_support()
    main()