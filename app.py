import sys, os, json, mimetypes, requests, uuid
from datetime import datetime
from io import BytesIO
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QStackedWidget, QHBoxLayout, QVBoxLayout, QPushButton, QTextEdit, QLineEdit, QListWidget, QListWidgetItem, QLabel, QFileDialog, QMessageBox, QMenuBar, QMenu, QCheckBox, QScrollArea, QInputDialog, QAbstractItemView, QSystemTrayIcon, QAction, QDialog, QFrame
from PyQt5.QtCore import Qt, QSize, QEvent, QThread, pyqtSignal, QObject, QMimeData
from PyQt5.QtGui import QPalette, QColor, QPixmap, QIcon

API_URL = "https://notetolink.win/api/addnote"
LOCAL_CACHE_FILE = "notes_data.json"

# ----------------- DATA WORKER & UTILITIES -----------------
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
        except:
            return {"categories": [], "notes": []}
    return {"categories": [], "notes": []}

# ----------------- CUSTOM WIDGETLER -----------------
class NoteListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDropIndicatorShown(True)
    def mimeData(self, items):
        md = QMimeData()
        if items:
            md.setText(items[0].data(Qt.UserRole))
        return md
    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()
    def dragMoveEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()
    def dropEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()
            super().dropEvent(e)

class CategoryListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDropIndicatorShown(True)
    def mimeData(self, items):
        md = QMimeData()
        if items:
            md.setText(items[0].data(Qt.UserRole) if items[0].data(Qt.UserRole) is not None else "")
        return md
    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()
    def dragMoveEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()
    def dropEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()
            super().dropEvent(e)

# ----------------- NEW NOTE & QUICK NOTE -----------------
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
        self.image_list.setIconSize(QSize(100,100))
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
                        item.setIcon(QIcon(pix.scaled(100,100,Qt.KeepAspectRatio,Qt.SmoothTransformation)))
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
        files_tuple = []
        file_objs = []
        if not self.selected_images:
            files_tuple.append(("images", ("dummy.jpg", BytesIO(b""), "image/jpeg")))
        else:
            for ip in self.selected_images:
                try:
                    f = open(ip, "rb")
                    file_objs.append(f)
                    mimetype, _ = mimetypes.guess_type(ip)
                    if not mimetype:
                        mimetype = "application/octet-stream"
                    files_tuple.append(("images", (os.path.basename(ip), f, mimetype)))
                except:
                    QMessageBox.warning(self, "Error", "Failed to open image:\n" + ip)
                    return
        payload = {"title": title, "content": content}
        try:
            headers = {"User-Agent": "Mozilla/5.0", "Origin": "https://notetolink.win", "Referer": "https://notetolink.win/"}
            resp = requests.post(API_URL, data=payload, files=files_tuple, headers=headers, timeout=15)
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Network Error", str(e))
            return
        finally:
            for f in file_objs:
                f.close()
        if resp.status_code == 200:
            try:
                js = resp.json()
            except:
                QMessageBox.warning(self, "Error", "JSON parse error.")
                return
            if js.get("success"):
                link = js.get("link", "Unknown")
                self.note_url = link
                QMessageBox.information(self, "Success", "Note shared!\nLink: " + link)
                QApplication.instance().tray_icon.showMessage("Note Shared", f"Note '{title}' has been shared.\nLink: {link}", QSystemTrayIcon.Information, 5000)
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
            with open(LOCAL_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=4)
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

# ----------------- EDIT NOTE -----------------
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
                item.setIcon(QIcon(pix.scaled(100,100,Qt.KeepAspectRatio,Qt.SmoothTransformation)))
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
        files_tuple = []
        file_objs = []
        if not self.selected_images:
            files_tuple.append(("images", ("dummy.jpg", BytesIO(b""), "image/jpeg")))
        else:
            for ip in self.selected_images:
                try:
                    f = open(ip, "rb")
                    file_objs.append(f)
                    mimetype, _ = mimetypes.guess_type(ip)
                    if not mimetype:
                        mimetype = "application/octet-stream"
                    files_tuple.append(("images", (os.path.basename(ip), f, mimetype)))
                except:
                    QMessageBox.warning(self, "Error", "Failed to open image:\n" + ip)
                    return
        payload = {"title": title, "content": content}
        try:
            headers = {"User-Agent": "Mozilla/5.0", "Origin": "https://notetolink.win", "Referer": "https://notetolink.win/"}
            resp = requests.post(API_URL, data=payload, files=files_tuple, headers=headers, timeout=15)
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Network Error", str(e))
            return
        finally:
            for f in file_objs:
                f.close()
        if resp.status_code == 200:
            try:
                js = resp.json()
            except:
                QMessageBox.warning(self, "Error", "JSON parse error.")
                return
            if js.get("success"):
                link = js.get("link", "Unknown")
                self.note_url = link
                QMessageBox.information(self, "Success", "Note updated!\nNew Link: " + link)
                QApplication.instance().tray_icon.showMessage("Note Updated", f"Note '{title}' has been updated.\nNew Link: {link}", QSystemTrayIcon.Information, 5000)
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

