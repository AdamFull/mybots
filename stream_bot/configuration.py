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
            json.dump(self._config, outfile, indent=4, sort_keys=True)

    def GetSaveInfo(self) -> dict:
        return self._config["save_info"]
    
    def GetSettings(self) -> dict:
        return self._config["settings"]

    def GetCBInfo(self) -> dict:
        return self._config["cb_info"]

    def GetTGBotData(self) -> dict:
        return self._config["bot_data"]

    #Save block
    def GetSaveDirectory(self) -> str:
        return self.GetSaveInfo()["save_directory"]

    def SetSaveDirectory(self, dir: str) -> None:
        self.GetSaveInfo()["save_directory"] = dir
        self.Save()
    
    def GetDirectoryStructure(self) -> str:
        return self.GetSaveInfo()["directory_structure"]
    
    def SetDirectoryStructure(self, placeholder: str) -> None:
        self.GetSaveInfo()["directory_structure"] = placeholder
        self.Save()
    
    def GetCompletedDirectory(self) -> str:
        return self.GetSaveInfo()["completed_directory"]
    
    def SetCompletedDirectory(self, dir: str) -> None:
        self.GetSaveInfo()["completed_directory"] = dir
        self.Save()

    #Settings block
    def GetCheckInterval(self) -> int:
        return self.GetSettings()["checkInterval"]
    
    def SetCheckInterval(self, interval: int) -> None:
        self.GetSettings()["checkInterval"] = interval
        self.Save()
        

    def GetPostProcessingCommand(self) -> str:
        return self.GetSettings()["postProcessingCommand"]
    
    def SetPostProcessingCommand(self, command: str) -> None:
        self.GetSettings()["postProcessingCommand"] = command
        self.Save()

    def GetPostProcessingThreads(self) -> int:
        return self.GetSettings()["postProcessingThreads"]
    
    def SetPostProcessingThreads(self, threads: int) -> None:
        self.GetSettings()["postProcessingThreads"] = threads
        self.Save()

    #CB data
    def GetModels(self) -> list:
        return self.GetCBInfo()["models"]
    
    def AddModel(self, name: str) -> None:
        self.GetCBInfo()["models"].append(name)
        self.Save()

    def RemoveModel(self, name: str) -> None:
        self.GetCBInfo()["models"].remove(name)
        self.Save()

    def GetGenders(self) -> list:
        return self.GetCBInfo()["genders"]
    
    def AddGender(self, name: str) -> None:
        self.GetCBInfo()["genders"].append(name)
        self.Save()

    def RemoveGender(self, name: str) -> None:
        self.GetCBInfo()["genders"].remove(name)
        self.Save()

    def GetLogin(self) -> str:
        return self.GetCBInfo()["login"]

    def SetLogin(self, login: str) -> None:
        self.GetCBInfo()["login"] = login
        self.Save()

    def GetPassword(self) -> str:
        return self.GetCBInfo()["password"]

    def SetPassword(self, password: str) -> None:
        self.GetCBInfo()["password"] = password
        self.Save()

    
    #TG bot data
    def GetBotToken(self) -> str:
        return self.GetTGBotData()["token"]

    def GetBotWhitelist(self) -> list:
        return self.GetTGBotData()["whitelist"]

    def GetBotNotificationPeriod(self) -> int:
        return self.GetTGBotData()["notification_period"]