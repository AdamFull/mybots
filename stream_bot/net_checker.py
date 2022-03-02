import time
import json
import requests
from configuration import Configuration

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class NetChecker(metaclass=SingletonMeta):
    def IsOnline(self, username: str) -> bool:
        try:
            resp = requests.get(f'https://chaturbate.com/api/chatvideocontext/{username}/')
            if resp.status_code == 200:
                return resp.json()["room_status"] == "public"
            else:
                return False
        except:
            return False

    def RequestFollowing(self):
        url = "https://chaturbate.com/statsapi/?username=admfull&token=Zvs1kkSKTh5bv0fQ1iZp0pEv"
        
        
    
    def GetOnlinesList(self) -> list:
        online_models = list()
        for model in Configuration().GetModels():
            if self.IsOnline(model):
                online_models.append(model)
        return online_models

