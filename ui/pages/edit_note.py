import os
from PyQt5.QtWidgets import QListWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from ui.pages.new_note import NewNoteWidget
from core.api import send_note_api
from core.data import save_data_sync
from PyQt5.QtWidgets import QApplication

class EditNoteWidget(NewNoteWidget):
    def __init__(self, note, notes_update_callback):
        super().__init__(notes_update_callback)
        self.note = note
        self.btn_share_note.setText("Update Note")
        self.populate_fields()
    def populate_fields(self):
        self.title_edit.setText(self.note.get("title", ""))
        self.note_edit.setText(self.note.get("note_text", ""))
        self.selected_images = self.note.get("images", [])
        self.image_list.clear()
        for img in self.selected_images:
            item = QListWidgetItem(os.path.basename(img))
            pix = QPixmap(img)
            if not pix.isNull():
                item.setIcon(QIcon(pix.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
            self.image_list.addItem(item)
        link = self.note.get("link", "")
        if link:
            self.note_url = link
            self.url_label.setText(link)
            self.url_label.show()
            self.btn_copy_url.show()
    def share_note(self):
        title = self.title_edit.text().strip()
        content = self.note_edit.toPlainText().strip()
        if not title or not content:
            QMessageBox.warning(self, "Error", "Title and Content cannot be empty!")
            return
        payload = {"title": title, "content": content}
        try:
            resp = send_note_api(payload, self.selected_images)
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
                QMessageBox.information(self, "Success", "Note updated!\nNew Link: " + link)
                QApplication.instance().tray_icon.showMessage("Note Updated", f"Note '{title}' has been updated.\nNew Link: {link}", QApplication.instance().tray_icon.Information, 5000)
                self.url_label.setText(link)
                self.url_label.show()
                self.btn_copy_url.show()
                self.save_to_local(title, content, self.selected_images, link, note_id=self.note["id"], category_id=self.note.get("category_id"), favorite=self.note.get("favorite", False))
                self.notes_update_callback()
                self.reset_form(True)
            else:
                QMessageBox.warning(self, "API Error", "Could not update note: " + js.get("error", "Unknown API error"))
        else:
            QMessageBox.warning(self, "HTTP Error", "Status: " + str(resp.status_code) + "\n" + resp.text)
