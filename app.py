import sys
import threading
from flask import Flask
from flask import request
import downloader

app = Flask(__name__)


@app.route('/')
def hello():
    return 'youbube-dl-http'

def get_arg(key):
    result = request.args.get(key)
    if result is not None:
        return result
    result = request.form.get(key)
    if result is not None:
        return result
    result = request.get_json(cache=True,silent=True).get(key)
    if result is not None:
        return result
    return None

def get_args()->dict:
    result = request.get_json(cache=True,silent=True)
    if result is None:
        result = {}
    for key in request.args:
        result[key] = request.args.get(key)
    for key in request.form:
        result[key] = request.form.get(key)
    return result

@app.get('/ping')
def ping():
    return 'pong'

@app.get('/info')
def info():
    url = get_arg('url')
    args = get_args()
    d = downloader.Downloader(url,args) 
    try:
        res = d.extract_info()
        return res
    except Exception as e:
        return str(e),400
    finally:
        d.__exit__()

downloader_map:dict[str,downloader.Downloader] = {}
downloader_lock = threading.RLock()

@app.post("/download")
def download():
    url = get_arg('url')
    if url is None:
        return "url is empty",400
    d = downloader.Downloader(url,get_args())
    downloader_lock.acquire()
    downloader_map[d.uuid] = d
    downloader_lock.release()
    d.start()
    return d.uuid

@app.get("/download/<uuid>/status")
def status(uuid):
    downloader_lock.acquire()
    d = downloader_map.get(uuid)
    downloader_lock.release()
    if d is None:
        return "download not found",404
    return d.get_status()

@app.delete("/download/<uuid>/delete")
def delete(uuid):
    downloader_lock.acquire()
    d = downloader_map.get(uuid)
    downloader_lock.release()
    if d is None:
        return "download not found",404
    if not d.is_deletable():
        return "download can not be deleted",400
    downloader_lock.acquire()
    d.__exit__()
    del downloader_map[uuid]
    downloader_lock.release()
    return "ok"

@app.get("/download/<uuid>/info")
def download_info(uuid):
    downloader_lock.acquire()
    d = downloader_map.get(uuid)
    downloader_lock.release()
    if d is None:
        return "download not found",404
    return d.extract_info()

@app.post("/download/<uuid>/retry")
def retry(uuid):
    downloader_lock.acquire()
    d = downloader_map.get(uuid)
    downloader_lock.release()
    if d is None:
        return "download not found",404
    if d.is_finished():
        return "download is finished",400
    if d.get_error() is None:
        return "download is not failed",400
    d.__exit__()

    d = downloader.Downloader(d.url,d.opts)
    d.uuid = uuid
    downloader_lock.acquire()
    downloader_map[uuid] = d
    downloader_lock.release()
    d.start()

    return "ok"

@app.get("/downloads")
def videos():
    downloader_lock.acquire()
    result = {}
    for key in downloader_map:
        d = downloader_map[key]
        result[key] = d.get_status()
    downloader_lock.release()
    return result

if __name__ == '__main__':
    app.run(debug=True, use_debugger=False, use_reloader=False,host="0.0.0.0")