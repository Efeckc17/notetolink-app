import uuid
from datetime import datetime
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QMessageBox, QApplication
from PyQt5.QtCore import Qt
from core.data import load_data_sync, save_data_sync
from core.api import send_note_api

class QuickNoteDialog(QDialog):
    def __init__(self, notes_update_callback):
        super().__init__()
        self.notes_update_callback = notes_update_callback
        self.note_url = None
        self.init_ui()
    def init_ui(self):
        self.setWindowTitle("Quick Note")
        layout = QVBoxLayout(self)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Note Title")
        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Write your note here...")
        self.btn_share = QPushButton("Share Note")
        self.url_label = QLabel("")
        self.btn_copy_url = QPushButton("Copy URL")
        self.url_label.hide()
        self.btn_copy_url.hide()
        layout.addWidget(self.title_edit)
        layout.addWidget(self.note_edit)
        layout.addWidget(self.btn_share)
        url_layout = QHBoxLayout()
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.btn_copy_url)
        layout.addLayout(url_layout)
        self.btn_share.clicked.connect(self.share_note)
        self.btn_copy_url.clicked.connect(self.copy_url)
    def share_note(self):
        title = self.title_edit.text().strip()
        content = self.note_edit.toPlainText().strip()
        if not title or not content:
            QMessageBox.warning(self, "Error", "Title and Content cannot be empty!")
            return
        payload = {"title": title, "content": content}
        try:
            resp = send_note_api(payload, [])
        except Exception as e:
            QMessageBox.warning(self, "Network Error", str(e))
            return
        if resp.status_code == 200:
            try:
                js = resp.json()
            except Exception:
                QMessageBox.warning(self, "Error", "JSON parse error.")
                return
            if js.get("success"):
                link = js.get("link", "Unknown")
                self.note_url = link
                QMessageBox.information(self, "Success", "Note shared!\nLink: " + link)
                QApplication.instance().tray_icon.showMessage("Note Shared", f"Quick Note '{title}' has been shared.\nLink: {link}", QApplication.instance().tray_icon.Information, 5000)
                self.url_label.setText(link)
                self.url_label.show()
                self.btn_copy_url.show()
                ddata = load_data_sync()
                nid = str(uuid.uuid4())
                ddata["notes"].append({
                    "id": nid,
                    "title": title,
                    "note_text": content,
                    "images": [],
                    "link": link,
                    "timestamp": datetime.now().isoformat(),
                    "category_id": None,
                    "favorite": False
                })
                try:
                    save_data_sync(ddata)
                except Exception as e:
                    QMessageBox.warning(self, "Error", "Failed to save data: " + str(e))
                self.notes_update_callback()
                self.title_edit.clear()
                self.note_edit.clear()
            else:
                QMessageBox.warning(self, "API Error", "Could not share note: " + js.get("error", "Unknown API error"))
        else:
            QMessageBox.warning(self, "HTTP Error", "Status: " + str(resp.status_code) + "\n" + resp.text)
    def copy_url(self):
        if self.note_url:
            QApplication.clipboard().setText(self.note_url)
            QMessageBox.information(self, "Copied", "Note URL copied to clipboard.")
