import threading, time, logging, os, urllib
import eyed3
from yandex_music import Client, Track, MetaData
from configuration import Configuration
from session_storage import SessionStorage

# logging.basicConfig(level=logging.DEBUG,  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# yandex music lib docs: https://pypi.org/project/yandex-music/

if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

def ClearString(string: str) -> str:
    sr = string
    sr = sr.replace(" ", "_")
    sr = sr.replace(":", "")
    sr = sr.replace("'", "")
    sr = sr.replace(",", "")
    sr = sr.replace(".", "")
    return sr

class DownloadingThread(threading.Thread):
    _track: Track = None
    finished: bool = False
    def __init__(self, track: Track):
        threading.Thread.__init__(self)
        self._track = track
        self.skip_block = False
        self._track.title

    def GetTrackId(self) -> str:
        return self._track.track_id

    def GetTrackName(self) -> str:
        return self._track.title

    def GetTrackArtist(self) -> str:
        return ClearString("&".join(self._track.artists_name()))

    def run(self) -> None:
        self.trank_name = f"{self.GetTrackArtist()}-{ClearString(self.GetTrackName())}.mp3"
        track_path = os.path.join(Configuration().GetOutputPath(), self.trank_name)
        try:
            self._track.download(track_path)
        except Exception as ex:
            self.skip_block = True
            print(f"Failed to download track. Exception: {ex}")

        if not self.skip_block:
            try:
                audiofile = eyed3.load(track_path)
                audiofile.initTag()
                # albium, album_artist, artist, artist_origin, artist_url, audio_file_url
                # bpm, composer, copyright, genre, images, lyrics
                # year, title, track_num

                artists = self._track.artists_name()
                self._track.download_info
                metadata = self._track.meta_data
                albium = self._track.albums[0] if self._track.albums else None
                
                if metadata:
                    audiofile.tag.albium = metadata.album
                    audiofile.tag.composer = metadata.composer
                    audiofile.tag.genre = metadata.genre
                    audiofile.tag.lyrics = metadata.lyricist
                    audiofile.tag.track_num = metadata.number
                    audiofile.tag.year = metadata.year
                else:
                    if albium:
                        artist = albium.artistsName() if albium else "Unknown"
                        audiofile.tag.albium = albium.title if albium else "Unknown"
                        audiofile.tag.album_artist = " & ".join(artist)
                        audiofile.tag.composer = artists[0]
                        audiofile.tag.genre = albium.genre
                        # audiofile.tag.best_release_date = albium.release_date
                        audiofile.tag.album_type = albium.type
                        audiofile.tag.year = albium.year
                        audiofile.tag.track_num = albium.track_position.index

                        cover_uri = albium.cover_uri if albium.cover_uri else None
                        if cover_uri:
                            image_response = urllib.request.urlopen(f"https://{cover_uri.replace('%%', '200x200')}")
                            imagedata = image_response.read()
                            mime_type = image_response.info().get_content_type()
                            audiofile.tag.images.set(3, imagedata , mime_type ,u"Description")
                            # audiofile.tag.images.set(2, imagedata , mime_type ,u"Description")
                            # audiofile.tag.images.set(type_=3, img_data=None, mime_type="img/jpg", description=u"Desc", img_url=f"https://{cover_uri.replace('%%', '200x200')}")

                audiofile.tag.artist = " & ".join(artists)
                # audiofile.tag.artist_origin = artists[0]
                audiofile.tag.title = self._track.title

                audiofile.tag.save()
            except Exception as ex:
                print(f"Failed to add metadata: {ex}")

        self.finished = True
    

class TrackDaemon(threading.Thread):
    _client = None
    def __init__(self):
        threading.Thread.__init__(self)
        self._lock = threading.Lock()
        self.status = "online"
        self._downloading_counter = 0
        self.interval = 0
        self._client = Client.from_credentials(Configuration().GetLogin(), Configuration().GetPassword())
        self._client.logger.disabled = True
        self._client.logger.propagate = False

    def GetCounter(self) -> int:
        return self._downloading_counter

    def run(self):
        while True:
            self._downloading_counter = 0
            self.status = "online"
            downloaded_list = Configuration().GetDownloaded()
            track_list = self._requestTracks()
            self._lock.acquire()

            self.status = "requesting tracks"
            if track_list:
                track_objects = self._client.tracks(track_list)

            while True:
                if self._downloading_counter >= len(track_list):
                    break
                elif len(SessionStorage().GetDownloadings()) <= 10:
                    track = track_objects[self._downloading_counter]

                    # skipping already downloaded songs
                    if track.track_id in downloaded_list:
                        self._downloading_counter = self._downloading_counter + 1
                        continue

                    self.status = "downloading"
                    downloading_thread = DownloadingThread(track)
                    downloading_thread.start()
                    SessionStorage().AddDownloading(downloading_thread)
                    self._downloading_counter = self._downloading_counter + 1
                else:
                    self.status = "waiting"
                    time.sleep(1)

            self.status = "sleeping bzzz..."
            self._lock.release()

            for i in range(Configuration().GetCheckInterval(), 0, -1):
                self.interval = i
                time.sleep(1)

    def _requestTracks(self) -> list:
        tracks = self._client.users_likes_tracks()
        return [track.trackId for track in tracks]

    def _getTracksDiff(self, first, second) -> list:
        return (set(first) - set(second))

class CleaningThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.interval = 0
        self.lock = threading.Lock()
        
    def run(self):
        while True:
            self.lock.acquire()
            new_hilos = []
            for hilo in SessionStorage().GetDownloadings():
                if hilo.is_alive() or not hilo.finished:
                    new_hilos.append(hilo)
                else:
                    Configuration().AddDownloaded(hilo.GetTrackId())
            SessionStorage().SetDownloadings(new_hilos)
            self.lock.release()
            for i in range(5, 0, -1):
                self.interval = i
                time.sleep(1)

if __name__ == '__main__':
    if not os.path.exists(Configuration().GetOutputPath()):
        os.mkdir(Configuration().GetOutputPath())

    trackDaemon = TrackDaemon()
    trackDaemon.start()
    
    cleaningThread = CleaningThread()
    cleaningThread.start()
    while True:
        try:
            cls()
            print(f'{len(SessionStorage().GetDownloadings()):02d} alive Threads (1 Thread per non-downloader), cleaning dead/finished Threads in {cleaningThread.interval:02d} seconds, {len(Configuration().GetDownloaded()):02d} tracks downloaded')
            print(f'Online Threads (downloadings): {len(SessionStorage().GetDownloadings()):02d}. Daemon status: {trackDaemon.status}')
            print('The following tracks are being downloaded:')
            for hiloModelo in SessionStorage().GetDownloadings(): print(f'  Track: {hiloModelo.GetTrackName()}  -->  File: {os.path.basename(hiloModelo.trank_name)}')
            print(f'Next check in {trackDaemon.interval:02d} seconds\r', end='')
            time.sleep(1)
        except:
            break
#login
#loop
####get_treck_list
####check_is_downloaded
####get_diff
####download_diff
####save_diffed
####wait