

import json
class Config:
    @staticmethod
    def get(key):
        config = json.load(open('config.json', 'r'))
        if key not in config:
            raise KeyError(f'Key {key} not found in config')
        return config[key]
    
    @staticmethod
    def set(key, value):
        config = json.load(open('config.json', 'r'))
        if key not in config:
            raise KeyError(f'Key {key} not found in config')
        config[key] = value
        json.dump(config, open('config.json', 'w'), indent=2)

    @staticmethod
    def add(key, value):
        config = json.load(open('config.json', 'r'))
        if key in config:
            raise KeyError(f'Key {key} already exists in config')
        config[key] = value
        json.dump(config, open('config.json', 'w'), indent=2)



from config import Config as cfg

if __name__ == '__main__':
    print(cfg.get('control_frequency'))


