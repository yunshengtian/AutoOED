import numpy as np

from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.utils.layout import grid_configure
from autooed.system.gui.widgets.table import Table
from autooed.system.gui.visualization.database.enter_design import EnterDesignController
from autooed.system.gui.visualization.database.enter_performance import EnterPerformanceController
from autooed.system.gui.visualization.database.start_eval import StartEvalController
from autooed.system.gui.visualization.database.stop_eval import StopEvalController
from autooed.system.gui.visualization.database.display import DisplaySettingsController


class VizDatabaseView:

    def __init__(self, root_view, columns, can_eval):
        self.root_view = root_view
        self.root = self.root_view.root
        frame_db = self.root_view.frame_db

        self.widget = {}

        frame_table = create_widget('frame', master=frame_db, row=0, column=0, padx=0, pady=0)
        self.widget['table'] = Table(master=frame_table, columns=columns)

        frame_action = create_widget('frame', master=frame_db, row=1, column=0, padx=0, pady=0)
        if can_eval:
            grid_configure(frame_action, 0, [2])
        else:
            grid_configure(frame_action, 0, [1])
        
        frame_enter = create_widget('frame', master=frame_action, row=0, column=0, padx=0, pady=0)
        self.widget['enter_design'] = create_widget('button', master=frame_enter, row=0, column=0, text='Enter Design')
        self.widget['enter_performance'] = create_widget('button', master=frame_enter, row=0, column=1, text='Enter Performance')

        if can_eval:
            frame_eval = create_widget('frame', master=frame_action, row=0, column=1, padx=0, pady=0)
            self.widget['start_eval'] = create_widget('button', master=frame_eval, row=0, column=0, text='Start Evaluation')
            self.widget['stop_eval'] = create_widget('button', master=frame_eval, row=0, column=1, text='Stop Evaluation')

        self.widget['set_display'] = create_widget('button', master=frame_action, row=0, column=2 if can_eval else 1, sticky='E', text='Display Settings')


class VizDatabaseController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        # set values from root
        self.database = self.root_controller.database
        self.table_name = self.root_controller.table_name
        self.agent, self.scheduler = self.root_controller.agent, self.root_controller.scheduler
        can_eval = self.agent.can_eval

        columns = self.database.get_column_names(self.table_name)
        self.columns_view = [col for col in columns if not col.startswith('_')] # columns for viewing only
        self.columns_pred_mean = [col for col in columns if col.startswith('_') and 'pred_mean' in col] # columns with prediction data
        self.columns_pred_std = [col for col in columns if col.startswith('_') and 'pred_std' in col] # columns with prediction data
        self.view = VizDatabaseView(self.root_view, columns=self.columns_view, can_eval=can_eval)
        self.table = self.view.widget['table']

        self.view.widget['enter_design'].configure(command=self.enter_design)
        self.view.widget['enter_performance'].configure(command=self.enter_performance)
        if can_eval:
            self.view.widget['start_eval'].configure(command=self.start_eval)
            self.view.widget['stop_eval'].configure(command=self.stop_eval)
        self.view.widget['set_display'].configure(command=self.update_display)

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

    def start_eval(self):
        '''
        Start auto evaluation at certain rows
        '''
        StartEvalController(self)

    def stop_eval(self):
        '''
        Stop auto evaluation at certain rows
        '''
        StopEvalController(self)

    def update_display(self):
        '''
        Update display settings
        '''
        DisplaySettingsController(self)
