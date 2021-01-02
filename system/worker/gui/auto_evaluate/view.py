import tkinter as tk


class AutoEvaluateView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.window = tk.Toplevel(master=self.root_view.root)
        self.window.title('Evaluate')
        self.window.resizable(False, False)

        