import time
import datetime
import os
import threading
import sys
import configparser
import streamlink
import subprocess
import queue
import requests
from telegram_notify import MessagingBot
from configuration import Configuration
from session_instance import SessionInstance

if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')
    
def readConfig():
    if not os.path.exists(f'{Configuration().GetSaveDirectory()}'):
        os.makedirs(f'{Configuration().GetSaveDirectory()}')

def postProcess():
    while True:
        while processingQueue.empty():
            time.sleep(1)
        parameters = processingQueue.get()
        model = parameters['model']
        path = parameters['path']
        filename = os.path.split(path)[-1]
        directory = os.path.dirname(path)
        file = os.path.splitext(filename)[0]
        subprocess.call(Configuration().GetPostProcessingCommand().split() + [path, filename, directory, model,  file, 'cam4'])

class Modelo(threading.Thread):
    def __init__(self, modelo):
        threading.Thread.__init__(self)
        self.modelo = modelo
        self._stopevent = threading.Event()
        self.file = None
        self.online = None
        self.lock = threading.Lock()

    def GetName(self) -> str:
        return self.modelo

    def run(self):
        isOnline = self.isOnline()
        if isOnline == False:
            self.online = False
        else:
            self.online = True
            self.file = os.path.join(Configuration().GetSaveDirectory(), self.modelo, f'{datetime.datetime.fromtimestamp(time.time()).strftime("%Y.%m.%d_%H.%M.%S")}_{self.modelo}.mp4')
            try:
                session = streamlink.Streamlink()
                streams = session.streams(f'hlsvariant://{isOnline}')
                stream = streams['best']
                fd = stream.open()
                if not isModelInListofObjects(self.modelo, SessionInstance().GetRecording()):
                    os.makedirs(os.path.join(Configuration().GetSaveDirectory(), self.modelo), exist_ok=True)
                    with open(self.file, 'wb') as f:
                        self.lock.acquire()
                        SessionInstance().AddRecord(self)
                        for index, hilo in enumerate(SessionInstance().GetHilos()):
                            if hilo.modelo == self.modelo:
                                SessionInstance().DelHilo(index)
                                break
                        self.lock.release()
                        while not (self._stopevent.isSet() or os.fstat(f.fileno()).st_nlink == 0):
                            try:
                                data = fd.read(1024)
                                f.write(data)
                            except:
                                fd.close()
                                break
                    if Configuration().GetPostProcessingCommand():
                            processingQueue.put({'model': self.modelo, 'path': self.file})
            except Exception as e:
                with open('log.log', 'a+') as f:
                    f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} EXCEPTION: {e}\n')
                self.stop()
            finally:
                self.exceptionHandler()

    def exceptionHandler(self):
        self.stop()
        self.online = False
        self.lock.acquire()
        for index, hilo in enumerate(SessionInstance().GetRecording()):
            if hilo.modelo == self.modelo:
                SessionInstance().DelRecord(index)
                break
        self.lock.release()
        try:
            file = os.path.join(os.getcwd(), self.file)
            if os.path.isfile(file):
                if os.path.getsize(file) <= 1024:
                    os.remove(file)
        except Exception as e:
            with open('log.log', 'a+') as f:
                f.write(f'\n{datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")} EXCEPTION: {e}\n')

    def isOnline(self):
        try:
            resp = requests.get(f'https://chaturbate.com/api/chatvideocontext/{self.modelo}/')
            hls_url = ''
            if 'hls_source' in resp.json():
                hls_url = resp.json()['hls_source']
            if len(hls_url):
                return hls_url
            else:
                return False
        except:
            return False

    def stop(self):
        self._stopevent.set()

class CleaningThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.interval = 0
        self.lock = threading.Lock()
        
    def run(self):
        while True:
            self.lock.acquire()
            new_hilos = []
            for hilo in SessionInstance().GetHilos():
                if hilo.is_alive() or hilo.online:
                    new_hilos.append(hilo)
            SessionInstance().SetHilos(new_hilos)
            self.lock.release()
            for i in range(10, 0, -1):
                self.interval = i
                time.sleep(1)

class AddModelsThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.wanted = []
        self.lock = threading.Lock()
        self.repeatedModels = []
        self.counterModel = 0

    def run(self):
        self.wanted = Configuration().GetModels()
        self.lock.acquire()
        aux = []
        for model in self.wanted:
            model = model.lower()
            if model in aux:
                self.repeatedModels.append(model)
            else:
                aux.append(model)
                self.counterModel = self.counterModel + 1
                if not isModelInListofObjects(model, SessionInstance().GetHilos()) and not isModelInListofObjects(model, SessionInstance().GetRecording()):
                    thread = Modelo(model)
                    thread.start()
                    SessionInstance().AddHilo(thread)
        for hilo in SessionInstance().GetRecording():
            if hilo.modelo not in aux:
                hilo.stop()
        self.lock.release()

def isModelInListofObjects(obj, lista):
    result = False
    for i in lista:
        if i.modelo == obj:
            result = True
            break
    return result

if __name__ == '__main__':
    tgbot = MessagingBot()
    tgbot.start()

    readConfig()
    if Configuration().GetPostProcessingCommand():
        processingQueue = queue.Queue()
        postprocessingWorkers = []
        for i in range(0, Configuration().GetPostProcessingThreads()):
            t = threading.Thread(target=postProcess)
            postprocessingWorkers.append(t)
            t.start()
    cleaningThread = CleaningThread()
    cleaningThread.start()
    while True:
        try:
            readConfig()
            addModelsThread = AddModelsThread()
            addModelsThread.start()
            i = 1
            for i in range(Configuration().GetCheckInterval(), 0, -1):
                cls()
                if len(addModelsThread.repeatedModels): print('The following models are more than once in wanted: [\'' + ', '.join(modelo for modelo in addModelsThread.repeatedModels) + '\']')
                print(f'{len(SessionInstance().GetHilos()):02d} alive Threads (1 Thread per non-recording model), cleaning dead/not-online Threads in {cleaningThread.interval:02d} seconds, {addModelsThread.counterModel:02d} models in wanted')
                print(f'Online Threads (models): {len(SessionInstance().GetRecording()):02d}')
                print('The following models are being recorded:')
                for hiloModelo in SessionInstance().GetRecording(): print(f'  Model: {hiloModelo.modelo}  -->  File: {os.path.basename(hiloModelo.file)}')
                print(f'Next check in {i:02d} seconds\r', end='')
                time.sleep(1)
            addModelsThread.join()
            del addModelsThread, i
        except:
            break
