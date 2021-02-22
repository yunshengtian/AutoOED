import numpy as np
from .view import VizDatabaseView


class VizDatabaseController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        # set values from root
        self.database = self.root_controller.database
        self.table_name = self.root_controller.table_name

        columns = self.database.get_column_names(self.table_name)
        columns = [col for col in columns if not col.startswith('_')]
        self.view = VizDatabaseView(self.root_view, columns=columns)
        self.table = self.view.widget['table']

        self.update_data()

    def update_data(self):
        '''
        Update table data
        '''
        data = self.database.load_table(name=self.table_name, column=self.view.get_table_columns())
        self.table.load(data)
