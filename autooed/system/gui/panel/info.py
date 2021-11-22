from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.utils.layout import grid_configure


class PanelInfoView:

    def __init__(self, root_view, exp_name, problem_name):
        self.root_view = root_view

        self.widget = {}

        frame_info = create_widget('labeled_frame', master=self.root_view.root, row=0, column=1, text='Experiment')
        grid_configure(frame_info, 0, 0)

        create_widget('label', master=frame_info, row=0, column=0, text=f'Name: {exp_name}')
        create_widget('label', master=frame_info, row=1, column=0, text=f'Problem: {problem_name}')
        self.widget['update'] = create_widget('button', master=frame_info, row=2, column=0, text='Update Config')


class PanelInfoController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        exp_name = self.root_controller.table_name
        problem_name = self.root_controller.problem_cfg['name']

        self.view = PanelInfoView(self.root_view, exp_name, problem_name)

        self.view.widget['update'].configure(command=self.update_config)

    def update_config(self):
        self.root_controller.update_experiment()

    def enable_update(self):
        self.view.widget['update'].enable()

    def disable_update(self):
        self.view.widget['update'].disable()
