from utils import set_environment
from system.technician import TechnicianController
from multiprocessing import freeze_support


def main():
    set_environment()
    TechnicianController().run()


if __name__ == '__main__':
    freeze_support()
    main()