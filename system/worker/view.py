import tkinter as tk
from system.gui.utils.grid import grid_configure
from system.gui.widgets.factory import create_widget
from system.gui.widgets_modular import ProblemInfoWidget, AdjustableTable
from system.params import *


class WorkerLoginView:

    def __init__(self, root):
        self.root = root

        frame_login = tk.Frame(master=self.root)
        frame_login.grid(row=0, column=0, padx=20, pady=20, sticky='NSEW')

        create_widget('logo', master=frame_login, row=0, column=0)

        self.widget = {}
        self.widget['ip'] = create_widget('labeled_entry', master=frame_login, row=1, column=0, width=20,
            text='Server IP Address', class_type='string', required=True, required_mark=False)
        self.widget['user'] = create_widget('labeled_entry', master=frame_login, row=2, column=0, width=20,
            text='Username', class_type='string', required=True, required_mark=False)
        self.widget['passwd'] = create_widget('labeled_entry', master=frame_login, row=3, column=0, width=20,
            text='Password', class_type='string', required=False)
        self.widget['task'] = create_widget('labeled_entry', master=frame_login, row=4, column=0, width=20,
            text='Task Name', class_type='string', required=True, required_mark=False)
        self.widget['login'] = create_widget('button', master=frame_login, row=5, column=0, text='Log in')


class WorkerView:

    def __init__(self, root):
        self.root = root

        self._init_menu()
        self._init_viz()

    def _init_menu(self):
        pass

    def _init_viz(self):
        '''
        '''
        grid_configure(self.root, 0, 0)

        self.widget = {}

        frame_db = create_widget('labeled_frame', master=self.root, row=0, column=0, text='Database')
        self.widget['db_frame'] = frame_db
        self.widget['db_placeholder'] = create_widget('label', master=frame_db, row=0, column=0, text='Uninitialized')
        self.widget['db_table'] = None

        frame_ctrl = create_widget('frame', master=self.root, row=0, column=1, padx=0, pady=0)
        self.widget['problem_info'] = ProblemInfoWidget(master=frame_ctrl, row=0, column=0)

        frame_eval = create_widget('labeled_frame', master=frame_ctrl, row=1, column=0, text='Evaluation')
        self.widget['mode'] = create_widget('radiobutton',
            master=frame_eval, row=0, column=0, text_list=['Manual', 'Auto'], default='Manual')

        frame_manual = create_widget('frame', master=frame_eval, row=1, column=0, padx=0, pady=0)
        self.widget['manual_lock'] = create_widget('button', master=frame_manual, row=0, column=0, text='Lock entry')
        self.widget['manual_release'] = create_widget('button', master=frame_manual, row=0, column=1, text='Release entry')
        self.widget['manual_fill'] = create_widget('button', master=frame_manual, row=1, column=0, columnspan=2, text='Fill value')

        frame_auto = create_widget('frame', master=frame_eval, row=1, column=0, padx=0, pady=0)
        self.widget['n_worker'] = create_widget('labeled_entry', master=frame_auto, row=0, column=0, columnspan=2, text='Number of workers',
            class_type='int', valid_check=lambda x: x > 0, error_msg='Number of evaluation workers must be positive', required=True, default=1)
        self.widget['auto_set_script'] = create_widget('button', master=frame_auto, row=1, column=0, text='Set script')
        self.widget['auto_evaluate'] = create_widget('button', master=frame_auto, row=1, column=1, text='Evaluate')

        grid_configure(frame_eval, 0, 0)
        grid_configure(frame_manual, 1, 1)
        grid_configure(frame_auto, 1, 1)
        frame_auto.grid_remove()

        def set_manual():
            frame_auto.grid_remove()
            frame_manual.grid()

        def set_auto():
            frame_manual.grid_remove()
            frame_auto.grid()

        for text, button in self.widget['mode'].widget.items():
            if text == 'Manual':
                button.configure(command=set_manual)
            elif text == 'Auto':
                button.configure(command=set_auto)
            else:
                raise Exception()

        for widget_name in ['auto_set_script', 'auto_evaluate', 'manual_lock', 'manual_release', 'manual_fill']:
            self.widget[widget_name].configure(state=tk.DISABLED)

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

        for widget_name in ['auto_set_script', 'manual_lock', 'manual_release', 'manual_fill']:
            self.widget[widget_name].configure(state=tk.NORMAL)

    def get_table_columns(self):
        return self.widget['db_table'].columns