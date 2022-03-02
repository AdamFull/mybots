from ast import Load
import json
from threading import Lock, Thread
import os

class ConfigMeta(type):
    _instances = {}

    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

    

class Configuration(metaclass=ConfigMeta):
    _config: dict = {}
    _config_path: str = ""

    def __init__(self):
        self._config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self.Load()

    def Load(self) -> None:
        with open(self._config_path) as json_file:
            self._config = json.load(json_file)

    def Save(self) -> None:
        with open(self._config_path, 'w') as outfile:
            json.dump(self._config, outfile, indent=4)

    def GetDownloaded(self) -> list:
        return self._config["downloaded"]

    def AddDownloaded(self, track: str) -> None:
        self._config["downloaded"].append(track)
        self.Save()
    
    def RemoveDownloaded(self, track: str) -> None:
        self._config["downloaded"].remove(track)
        self.Save()

    def GetCheckInterval(self) -> int:
        return self._config["check_interval"]

    def GetLogin(self) -> str:
        return self._config["login"]

    def GetPassword(self) -> str:
        return self._config["password"]

    def GetOutputPath(self) -> str:
        return self._config["output_dir"]