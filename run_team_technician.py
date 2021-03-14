import os
import warnings
warnings.filterwarnings('ignore')

from system.technician import TechnicianController


def main():
    TechnicianController().run()


if __name__ == '__main__':
    main()