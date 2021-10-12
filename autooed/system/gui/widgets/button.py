import tkinter as tk


class Button(tk.Button):
    '''
    tkinter Button with convenient functions
    '''
    def enable(self):
        if self['state'] != tk.NORMAL:
            self.configure(state=tk.NORMAL)

    def disable(self):
        if self['state'] != tk.DISABLED:
            self.configure(state=tk.DISABLED)