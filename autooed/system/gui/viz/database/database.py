import numpy as np

from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.grouped import AdjustableTable
from autooed.system.gui.viz.database.enter_design import EnterDesignController
from autooed.system.gui.viz.database.enter_performance import EnterPerformanceController


class VizDatabaseView:

    def __init__(self, root_view, columns):
        self.root_view = root_view
        self.root = self.root_view.root

        self.widget = {}
        
        frame_db = create_widget('frame', master=self.root_view.frame_db, row=0, column=0, padx=0, pady=0)
        self.widget['table'] = AdjustableTable(master=frame_db, columns=columns)

        frame_enter = create_widget('frame', master=frame_db, row=1, column=0, padx=0, pady=0)
        self.widget['enter_design'] = create_widget('button', master=frame_enter, row=0, column=0, text='Enter Design')
        self.widget['enter_performance'] = create_widget('button', master=frame_enter, row=0, column=1, text='Enter Performance')
        self.widget['table'].widget['set'].grid(row=1, column=1)


class VizDatabaseController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        # set values from root
        self.database = self.root_controller.database
        self.table_name = self.root_controller.table_name
        self.agent, self.scheduler = self.root_controller.agent, self.root_controller.scheduler

        columns = self.database.get_column_names(self.table_name)
        self.columns_view = [col for col in columns if not col.startswith('_')] # columns for viewing only
        self.columns_pred_mean = [col for col in columns if col.startswith('_') and 'pred_mean' in col] # columns with prediction data
        self.columns_pred_std = [col for col in columns if col.startswith('_') and 'pred_std' in col] # columns with prediction data
        self.view = VizDatabaseView(self.root_view, columns=self.columns_view)
        self.table = self.view.widget['table']

        self.view.widget['enter_design'].configure(command=self.enter_design)
        self.view.widget['enter_performance'].configure(command=self.enter_performance)

        self.update_data()

    def update_data(self):
        '''
        Update table data
        '''
        data = self.database.load_table(name=self.table_name, column=self.columns_view + self.columns_pred_mean + self.columns_pred_std)

        status_idx, pareto_idx = self.columns_view.index('status'), self.columns_view.index('pareto')
        data_view_dim, obj_dim = len(self.columns_view), len(self.columns_pred_mean)
        data_processed = []

        for row_data in data:
            row_data_processed = list(row_data[:data_view_dim])

            # transform the pareto column to bool
            row_data_processed[pareto_idx] = bool(row_data_processed[pareto_idx])

            # update the objective columns for unevaluated data with predicted values
            if row_data[status_idx] == 'unevaluated':
                for i, (column_mean, column_std) in enumerate(zip(self.columns_pred_mean, self.columns_pred_std)):
                    pred_mean, pred_std = row_data[data_view_dim + i], row_data[data_view_dim + obj_dim + i]
                    if pred_mean is None or pred_std is None: continue
                    obj_name = column_mean.replace('_pred_mean', '')[1:]
                    assert obj_name == column_std.replace('_pred_std', '')[1:], 'objective name sequence error'
                    obj_idx = self.columns_view.index(obj_name)
                    row_data_processed[obj_idx] = complex(pred_mean, pred_std)
            data_processed.append(row_data_processed)

        self.table.load(data_processed)

    def get_config(self):
        return self.root_controller.get_config()

    def get_problem_cfg(self):
        return self.root_controller.get_problem_cfg()

    def enter_design(self):
        '''
        Enter design variables
        '''
        EnterDesignController(self)

    def enter_performance(self):
        '''
        Enter performance values at certain rows
        '''
        EnterPerformanceController(self)
