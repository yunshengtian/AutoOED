import tkinter as tk
from tkinter import ttk
from system.gui.utils.grid import grid_configure
from system.gui.widgets.factory import create_widget
from system.gui.widgets_modular import ProblemInfoWidget, AdjustableTable
from system.params import *


class ServerLoginView:

    def __init__(self, root):
        self.root = root

        frame_login = create_widget('frame', master=self.root, row=0, column=0)
        create_widget('logo', master=frame_login, row=0, column=0)

        self.widget = {}
        self.widget['user'] = create_widget('labeled_entry', master=frame_login, row=1, column=0, width=20,
            text='Username', class_type='string', required=True, required_mark=False)
        self.widget['passwd'] = create_widget('labeled_entry', master=frame_login, row=2, column=0, width=20,
            text='Password', class_type='string', required=False)
        self.widget['login'] = create_widget('button', master=frame_login, row=3, column=0, text='Log in')


class ServerInitView:

    def __init__(self, root):
        self.root = root

        frame_init = create_widget('frame', master=self.root, row=0, column=0)
        grid_configure(frame_init, 1, 0)

        self.widget = {}

        frame_info = create_widget('labeled_frame', master=frame_init, row=0, column=0, columnspan=2, text='Info')
        grid_configure(frame_info, 0, 2)
        self.widget['user'] = create_widget('label', master=frame_info, row=0, column=0, text='Username:')
        self.widget['ip'] = create_widget('label', master=frame_info, row=0, column=1, text='IP Address:')
        self.widget['refresh'] = create_widget('button', master=frame_info, row=0, column=2, text='Refresh')

        frame_db = create_widget('labeled_frame', master=frame_init, row=1, column=0, text='Database')
        grid_configure(frame_db, 0, 2)
        self.widget['create_task'] = create_widget('button', master=frame_db, row=0, column=0, text='Create Task')
        self.widget['load_task'] = create_widget('button', master=frame_db, row=0, column=1, text='Load Task')
        self.widget['remove_task'] = create_widget('button', master=frame_db, row=0, column=2, text='Remove Task')

        frame_access = create_widget('labeled_frame', master=frame_init, row=2, column=0, text='Access')
        grid_configure(frame_access, 0, 1)
        self.widget['manage_admin'] = create_widget('button', master=frame_access, row=0, column=0, text='Manage Admin Access')
        self.widget['manage_user'] = create_widget('button', master=frame_access, row=0, column=1, text='Manage User Access')


class ServerView:

    def __init__(self, root):
        self.root = root

        self._init_menu()
        self._init_viz()

    def _init_menu(self):
        pass

    def _init_viz(self):
        '''
        Visualization initialization
        '''
        grid_configure(self.root, 0, 0)

        self.widget = {}

        frame_db = create_widget('labeled_frame', master=self.root, row=0, column=0, text='Database')
        self.widget['db_frame'] = frame_db
        self.widget['db_placeholder'] = create_widget('label', master=frame_db, row=0, column=0, text='Uninitialized')
        self.widget['db_table'] = None

        frame_conn = create_widget('frame', master=self.root, row=0, column=1, padx=0, pady=0)
        grid_configure(frame_conn, [3], 0)

        self.widget['problem_info'] = ProblemInfoWidget(master=frame_conn, row=0, column=0)

        frame_server = create_widget('labeled_frame', master=frame_conn, row=1, column=0, text='Server Info')
        self.widget['server_user'] = create_widget('label', master=frame_server, row=0, column=0, text='Username:')
        self.widget['server_ip'] = create_widget('label', master=frame_server, row=0, column=1, text='IP Address:')
        self.widget['server_refresh'] = create_widget('button', master=frame_server, row=0, column=2, text='Refresh')

        frame_sci = create_widget('labeled_frame', master=frame_conn, row=2, column=0, text='Scientist Info')
        self.widget['sci_user'] = create_widget('label', master=frame_sci, row=0, column=0, text='Username: unknown')
        self.widget['sci_ip'] = create_widget('label', master=frame_sci, row=0, column=1, text='IP Address: unknown')
        self.widget['sci_refresh'] = create_widget('button', master=frame_sci, row=0, column=2, text='Refresh')

        frame_worker = create_widget('labeled_frame', master=frame_conn, row=3, column=0, text='Worker Info')
        grid_configure(frame_worker, 0, 2)
        frame_disp = create_widget('frame', master=frame_worker, row=0, column=0, columnspan=3)
        grid_configure(frame_disp, 0, 0)
        self.widget['worker_disp'] = ttk.Treeview(master=frame_disp, columns=(1, 2, 3))
        self.widget['worker_disp'].column('#0', width=100, minwidth=150, stretch=tk.YES)
        self.widget['worker_disp'].column('#1', width=100, minwidth=150, stretch=tk.YES)
        self.widget['worker_disp'].column('#2', width=100, minwidth=150, stretch=tk.YES)
        self.widget['worker_disp'].column('#3', width=100, minwidth=150, stretch=tk.YES)
        self.widget['worker_disp'].heading('#0', text='User', anchor=tk.W)
        self.widget['worker_disp'].heading('#1', text='IP Address', anchor=tk.W)
        self.widget['worker_disp'].heading('#2', text='Status', anchor=tk.W)
        self.widget['worker_disp'].heading('#3', text='Rows in Evaluation', anchor=tk.W)
        self.widget['worker_disp'].grid(row=0, column=0, sticky='NSEW')
        horscrlbar = ttk.Scrollbar(frame_disp, orient='horizontal', command=self.widget['worker_disp'].xview)
        horscrlbar.grid(row=1, column=0, sticky='SEW')
        verscrlbar = ttk.Scrollbar(frame_disp, orient='vertical', command=self.widget['worker_disp'].yview)
        verscrlbar.grid(row=0, rowspan=2, column=1, sticky='NSE')
        self.widget['worker_disp'].configure(xscrollcommand=horscrlbar.set)
        self.widget['worker_disp'].configure(yscrollcommand=verscrlbar.set)
        self.widget['worker_add'] = create_widget('button', master=frame_worker, row=1, column=0, text='Add Worker')
        self.widget['worker_stop'] = create_widget('button', master=frame_worker, row=1, column=1, text='Stop Worker')
        self.widget['worker_remove'] = create_widget('button', master=frame_worker, row=1, column=2, text='Remove Worker')

    def init_db_table(self, columns):
        '''
        '''
        screen_width = self.root.winfo_screenwidth()
        max_width = GEOMETRY_MAX_WIDTH
        width = GEOMETRY_WIDTH_RATIO * screen_width
        if width > max_width: width = max_width
        height = GEOMETRY_HEIGHT_RATIO * width
        self.root.geometry(f'{int(width)}x{int(height)}')

        self.widget['db_placeholder'].destroy()
        self.widget['db_table'] = AdjustableTable(master=self.widget['db_frame'], columns=columns)

    def get_table_columns(self):
        return self.widget['db_table'].columns