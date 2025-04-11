import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QScrollArea, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from core.data import load_data_sync, save_data_sync

class NoteDetailWidget(QWidget):
    def __init__(self, note, back_callback, edit_callback):
        super().__init__()
        self.note = note
        self.back_callback = back_callback
        self.edit_callback = edit_callback
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Title: " + self.note.get("title", "Untitled")))
        content_label = QLabel(self.note.get("note_text", ""))
        content_label.setWordWrap(True)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.addWidget(content_label)
        scroll.setWidget(content_container)
        layout.addWidget(scroll)
        images = self.note.get("images", [])
        if images:
            hl = QHBoxLayout()
            for i in images:
                pix = QPixmap(i) if os.path.exists(i) else QPixmap()
                if not pix.isNull():
                    thumb = pix.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    lbl = QLabel()
                    lbl.setPixmap(thumb)
                    hl.addWidget(lbl)
            layout.addLayout(hl)
        link = self.note.get("link", "")
        if link:
            link_layout = QHBoxLayout()
            link_layout.addWidget(QLabel("Link:"))
            self.link_label = QLabel(link)
            link_layout.addWidget(self.link_label)
            btn_copy = QPushButton("Copy Link")
            btn_copy.clicked.connect(self.copy_link)
            link_layout.addWidget(btn_copy)
            layout.addLayout(link_layout)
        btn_layout = QHBoxLayout()
        btn_delete = QPushButton("Delete Note")
        btn_edit = QPushButton("Edit Note")
        btn_toggle = QPushButton()
        self.update_fav_button_text(btn_toggle)
        btn_back = QPushButton("Back")
        btn_layout.addWidget(btn_delete)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_toggle)
        btn_layout.addWidget(btn_back)
        layout.addLayout(btn_layout)
        btn_delete.clicked.connect(self.delete_note)
        btn_edit.clicked.connect(lambda: self.edit_callback(self.note))
        btn_toggle.clicked.connect(lambda: self.toggle_favorite(btn_toggle))
        btn_back.clicked.connect(self.back_callback)
    def copy_link(self):
        if self.note.get("link"):
            QApplication.clipboard().setText(self.note["link"])
            QMessageBox.information(self, "Copied", "Note link copied to clipboard.")
    def delete_note(self):
        d = load_data_sync()
        nid = self.note.get("id")
        d["notes"] = [x for x in d["notes"] if x.get("id") != nid]
        try:
            save_data_sync(d)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        QMessageBox.information(self, "Deleted", "Note has been deleted.")
        QApplication.instance().tray_icon.showMessage("Note Deleted", "The note has been successfully deleted.", QApplication.instance().tray_icon.Information, 5000)
        self.back_callback()
    def toggle_favorite(self, btn):
        d = load_data_sync()
        nid = self.note.get("id")
        for note in d["notes"]:
            if note.get("id") == nid:
                note["favorite"] = not note.get("favorite", False)
                self.note["favorite"] = note["favorite"]
                break
        try:
            save_data_sync(d)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        self.update_fav_button_text(btn)
        QMessageBox.information(self, "Updated", "Favorite status updated.")
    def update_fav_button_text(self, btn):
        if self.note.get("favorite", False):
            btn.setText("Unmark Favorite")
        else:
            btn.setText("Mark as Favorite")
