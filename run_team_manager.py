from utils import set_environment
from system.manager import ManagerController


def main():
    set_environment()
    ManagerController().run()


if __name__ == '__main__':
    main()