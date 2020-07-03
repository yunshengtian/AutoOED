import tkinter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler


class LocalGUI:
    '''
    Local tkinter-based GUI
    Layout:
        Figure 1: performance space (evaluated points, approximated Pareto front and true Pareto front)
        Figure 2: hypervolume curve (hypervolume value w.r.t. number of evaluations)
        Button: "optimize" (execute the optimization algorithm)
    '''
    def __init__(self, config, optimize_command, load_command):
        '''
        GUI initialization
        Input:
            config: loaded configuration file
        '''
        # GUI root
        self.root = tkinter.Tk()

        # GUI quit handling
        def gui_quit():
            self.root.quit()
            self.root.destroy()
        self.root.protocol("WM_DELETE_WINDOW", gui_quit)

        # figure placeholder in GUI
        self.fig = plt.figure(figsize=(12, 6))

        # performance space figure
        self.ax1 = self.fig.add_subplot(121)
        self.ax1.set_title('Performance Space')
        f1_name, f2_name = config['problem']['obj_name']
        self.ax1.set_xlabel(f1_name)
        self.ax1.set_ylabel(f2_name)

        # hypervolume curve figure
        self.ax2 = self.fig.add_subplot(122)
        self.ax2.set_title('Hypervolume')
        self.ax2.set_xlabel('Evaluations')
        self.ax2.set_ylabel('Hypervolume')

        # connect matplotlib figure with tkinter GUI
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.draw()
        widget = self.canvas.get_tk_widget()
        widget.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

        # data to be plotted
        self.scatter_y = None
        self.scatter_y_pareto = None
        self.line_hv = None

        # link optimization and dataloading command for GUI interaction with algorithm and database
        self._link_optimize_command(optimize_command)
        self._link_load_command(load_command)

    def _link_optimize_command(self, command):
        '''
        Link command for optimization, triggered by button "optimize"
        '''
        button = tkinter.Button(master=self.root, text="optimize", command=command)
        button.pack(side=tkinter.BOTTOM)

    def _link_load_command(self, command):
        '''
        Link command for loading performance data, triggered automatically every 100ms
        '''
        self.load_command = command
        self.root.after(100, self._redraw)

    def init_draw(self, true_pfront=None):
        '''
        First draw of performance space and hypervolume curve
        Input:
            true_pfront: ground truth Pareto front (optional)
        '''
        # plot true pareto front
        if true_pfront is not None:
            self.ax1.scatter(*true_pfront.T, color='gray', s=5, label='True Pareto front')

        # load from database
        Y, Y_pareto, hv_value = self.load_command()

        # plot performance space
        self.scatter_y = self.ax1.scatter(*Y.T, color='blue', s=10, label='Evaluated points')
        self.scatter_y_pareto = self.ax1.scatter(*Y_pareto.T, color='red', s=10, label='Approximated Pareto front')
        self.ax1.legend(loc='upper right')

        # plot hypervolume curve
        self.line_hv = self.ax2.plot(list(range(len(Y))), hv_value)[0]
        self.ax2.set_title('Hypervolume: %.2f' % hv_value[-1])

    def _redraw(self):
        '''
        Redraw performance space and hypervolume curve
        '''
        # load from database
        Y, Y_pareto, hv_value = self.load_command()

        # replot performance space
        self.scatter_y.set_offsets(Y)
        self.scatter_y_pareto.set_offsets(Y_pareto)

        # replot hypervolume curve
        self.line_hv.set_data(list(range(len(Y))), hv_value)
        self.ax2.relim()
        self.ax2.autoscale_view()
        self.ax2.set_title('Hypervolume: %.2f' % hv_value[-1])

        # refresh figure and trigger another redraw
        self.fig.canvas.draw()
        self.root.after(100, self._redraw)

    def mainloop(self):
        '''
        Start mainloop of GUI
        '''
        tkinter.mainloop()