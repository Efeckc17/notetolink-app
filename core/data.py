import os
import json
from datetime import datetime
from PyQt5.QtCore import QObject, QThread, pyqtSignal

LOCAL_CACHE_FILE = "notes_data.json"

class DataWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    def load(self):
        try:
            if os.path.exists(LOCAL_CACHE_FILE):
                with open(LOCAL_CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"categories": [], "notes": []}
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))
    def save(self, data):
        try:
            with open(LOCAL_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))

def run_data_worker(fn, callback, error_callback, *args, **kwargs):
    thread = QThread()
    worker = DataWorker()
    worker.moveToThread(thread)
    thread.started.connect(lambda: fn(worker, *args, **kwargs))
    worker.finished.connect(callback)
    worker.error.connect(error_callback)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.start()

def load_data_sync():
    if os.path.exists(LOCAL_CACHE_FILE):
        try:
            with open(LOCAL_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"categories": [], "notes": []}
    return {"categories": [], "notes": []}

def save_data_sync(data):
    try:
        with open(LOCAL_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        raise Exception("Failed to save data: " + str(e))
