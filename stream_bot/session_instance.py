from threading import Lock

# create today streamers list
class SessionMeta(type):
    _instances = {}

    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class SessionInstance(metaclass=SessionMeta):
    _settings: dict = dict()
    _recording: list = list()
    _hilos: list = list()

    def __init__(self) -> None:
        pass

    def GetSettings(self) -> dict:
        return self._settings

    def SetSettings(self, new_settings: dict) -> None:
        self._settings = new_settings

    def GetRecording(self) -> list:
        return self._recording

    def AddRecord(self, nrecord) -> None:
        self._recording.append(nrecord)

    def DelRecord(self, index) -> None:
        del self._recording[index]

    def GetHilos(self) -> list:
        return self._hilos

    def AddHilo(self, hilo) -> None:
        self._hilos.append(hilo)

    def DelHilo(self, index) -> None:
        del self._hilos[index]

    def SetHilos(self, hilos: list) -> None:
        self._hilos = hilos