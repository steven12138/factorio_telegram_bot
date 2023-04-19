import yaml

class config:
    def __init__(self,path):
        self.path = path
        with open(path, 'r') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
    def save(self):
        with open(self.path, 'w') as f:
            yaml.dump(self.config, f)