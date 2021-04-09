import webbrowser
import tkinter as tk
from system.gui.widgets.factory import create_widget
from system.params import VERSION, COPYRIGHT


class HelpMenu:

    def __init__(self, master_menu):

        self.menu = tk.Menu(master=master_menu, tearoff=0)
        master_menu.add_cascade(label='Help', menu=self.menu)
        self.menu.add_command(label='Version')
        self.menu.add_command(label='Documentation')
        self.menu.add_command(label='Github')
        self.menu.add_command(label='Contact')
        self.menu.entryconfig(0, command=self.show_version)
        self.menu.entryconfig(1, command=self.show_docs)
        self.menu.entryconfig(2, command=self.show_github)
        self.menu.entryconfig(3, command=self.show_contact)

    def show_version(self):

        window = create_widget('toplevel', master=self.menu, title='Version')
        create_widget('logo', master=window, row=0, column=0)
        create_widget('label', master=window, row=1, column=0, text=f'Version {VERSION}', sticky=None)
        create_widget('label', master=window, row=2, column=0, text=COPYRIGHT, sticky=None)

    def show_docs(self):

        webbrowser.open('https://autooed.readthedocs.io')

    def show_github(self):

        webbrowser.open('https://github.com/yunshengtian/AutoOED')

    def show_contact(self):

        webbrowser.open('mailto:autooed@csail.mit.edu')
