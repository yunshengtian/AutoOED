from utils import set_environment
from system.scientist.controller.personal import ScientistController
from multiprocessing import freeze_support


def main():
    set_environment()
    ScientistController().run()


if __name__ == '__main__':
    freeze_support()
    main()