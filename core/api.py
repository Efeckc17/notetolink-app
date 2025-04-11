import os
import mimetypes
from io import BytesIO
import requests

API_URL = "https://notetolink.win/api/addnote"

def send_note_api(payload, images):
    files_tuple = []
    file_objs = []
    if not images:
        files_tuple.append(("images", ("dummy.jpg", BytesIO(b""), "image/jpeg")))
    else:
        for ip in images:
            try:
                f = open(ip, "rb")
                file_objs.append(f)
                mimetype, _ = mimetypes.guess_type(ip)
                if not mimetype:
                    mimetype = "application/octet-stream"
                files_tuple.append(("images", (os.path.basename(ip), f, mimetype)))
            except Exception as e:
                raise Exception("Failed to open image: " + ip) from e
    headers = {"User-Agent": "Mozilla/5.0", "Origin": "https://notetolink.win", "Referer": "https://notetolink.win/"}
    try:
        resp = requests.post(API_URL, data=payload, files=files_tuple, headers=headers, timeout=15)
    finally:
        for f in file_objs:
            f.close()
    return resp
