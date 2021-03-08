import os
import tkinter as tk
from tkinter import ttk
from system.gui.widgets.image import ImageFrame
from system.gui.utils.grid import grid_configure
from system.utils.path import get_root_dir
from system.params import *


class ScientistView:

    def __init__(self, root):
        '''
        GUI initialization
        '''
        # GUI root initialization
        self.root = root
        self.root.geometry(f'{WIDTH}x{HEIGHT}')
        grid_configure(self.root, 2, 0, row_weights=[1, 1, 20]) # configure for resolution change

        self._init_menu()
        self._init_viz()

    def _init_menu(self):
        '''
        Menu initialization
        '''
        # top-level menu
        self.menu = tk.Menu(master=self.root, relief='raised')
        self.root.config(menu=self.menu)

        # sub-level menu
        self.menu_config = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='Config', menu=self.menu_config)
        self.menu_config.add_command(label='Load')
        self.menu_config.add_command(label='Create')
        self.menu_config.add_command(label='Change')

        self.menu_problem = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='Problem', menu=self.menu_problem)
        self.menu_problem.add_command(label='Manage')

        self.menu_eval = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='Evaluation', menu=self.menu_eval)
        self.menu_eval.add_command(label='Start')
        self.menu_eval.add_command(label='Stop')

        self.menu_export = tk.Menu(master=self.menu, tearoff=0)
        self.menu.add_cascade(label='Export', menu=self.menu_export)
        self.menu_export.add_command(label='Database')
        self.menu_export.add_command(label='Statistics')
        self.menu_export.add_command(label='Figures')
        
    def _init_viz(self):
        '''
        Visualization initialization
        '''
        frame_viz = tk.Frame(master=self.root)
        frame_viz.grid(row=0, column=0, rowspan=3, sticky='NSEW')
        grid_configure(frame_viz, 0, 0)

        # configure tab widgets
        self.nb_viz = ttk.Notebook(master=frame_viz)
        self.nb_viz.grid(row=0, column=0, sticky='NSEW')
        self.frame_plot = tk.Frame(master=self.nb_viz)
        self.frame_stat = tk.Frame(master=self.nb_viz)
        self.frame_db = tk.Frame(master=self.nb_viz)
        self.nb_viz.add(child=self.frame_plot, text='Visualization')
        self.nb_viz.add(child=self.frame_stat, text='Statistics')
        self.nb_viz.add(child=self.frame_db, text='Database')
        grid_configure(self.frame_plot, [0], [0])
        grid_configure(self.frame_stat, [0], [0])
        grid_configure(self.frame_db, [0], [0])

        # temporarily disable tabs until data loaded
        self.nb_viz.tab(0, state=tk.DISABLED)
        self.nb_viz.tab(1, state=tk.DISABLED)
        self.nb_viz.tab(2, state=tk.DISABLED)

        # initialize tutorial image
        img_path = os.path.join(get_root_dir(), 'system', 'static', 'tutorial.png')
        self.image_tutorial = ImageFrame(master=self.root, img_path=img_path)
        self.image_tutorial.grid(row=0, column=0, rowspan=3, sticky='NSEW')

    def activate_viz(self):
        '''
        activate visualization tabs
        '''
        self.nb_viz.tab(0, state=tk.NORMAL)
        self.nb_viz.tab(1, state=tk.NORMAL)
        self.nb_viz.tab(2, state=tk.NORMAL)
        self.nb_viz.select(0)