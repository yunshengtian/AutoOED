'''
Run with local tkinter GUI and SQLite for data storage, having more GUI interactions for configurations, control and logging
'''

import os
from system.gui import GUI


def main():
    os.environ['OMP_NUM_THREADS'] = '1'
    gui = GUI()
    gui.mainloop()


if __name__ == '__main__':
    main()