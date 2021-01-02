import tkinter as tk


class ManualFillView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.window = tk.Toplevel(master=self.root_view.root)
        self.window.title('Fill Entries')
        self.window.resizable(False, False)
