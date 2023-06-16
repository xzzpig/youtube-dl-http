import threading
import uuid
import youtube_dl

class Downloader:
    def __init__(self,url:str,ydl_opts:dict):
        if ydl_opts == None:
            ydl_opts = {}
        ydl_opts['progress_hooks'] = [self._download_hook]
        
        self.uuid = uuid.uuid4().hex
        self.opts = ydl_opts
        self.ydl = youtube_dl.YoutubeDL(ydl_opts)
        self.url = url
        self._lock = threading.RLock()
        self._finished = False
        self._started = False
        self._status = None
        self._error = None

    def _download_hook(self, d):
        self._lock.acquire()
        self._status = d
        self._lock.release()
    
    def extract_info(self):
        return self.ydl.extract_info(self.url,download=False)

    def get_status(self):
        self._lock.acquire()

        status = self._status
        if status is None:
            status = {"status":"parsing"}
        if self._error is not None:
            status["error"] = str(self._error)
        status["url"] = self.url
        status["uuid"] = self.uuid
        status["source"] = self.opts.get("source")
        self._lock.release()
        return status
    
    def _download(self):
        try:
            self.ydl.download([self.url])
            self.ydl.__exit__()
            self._lock.acquire()
            self._finished = True
            self._lock.release()
        except Exception as e:
            self._lock.acquire()
            self._error = e
            self._lock.release()
            raise e

    def start(self):
        if self._started:
            return
        self._started = True
        self.thread = threading.Thread(target=self._download,daemon=True,name="Downloader-"+self.uuid)
        self.thread.start()
    
    def get_error(self):
        self._lock.acquire()
        error = self._error
        self._lock.release()
        return error

    def is_finished(self):
        self._lock.acquire()
        finished = self._finished
        self._lock.release()
        return finished

    def wait(self):
        self.thread.join()

    def is_deletable(self):
        return self.is_finished() or self.get_error() is not None

    def __exit__(self):
        self.ydl.__exit__()