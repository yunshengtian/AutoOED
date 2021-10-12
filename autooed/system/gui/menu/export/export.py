from autooed.system.gui.menu.export.stats import MenuExportStatsController
from autooed.system.gui.menu.export.figures import MenuExportFiguresController


class MenuExportView:
    
    def __init__(self, root_view):
        self.root_view = root_view


class MenuExportController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.agent, self.scheduler = self.root_controller.agent, self.root_controller.scheduler

        self.view = MenuExportView(self.root_view)

    def export_db(self):
        '''
        Export database to csv file
        '''
        table = self.root_controller.controller['viz_database'].table
        table.export_csv()

    def export_stats(self):
        '''
        '''
        MenuExportStatsController(self)

    def export_figures(self):
        '''
        '''
        MenuExportFiguresController(self)