import os
import uuid
from datetime import datetime
from io import BytesIO
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QMessageBox, QFileDialog, QApplication
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
from core.data import load_data_sync, save_data_sync
from core.api import send_note_api
from ui.widgets import NoteListWidget

class NewNoteWidget(QWidget):
    def __init__(self, notes_update_callback):
        super().__init__()
        self.notes_update_callback = notes_update_callback
        self.selected_images = []
        self.note_url = None
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout(self)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Note Title")
        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Write your note here...")
        self.image_list = QListWidget()
        self.image_list.setIconSize(QSize(100, 100))
        self.btn_add_images = QPushButton("Add Images")
        self.btn_share_note = QPushButton("Share Note")
        self.url_label = QLabel("")
        self.btn_copy_url = QPushButton("Copy URL")
        self.url_label.hide()
        self.btn_copy_url.hide()
        layout.addWidget(self.title_edit)
        layout.addWidget(self.note_edit)
        layout.addWidget(self.image_list)
        hl = QHBoxLayout()
        hl.addWidget(self.btn_add_images)
        hl.addWidget(self.btn_share_note)
        layout.addLayout(hl)
        url_layout = QHBoxLayout()
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.btn_copy_url)
        layout.addLayout(url_layout)
        self.btn_add_images.clicked.connect(self.add_images)
        self.btn_share_note.clicked.connect(self.share_note)
        self.btn_copy_url.clicked.connect(self.copy_url)
    def add_images(self):
        opts = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)", options=opts)
        if files:
            for f in files:
                if len(self.selected_images) >= 5:
                    break
                if f not in self.selected_images:
                    self.selected_images.append(f)
                    item = QListWidgetItem(os.path.basename(f))
                    pix = QPixmap(f)
                    if not pix.isNull():
                        item.setIcon(QIcon(pix.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
                    self.image_list.addItem(item)
    def share_note(self):
        data_file = load_data_sync()
        title = self.title_edit.text().strip()
        content = self.note_edit.toPlainText().strip()
        if not title or not content:
            QMessageBox.warning(self, "Error", "Title and Content cannot be empty!")
            return
        for n in data_file["notes"]:
            if n.get("title", "").strip() == title:
                res = QMessageBox.question(self, "Duplicate Note", "A note with the same title exists. Continue?", QMessageBox.Yes|QMessageBox.No)
                if res == QMessageBox.No:
                    return
                break
        payload = {"title": title, "content": content}
        try:
            resp = send_note_api(payload, self.selected_images)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
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
                QApplication.instance().tray_icon.showMessage("Note Shared", f"Note '{title}' has been shared.\nLink: {link}", QApplication.instance().tray_icon.Information, 5000)
                self.url_label.setText(link)
                self.url_label.show()
                self.btn_copy_url.show()
                self.save_to_local(title, content, self.selected_images, link)
                self.notes_update_callback()
                self.reset_form(True)
            else:
                QMessageBox.warning(self, "API Error", "Could not share note: " + js.get("error", "Unknown API error"))
        else:
            QMessageBox.warning(self, "HTTP Error", "Status: " + str(resp.status_code) + "\n" + resp.text)
    def copy_url(self):
        if self.note_url:
            QApplication.clipboard().setText(self.note_url)
            QMessageBox.information(self, "Copied", "Note URL copied to clipboard.")
    def save_to_local(self, title, content, images, link, note_id=None, category_id=None, favorite=False):
        d = load_data_sync()
        timestamp = datetime.now().isoformat()
        if note_id is None:
            note_id = str(uuid.uuid4())
            d["notes"].append({
                "id": note_id,
                "title": title,
                "note_text": content,
                "images": images,
                "link": link,
                "timestamp": timestamp,
                "category_id": category_id,
                "favorite": favorite
            })
        else:
            for note in d["notes"]:
                if note["id"] == note_id:
                    note["title"] = title
                    note["note_text"] = content
                    note["images"] = images
                    note["link"] = link
                    note["timestamp"] = timestamp
                    break
        try:
            save_data_sync(d)
        except Exception as e:
            QMessageBox.warning(self, "Error", "Failed to save data: " + str(e))
    def reset_form(self, keep_url=False):
        self.title_edit.clear()
        self.note_edit.clear()
        self.image_list.clear()
        self.selected_images = []
        if not keep_url:
            self.url_label.hide()
            self.btn_copy_url.hide()
