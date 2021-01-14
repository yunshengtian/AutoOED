import os, sys
root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.append(root_dir)

from system.scientist import TeamScientistController


def main():
    os.environ['OMP_NUM_THREADS'] = '1'
    TeamScientistController().run()


if __name__ == '__main__':
    main()