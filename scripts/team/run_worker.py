import os, sys
root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.append(root_dir)

from system.worker import WorkerController


def main():
    WorkerController().run()


if __name__ == '__main__':
    main()