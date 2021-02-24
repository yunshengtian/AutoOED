import tkinter as tk
from system.utils.path import get_logo_path
from system.gui.widgets.image import StaticImageFrame
from system.gui.widgets.factory import create_widget


class ScientistLoginView:

    def __init__(self, root):
        self.root = root

        frame_login = tk.Frame(master=self.root)
        frame_login.grid(row=0, column=0, padx=20, pady=20, sticky='NSEW')

        image_tutorial = StaticImageFrame(master=frame_login, img_path=get_logo_path())
        image_tutorial.grid(row=0, column=0)

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
