import tkinter as tk
from .view import FileView


class FileController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view
        
        self.view = FileView(self.root_view)

    def set_result_dir(self):
        '''
        Set directory for saving results
        '''
        dirname = tk.filedialog.askdirectory(parent=self.root_view.root)
        if not isinstance(dirname, str) or dirname == '': return
        self.root_controller.set_result_dir(dirname)
