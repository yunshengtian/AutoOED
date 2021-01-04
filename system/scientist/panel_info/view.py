from system.gui.widgets_modular import ProblemInfoWidget


class PanelInfoView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.widget = {}

        self.widget['problem_info'] = ProblemInfoWidget(master=self.root_view.root, row=0, column=1)