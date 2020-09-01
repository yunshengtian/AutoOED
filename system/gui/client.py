import tkinter as tk
from tkinter import scrolledtext

from system.gui.utils.grid import grid_configure
from system.gui.utils.widget_creation import create_widget


class ClientGUI:
    '''
    Client GUI
    '''
    def __init__(self):
        '''
        GUI initialization
        '''
        # GUI root initialization
        self.root = tk.Tk()
        self.root.title('OpenMOBO - Client')
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        self.root.resizable(False, False)

        # event widgets
        self.scrtext_log = None

        # GUI modules initialization
        self._init_mapping()
        self._init_widgets()

    def _init_mapping(self):
        '''
        Mapping initialization
        '''
        self.name_map = {
            'id': 'ID',
            'name': 'Name',
            'description': 'Description',
        }

    def _init_widgets(self):
        '''
        Widgets initialization
        '''
        self._init_info_widgets()
        self._init_comm_widgets()
        self._init_log_widgets()

    def _init_info_widgets(self):
        '''
        Worker information widgets initialization
        '''
        frame_info = create_widget('labeled_frame', master=self.root, row=0, column=0, text='Worker Info')
        frame_config = create_widget('frame', master=frame_info, row=0, column=0, padx=0, pady=0)
        frame_action = create_widget('frame', master=frame_info, row=1, column=0, padx=0, pady=0)
        grid_configure(frame_info, [0], [0])
        grid_configure(frame_action, [0], [0, 1])

        widget_map = {}
        widget_map['id'] = create_widget('labeled_entry', master=frame_config, row=0, column=0, text=self.name_map['id'],
            class_type='string', width=10, required=True)
        widget_map['name'] = create_widget('labeled_entry', master=frame_config, row=1, column=0, text=self.name_map['name'],
            class_type='string', width=10)
        widget_map['description'] = create_widget('labeled_text', master=frame_config, row=2, column=0, text=self.name_map['description'],
            width=20, height=10)

        button_register = create_widget('button', master=frame_action, row=0, column=0, text='Register')
        button_login = create_widget('button', master=frame_action, row=0, column=1, text='Log In')

    def _init_comm_widgets(self):
        '''
        Server/client communication widgets initialization
        '''
        frame_comm = create_widget('frame', master=self.root, row=0, column=1, padx=0, pady=0)
        frame_recv = create_widget('labeled_frame', master=frame_comm, row=0, column=1, text='Receive')
        frame_send = create_widget('labeled_frame', master=frame_comm, row=1, column=1, text='Send')
        grid_configure(frame_comm, [0], [0])
        grid_configure(frame_recv, [0], [0])

        label_status = create_widget('label', master=frame_recv, row=0, column=0, text='Status: idle')
        frame_recv_action = create_widget('frame', master=frame_recv, row=1, column=0, padx=0, pady=0)
        button_view = create_widget('button', master=frame_recv_action, row=0, column=0, text='View')
        button_download = create_widget('button', master=frame_recv_action, row=0, column=1, text='Download')

        frame_send_action = create_widget('frame', master=frame_send, row=0, column=0, padx=0, pady=0)
        button_enter = create_widget('button', master=frame_send_action, row=0, column=0, text='Enter')
        button_upload = create_widget('button', master=frame_send_action, row=0, column=1, text='Upload')
        button_eval = create_widget('button', master=frame_send_action, row=1, column=0, columnspan=2, text='Auto evaluate')

    def _init_log_widgets(self):
        '''
        Log widgets initailization
        '''
        frame_log = create_widget('labeled_frame', master=self.root, row=0, column=2, text='Log')
        grid_configure(frame_log, [0], [0])
        self.scrtext_log = scrolledtext.ScrolledText(master=frame_log, width=20, height=10)
        self.scrtext_log.grid(row=0, column=0, sticky='NSEW', padx=5, pady=5)

    def mainloop(self):
        '''
        Start mainloop of GUI
        '''
        tk.mainloop()

    def _quit(self):
        '''
        Quit handling
        '''
        self.root.quit()
        self.root.destroy()