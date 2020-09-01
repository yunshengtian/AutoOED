import os
from system.gui import ServerGUI


def main():
    os.environ['OMP_NUM_THREADS'] = '1'
    gui = ServerGUI()
    gui.mainloop()


if __name__ == '__main__':
    main()