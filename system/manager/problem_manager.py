import os
import yaml


class ProblemManager:
    '''
    Problem config management in file system
    '''
    def __init__(self):
        '''
        Manager initialization
        '''
        # create folder
        self.problem_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'problems', 'custom', 'yaml')
        os.makedirs(self.problem_dir, exist_ok=True)

    def save_problem(self, config):
        '''
        Save problem config as yaml file
        '''
        name = config['name']
        config_path = os.path.join(self.problem_dir, f'{name}.yml')
        try:
            with open(config_path, 'w') as fp:
                yaml.dump(config, fp, default_flow_style=False, sort_keys=False)
        except:
            raise Exception('not a valid problem config')
        
    def load_problem(self, name):
        '''
        Load problem config from yaml file
        '''
        config_path = os.path.join(self.problem_dir, f'{name}.yml')
        try:
            with open(config_path, 'r') as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
        except:
            raise Exception('not a valid config file')
        return config

    def list_problem(self):
        '''
        List all the problems saved
        '''
        return [name[:-4] for name in os.listdir(self.problem_dir) if name.endswith('.yml')]

    def remove_problem(self, name):
        '''
        Remove a problem from saved problems
        '''
        config_path = os.path.join(self.problem_dir, f'{name}.yml')
        try:
            os.remove(config_path)
        except:
            raise Exception("problem doesn't exist")
