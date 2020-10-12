import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


class VizStatsView:

    def __init__(self, root_view):
        self.root_view = root_view

        # figure placeholder in GUI
        self.fig = plt.figure(figsize=(10, 5))

        # hypervolume curve figure
        self.ax1 = self.fig.add_subplot(121)
        self.ax1.set_title('Hypervolume')
        self.ax1.set_xlabel('Evaluations')
        self.ax1.set_ylabel('Hypervolume')
        self.ax1.xaxis.set_major_locator(MaxNLocator(integer=True))

        # model prediction error figure
        self.ax2 = self.fig.add_subplot(122)
        self.ax2.set_title('Model Prediction Error')
        self.ax2.set_xlabel('Evaluations')
        self.ax2.set_ylabel('Average Error')
        self.ax2.xaxis.set_major_locator(MaxNLocator(integer=True))