class Variable:
    '''
    Variable widget with customized get() and set() method
    '''
    def __init__(self, var, widget):
        '''
        '''
        self.var = var
        self.widget = widget

    def enable(self):
        '''
        Enable changing variable value
        '''
        if self.widget['state'] != 'normal':
            self.widget.configure(state='normal')
    
    def disable(self):
        '''
        Disable changing variable value
        '''
        if self.widget['state'] != 'disabled':
            self.widget.configure(state='disabled')

    def get(self):
        '''
        Get variable value
        '''
        return self.var.get()

    def set(self, val):
        '''
        Set variable value
        '''
        self.var.set(val)

    def select(self):
        pass


class CheckbuttonVar(Variable):
    '''
    Variable for checkbutton
    '''
    def get(self):
        '''
        Get entry value
        '''
        val = self.var.get() == 1
        return val

    def set(self, val):
        '''
        Set entry value
        '''
        self.var.set(int(val))


class RadiobuttonVar(Variable):
    '''
    Variable for radiobutton
    '''
    def enable(self, name=None):
        '''
        Enable changing variable value
        '''
        if name is None:
            for widget in self.widget.values():
                if widget['state'] != 'normal':
                    widget.configure(state='normal')
        else:
            assert name in self.widget
            if self.widget[name]['state'] != 'normal':
                self.widget[name].configure(state='normal')
    
    def disable(self, name=None):
        '''
        Disable changing variable value
        '''
        if name is None:
            for widget in self.widget.values():
                if widget['state'] != 'disabled':
                    widget.configure(state='disabled')
        else:
            assert name in self.widget
            if self.widget[name]['state'] != 'disabled':
                self.widget[name].configure(state='disabled')


class SpinboxVar(Variable):
    '''
    Variable for spinbox
    '''
    pass


def get_variable(name, *args, **kwargs):
    '''
    Create variable by name and other arguments
    '''
    factory = {
        'checkbutton': CheckbuttonVar,
        'radiobutton': RadiobuttonVar,
        'spinbox': SpinboxVar,
    }
    return factory[name](*args, **kwargs)