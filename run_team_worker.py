import os
import warnings
warnings.filterwarnings('ignore')

from system.worker import WorkerController


def main():
    WorkerController().run()


if __name__ == '__main__':
    main()