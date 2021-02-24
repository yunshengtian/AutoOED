from system.gui.widgets.factory import create_widget


class CreateTaskView:

    def __init__(self, root_view):
        self.window = create_widget('toplevel', master=root_view.root, title='Create Task')
        
        self.widget = {}
        self.widget['task_name'] = create_widget('labeled_entry', master=self.window, row=0, column=0, columnspan=2, 
            text='Task name', class_type='string', width=10, required=True)
        self.widget['create'] = create_widget('button', master=self.window, row=1, column=0, text='Create')
        self.widget['cancel'] = create_widget('button', master=self.window, row=1, column=1, text='Cancel')