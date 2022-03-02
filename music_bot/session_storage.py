from threading import Lock

class SessionMeta(type):
    _instances = {}

    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class SessionStorage(metaclass=SessionMeta):
    _downloading_threads: list = []
    def __init__(self) -> None:
        pass

    def GetDownloadings(self) -> list:
        return self._downloading_threads

    def SetDownloadings(self, downloadings) -> None:
        self._downloading_threads = downloadings

    def AddDownloading(self, thread) -> None:
        self._downloading_threads.append(thread)

    def DelDownloading(self, index) -> None:
        del self._downloading_threads[index]