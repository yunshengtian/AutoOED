import tkinter as tk
from autooed.system.gui.widgets.utils.layout import grid_configure


class Listbox:
    '''
    Tkinter Listbox with Scrollbar and custom features
    '''
    def __init__(self, master):
        self.master = master
        self.listbox = tk.Listbox(master=self.master, selectmode=tk.SINGLE, exportselection=False)
        self.scrollbar = tk.Scrollbar(master=self.master)
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        self.reload_cmd = None

        self.get = self.listbox.get
        self.insert = self.listbox.insert
        self.delete = self.listbox.delete
        self.select_set = self.listbox.select_set
        self.select_clear = self.listbox.select_clear
        self.select_event = lambda: self.listbox.event_generate('<<ListboxSelect>>')
        self.curselection = self.listbox.curselection
        self.size = self.listbox.size

    def grid(self):
        self.listbox.grid(row=0, column=0, sticky='NSEW')
        self.scrollbar.grid(row=0, column=1, sticky='NSEW')
        grid_configure(self.master, [0], [0])

    def bind_cmd(self, reload_cmd=None, select_cmd=None):
        '''
        Bind reload command and select command to listbox
        '''
        self.reload_cmd = reload_cmd
        if select_cmd is not None: self.listbox.bind('<<ListboxSelect>>', select_cmd)

    def reload(self):
        '''
        Reload listbox items
        '''
        assert self.reload_cmd is not None
        self.listbox.delete(0, tk.END)
        for item in self.reload_cmd():
            self.listbox.insert(tk.END, item)

    def locate(self, text):
        '''
        Locate listbox at given text
        '''
        all_items = self.listbox.get(0, tk.END)
        return all_items.index(text)

    def select(self, text):
        '''
        Select a given text in listbox
        '''
        index = self.locate(text)
        self.listbox.select_set(index)
        self.listbox.event_generate('<<ListboxSelect>>')