# ----------------- NOTE DETAIL WIDGET -----------------
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
                    thumb = pix.scaled(150,150,Qt.KeepAspectRatio,Qt.SmoothTransformation)
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
            with open(LOCAL_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        QMessageBox.information(self, "Deleted", "Note has been deleted.")
        QApplication.instance().tray_icon.showMessage("Note Deleted", "The note has been successfully deleted.", QSystemTrayIcon.Information, 5000)
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
            with open(LOCAL_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=4)
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

# ----------------- MY NOTES WIDGET -----------------
class MyNotesWidget(QWidget):
    def __init__(self, open_note_callback, open_edit_callback):
        super().__init__()
        self.open_note_callback = open_note_callback
        self.open_edit_callback = open_edit_callback
        self.init_ui()
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()
        self.cat_list = CategoryListWidget()
        self.note_list = NoteListWidget()
        self.btn_new_cat = QPushButton("New Category")
        self.btn_rename_cat = QPushButton("Rename Category")
        self.btn_del_cat = QPushButton("Delete Category")
        self.btn_refresh = QPushButton("Refresh")
        left_panel.addWidget(QLabel("Categories"))
        fav = QListWidgetItem("Favorites")
        fav.setData(Qt.UserRole, "favorites")
        self.cat_list.addItem(fav)
        self.cat_list.addItem(QListWidgetItem("Uncategorized"))
        left_panel.addWidget(self.cat_list)
        left_panel.addWidget(self.btn_new_cat)
        left_panel.addWidget(self.btn_rename_cat)
        left_panel.addWidget(self.btn_del_cat)
        left_panel.addWidget(self.btn_refresh)
        right_panel.addWidget(QLabel("Notes"))
        right_panel.addWidget(self.note_list)
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)
        self.note_list.itemDoubleClicked.connect(self.on_note_doubleclick)
        self.cat_list.itemClicked.connect(self.load_notes_for_category)
        self.btn_new_cat.clicked.connect(self.new_category)
        self.btn_rename_cat.clicked.connect(self.rename_category)
        self.btn_del_cat.clicked.connect(self.delete_category)
        self.btn_refresh.clicked.connect(self.refresh_data)
        self.cat_list.viewport().installEventFilter(self)
        self.note_list.viewport().installEventFilter(self)
        self.refresh_data()
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Drop:
            if obj == self.cat_list.viewport():
                idx = self.cat_list.indexAt(event.pos())
                if idx.isValid():
                    item = self.cat_list.item(idx.row())
                    cid = item.data(Qt.UserRole)
                    mime = self.cat_list.mimeData(self.note_list.selectedItems())
                    nid = mime.text()
                    d = load_data_sync()
                    note_obj = None
                    for n in d["notes"]:
                        if n["id"] == nid:
                            note_obj = n
                            break
                    if note_obj:
                        note_obj["category_id"] = cid
                        try:
                            with open(LOCAL_CACHE_FILE, "w", encoding="utf-8") as f:
                                json.dump(d, f, ensure_ascii=False, indent=4)
                        except:
                            pass
                    self.refresh_data()
        return super().eventFilter(obj, event)
    def refresh_data(self):
        self.load_categories()
        self.load_notes_for_category()
    def load_categories(self):
        d = load_data_sync()
        self.cat_list.clear()
        fav = QListWidgetItem("Favorites")
        fav.setData(Qt.UserRole, "favorites")
        self.cat_list.addItem(fav)
        unc = QListWidgetItem("Uncategorized")
        unc.setData(Qt.UserRole, None)
        self.cat_list.addItem(unc)
        for c in d["categories"]:
            item = QListWidgetItem(c["name"])
            item.setData(Qt.UserRole, c["id"])
            self.cat_list.addItem(item)
    def load_notes_for_category(self, item=None):
        d = load_data_sync()
        self.note_list.clear()
        cid = item.data(Qt.UserRole) if item else None
        for n in reversed(d["notes"]):
            if cid == "favorites":
                if n.get("favorite", False):
                    it = QListWidgetItem(n["title"]+" - "+n["timestamp"])
                    it.setData(Qt.UserRole, n["id"])
                    self.note_list.addItem(it)
            elif cid is None:
                if n["category_id"] is None:
                    it = QListWidgetItem(n["title"]+" - "+n["timestamp"])
                    it.setData(Qt.UserRole, n["id"])
                    self.note_list.addItem(it)
            else:
                if n["category_id"] == cid:
                    it = QListWidgetItem(n["title"]+" - "+n["timestamp"])
                    it.setData(Qt.UserRole, n["id"])
                    self.note_list.addItem(it)
    def on_note_doubleclick(self, item):
        nid = item.data(Qt.UserRole)
        d = load_data_sync()
        for n in d["notes"]:
            if n["id"] == nid:
                self.open_note_callback(n)
                break
    def new_category(self):
        text, ok = QInputDialog.getText(self, "New Category", "Category Name:")
        if ok and text.strip():
            d = load_data_sync()
            cid = str(uuid.uuid4())
            d["categories"].append({"id": cid, "name": text.strip()})
            try:
                with open(LOCAL_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(d, f, ensure_ascii=False, indent=4)
            except:
                pass
            self.refresh_data()
    def rename_category(self):
        sel = self.cat_list.currentItem()
        if not sel:
            return
        cid = sel.data(Qt.UserRole)
        if cid in ("favorites", None):
            return
        d = load_data_sync()
        new_name, ok = QInputDialog.getText(self, "Rename Category", "New Name:", text=sel.text())
        if ok and new_name.strip():
            for c in d["categories"]:
                if c["id"] == cid:
                    c["name"] = new_name.strip()
                    break
            try:
                with open(LOCAL_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(d, f, ensure_ascii=False, indent=4)
            except:
                pass
            self.refresh_data()
    def delete_category(self):
        sel = self.cat_list.currentItem()
        if not sel:
            return
        cid = sel.data(Qt.UserRole)
        if cid in ("favorites", None):
            return
        res = QMessageBox.question(self, "Delete Category", "Delete this category?", QMessageBox.Yes|QMessageBox.No)
        if res == QMessageBox.Yes:
            d = load_data_sync()
            d["categories"] = [c for c in d["categories"] if c["id"] != cid]
            for n in d["notes"]:
                if n["category_id"] == cid:
                    n["category_id"] = None
            try:
                with open(LOCAL_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(d, f, ensure_ascii=False, indent=4)
            except:
                pass
            self.refresh_data()

# ----------------- SETTINGS WIDGET -----------------
class SettingsWidget(QWidget):
    def __init__(self, theme_change_callback, current_theme="dark"):
        super().__init__()
        self.theme_change_callback = theme_change_callback
        self.current_theme = current_theme
        layout = QVBoxLayout(self)
        lbl = QLabel("Settings")
        self.chk_dark_mode = QCheckBox("Enable Dark Mode")
        self.chk_dark_mode.setChecked(self.current_theme=="dark")
        layout.addWidget(lbl)
        layout.addWidget(self.chk_dark_mode)
        layout.addStretch()
        self.chk_dark_mode.stateChanged.connect(self.on_theme_toggled)
    def on_theme_toggled(self, state):
        self.current_theme = "dark" if state==Qt.Checked else "light"
        self.theme_change_callback(self.current_theme)

# ----------------- QUICK NOTE DIALOG -----------------
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
        files_tuple = [("images", ("dummy.jpg", BytesIO(b""), "image/jpeg"))]
        try:
            headers = {"User-Agent": "Mozilla/5.0", "Origin": "https://notetolink.win", "Referer": "https://notetolink.win/"}
            resp = requests.post(API_URL, data=payload, files=files_tuple, headers=headers, timeout=15)
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Network Error", str(e))
            return
        if resp.status_code == 200:
            try:
                js = resp.json()
            except:
                QMessageBox.warning(self, "Error", "JSON parse error.")
                return
            if js.get("success"):
                link = js.get("link", "Unknown")
                self.note_url = link
                QMessageBox.information(self, "Success", "Note shared!\nLink: " + link)
                QApplication.instance().tray_icon.showMessage("Note Shared", f"Quick Note '{title}' has been shared.\nLink: {link}", QSystemTrayIcon.Information, 5000)
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
                    with open(LOCAL_CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump(ddata, f, ensure_ascii=False, indent=4)
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

# ----------------- MAIN WINDOW -----------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NoteToLink Desktop")
        self.setWindowIcon(QIcon("icon.ico"))
        self.resize(1200, 700)
        self.setWindowOpacity(0.95)
        self.tray_icon = QSystemTrayIcon(QIcon("icon.ico"), self)
        self.current_theme = "dark"
        self.init_ui()
    def init_ui(self):
        self.setStyleSheet(self.get_stylesheet(self.current_theme))
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        title = QLabel("NoteToLink")
        title.setObjectName("headerTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()
        btn_settings = QPushButton("Settings")
        btn_settings.clicked.connect(lambda: self.stack.setCurrentWidget(self.settings_page))
        header_layout.addWidget(btn_settings)
        nav = QFrame()
        nav.setObjectName("nav")
        nav_layout = QVBoxLayout(nav)
        btn_new = QPushButton("New Note")
        btn_new.clicked.connect(lambda: self.stack.setCurrentWidget(self.new_note_page))
        btn_notes = QPushButton("My Notes")
        btn_notes.clicked.connect(lambda: self.stack.setCurrentWidget(self.my_notes_page))
        nav_layout.addWidget(btn_new)
        nav_layout.addWidget(btn_notes)
        nav_layout.addStretch()
        self.stack = QStackedWidget()
        self.new_note_page = NewNoteWidget(self.on_notes_updated)
        self.my_notes_page = MyNotesWidget(self.open_note_detail, self.open_edit_note)
        self.settings_page = SettingsWidget(self.change_theme, self.current_theme)
        self.stack.addWidget(self.new_note_page)
        self.stack.addWidget(self.my_notes_page)
        self.stack.addWidget(self.settings_page)
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.addWidget(header)
        body_layout = QHBoxLayout()
        body_layout.addWidget(nav, 1)
        body_layout.addWidget(self.stack, 4)
        central_layout.addLayout(body_layout)
        self.setCentralWidget(central_widget)
    def on_notes_updated(self):
        self.my_notes_page.refresh_data()
        self.stack.setCurrentWidget(self.my_notes_page)
    def open_note_detail(self, note):
        detail = NoteDetailWidget(note, back_callback=lambda: self.stack.setCurrentWidget(self.my_notes_page), edit_callback=self.open_edit_note)
        if self.stack.count() > 3:
            w = self.stack.widget(3)
            self.stack.removeWidget(w)
            w.deleteLater()
        self.stack.addWidget(detail)
        self.stack.setCurrentWidget(detail)
    def open_edit_note(self, note):
        edit = EditNoteWidget(note, notes_update_callback=self.on_notes_updated)
        if self.stack.count() > 3:
            w = self.stack.widget(3)
            self.stack.removeWidget(w)
            w.deleteLater()
        self.stack.addWidget(edit)
        self.stack.setCurrentWidget(edit)
    def change_theme(self, theme):
        self.current_theme = theme
        self.setStyleSheet(self.get_stylesheet(theme))
    def get_stylesheet(self, theme):
        if theme == "dark":
            return """
            QMainWindow { background-color: #2e2e2e; }
            #header { background-color: #3b3b3b; padding: 10px; }
            #headerTitle { color: white; font-size: 24px; font-weight: bold; }
            QPushButton { background-color: #505050; color: white; border: none; padding: 8px 16px; border-radius: 4px; }
            QPushButton:hover { background-color: #606060; }
            QLineEdit, QTextEdit, QListWidget { background-color: #3b3b3b; color: white; border: 1px solid #555; border-radius: 4px; }
            QLabel { color: white; }
            QFrame#nav { background-color: #3b3b3b; padding: 10px; }
            """
        else:
            return """
            QMainWindow { background-color: #f0f0f0; }
            #header { background-color: #e0e0e0; padding: 10px; }
            #headerTitle { color: #333; font-size: 24px; font-weight: bold; }
            QPushButton { background-color: #d0d0d0; color: #333; border: none; padding: 8px 16px; border-radius: 4px; }
            QPushButton:hover { background-color: #c0c0c0; }
            QLineEdit, QTextEdit, QListWidget { background-color: white; color: #333; border: 1px solid #aaa; border-radius: 4px; }
            QLabel { color: #333; }
            QFrame#nav { background-color: #e0e0e0; padding: 10px; }
            """
    def show_main_window(self):
        self.showNormal()
        self.activateWindow()

# ----------------- MAIN FUNCTION -----------------
def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    tray_icon = QSystemTrayIcon(QIcon("icon.ico"), app)
    tray_menu = QMenu()
    show_action = QAction("Show", tray_icon)
    quick_action = QAction("Quick Note", tray_icon)
    exit_action = QAction("Exit", tray_icon)
    tray_menu.addAction(show_action)
    tray_menu.addAction(quick_action)
    tray_menu.addAction(exit_action)
    tray_icon.setContextMenu(tray_menu)
    main_window = MainWindow()
    show_action.triggered.connect(lambda: main_window.show_main_window())
    quick_action.triggered.connect(lambda: QuickNoteDialog(main_window.on_notes_updated).exec_())
    exit_action.triggered.connect(app.quit)
    tray_icon.show()
    app.tray_icon = tray_icon
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
