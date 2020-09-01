import os
import yaml


class RequestManager:
    '''
    Request config management in file system
    '''
    # create folder
    def __init__(self):
        self.request_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'request')
        os.makedirs(self.request_dir, exist_ok=True)

    def save_request(self, config):
        '''
        Save request config as yaml file
        '''
        wid = config['id']
        config_path = os.path.join(self.request_dir, f'{wid}.yml')
        try:
            with open(config_path, 'w') as fp:
                yaml.dump(config, fp, default_flow_style=False, sort_keys=False)
        except:
            raise Exception('not a valid request config')
        
    def load_request(self, wid):
        '''
        Load request config from yaml file
        '''
        config_path = os.path.join(self.request_dir, f'{wid}.yml')
        try:
            with open(config_path, 'r') as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
        except:
            raise Exception('not a valid config file')
        return config

    def list_request(self):
        '''
        List all the requests saved
        '''
        return [name[:-4] for name in os.listdir(self.request_dir) if name.endswith('.yml')]

    def remove_request(self, wid):
        '''
        Remove a request from saved requests
        '''
        config_path = os.path.join(self.request_dir, f'{wid}.yml')
        try:
            os.remove(config_path)
        except:
            raise Exception("request doesn't exist")