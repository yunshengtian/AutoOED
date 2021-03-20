from utils import set_environment
from system.technician import TechnicianController


def main():
    set_environment()
    TechnicianController().run()


if __name__ == '__main__':
    main()