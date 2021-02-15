from system.gui.utils.figure import embed_figure
from .view import VizStatsView


class VizStatsController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        # set values from root
        self.problem_cfg = self.root_controller.problem_cfg
        self.data_agent = self.root_controller.data_agent

        self.view = VizStatsView(self.root_view, self.problem_cfg)

        # connect matplotlib figure with tkinter GUI
        embed_figure(self.view.fig, self.root_view.frame_stat)

        # refresh figure
        self.view.fig.tight_layout()
        self.redraw()

    def redraw(self):
        '''
        Redraw hypervolume and prediction error curves
        '''
        hypervolume = self.data_agent.load_hypervolume()
        model_error = self.data_agent.load_model_error()

        self.view.redraw(hypervolume, model_error)