class Variable:
    '''
    Variable widget with customized get() and set() method
    '''
    def __init__(self, var, widget):
        '''
        '''
        self.var = var
        self.widget = widget

    def enable(self, readonly=None):
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
        'spinbox': SpinboxVar,
    }
    return factory[name](*args, **kwargs)