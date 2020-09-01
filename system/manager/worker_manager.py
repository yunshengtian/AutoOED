import os
import yaml


class WorkerManager:
    '''
    Worker config management in file system
    '''
    # create folder
    def __init__(self):
        self.worker_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'worker')
        os.makedirs(self.worker_dir, exist_ok=True)

    def save_worker(self, config):
        '''
        Save worker config as yaml file
        '''
        wid = config['id']
        config_path = os.path.join(self.worker_dir, f'{wid}.yml')
        try:
            with open(config_path, 'w') as fp:
                yaml.dump(config, fp, default_flow_style=False, sort_keys=False)
        except:
            raise Exception('not a valid worker config')
        
    def load_worker(self, wid):
        '''
        Load worker config from yaml file
        '''
        config_path = os.path.join(self.worker_dir, f'{wid}.yml')
        try:
            with open(config_path, 'r') as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
        except:
            raise Exception('not a valid config file')
        return config

    def list_worker(self):
        '''
        List all the workers saved
        '''
        return [name[:-4] for name in os.listdir(self.worker_dir) if name.endswith('.yml')]

    def remove_worker(self, wid):
        '''
        Remove a worker from saved workers
        '''
        config_path = os.path.join(self.worker_dir, f'{wid}.yml')
        try:
            os.remove(config_path)
        except:
            raise Exception("worker doesn't exist")