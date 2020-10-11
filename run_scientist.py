import os
from system.scientist.gui import ScientistController


def main():
    os.environ['OMP_NUM_THREADS'] = '1'
    ScientistController().run()


if __name__ == '__main__':
    main()