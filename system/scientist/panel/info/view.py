from system.gui.modules import ProblemInfo


class PanelInfoView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.widget = {}

        self.widget['problem_info'] = ProblemInfo(master=self.root_view.root, row=0, column=1)