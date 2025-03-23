import sys, os, json, mimetypes, requests, uuid
from datetime import datetime
from io import BytesIO
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QStackedWidget, QHBoxLayout, QVBoxLayout, QPushButton, QTextEdit, QLineEdit, QListWidget, QListWidgetItem, QLabel, QFileDialog, QMessageBox, QMenuBar, QMenu, QCheckBox, QScrollArea, QInputDialog, QAbstractItemView, QSystemTrayIcon, QAction
from PyQt5.QtCore import Qt, QSize, QEvent, QThread, pyqtSignal, QObject, QMimeData
from PyQt5.QtGui import QPalette, QColor, QPixmap, QIcon

API_URL = "https://notetolink.win/api/addnote"
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
        except:
            return {"categories": [], "notes": []}
    return {"categories": [], "notes": []}

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

class NewNoteWidget(QWidget):
    def __init__(self, notes_update_callback):
        super().__init__()
        self.notes_update_callback = notes_update_callback
        self.selected_images = []
        self.note_url = None
        self.init_ui()
    def init_ui(self):
        l = QVBoxLayout(self)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter note title")
        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Enter note content")
        self.image_list = QListWidget()
        self.image_list.setIconSize(QSize(100,100))
        self.btn_add_images = QPushButton("Add Images")
        self.btn_share_note = QPushButton("Share Note")
        self.url_label = QLabel("")
        self.btn_copy_url = QPushButton("Copy URL")
        self.url_label.hide()
        self.btn_copy_url.hide()
        l.addWidget(QLabel("Note Title:"))
        l.addWidget(self.title_edit)
        l.addWidget(QLabel("Note Content:"))
        l.addWidget(self.note_edit)
        l.addWidget(QLabel("Selected Images:"))
        l.addWidget(self.image_list)
        hl = QHBoxLayout()
        hl.addWidget(self.btn_add_images)
        hl.addWidget(self.btn_share_note)
        l.addLayout(hl)
        ul = QHBoxLayout()
        ul.addWidget(QLabel("Your Note URL:"))
        ul.addWidget(self.url_label)
        ul.addWidget(self.btn_copy_url)
        l.addLayout(ul)
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
                    it = QListWidgetItem(os.path.basename(f))
                    pm = QPixmap(f)
                    if not pm.isNull():
                        it.setIcon(QIcon(pm.scaled(100,100,Qt.KeepAspectRatio,Qt.SmoothTransformation)))
                    self.image_list.addItem(it)
    def share_note(self):
        data_file = load_data_sync()
        title = self.title_edit.text().strip()
        content = self.note_edit.toPlainText().strip()
        if not title:
            QMessageBox.warning(self, "Error", "Note title cannot be empty!")
            return
        if not content:
            QMessageBox.warning(self, "Error", "Note content cannot be empty!")
            return
        for n in data_file["notes"]:
            if n.get("title", "").strip() == title:
                r = QMessageBox.question(self, "Duplicate Note", "A note with the same title exists. Create anyway?", QMessageBox.Yes|QMessageBox.No)
                if r == QMessageBox.No:
                    return
                break
        ft = []
        fo = []
        if not self.selected_images:
            ft.append(("images", ("dummy.jpg", BytesIO(b""), "image/jpeg")))
        else:
            for ip in self.selected_images:
                try:
                    f = open(ip, "rb")
                    fo.append(f)
                    mm, _ = mimetypes.guess_type(ip)
                    if not mm:
                        mm = "application/octet-stream"
                    ft.append(("images", (os.path.basename(ip), f, mm)))
                except:
                    QMessageBox.warning(self, "Error", "Failed to open image:\n"+ip)
                    return
        d = {"title": title, "content": content}
        try:
            h = {"User-Agent": "Mozilla/5.0", "Origin": "https://notetolink.win", "Referer": "https://notetolink.win/"}
            r = requests.post(API_URL, data=d, files=ft, headers=h, timeout=15)
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Network Error", str(e))
            return
        finally:
            for f in fo:
                f.close()
        if r.status_code == 200:
            try:
                js = r.json()
            except:
                QMessageBox.warning(self, "Error", "JSON parse error.")
                return
            if js.get("success"):
                link = js.get("link", "Unknown")
                self.note_url = link
                QMessageBox.information(self, "Success", "Note shared!\nLink: "+link)
                QApplication.instance().tray_icon.showMessage("Note Shared", "Note '"+title+"' has been shared.\nLink: "+link, QSystemTrayIcon.Information, 5000)
                self.url_label.setText(link)
                self.url_label.show()
                self.btn_copy_url.show()
                self.save_to_local(title, content, self.selected_images, link)
                self.notes_update_callback()
                self.reset_form(True)
            else:
                er = js.get("error", "Unknown API error")
                QMessageBox.warning(self, "API Error", "Could not share note: "+er)
        else:
            QMessageBox.warning(self, "HTTP Error", "Status: "+str(r.status_code)+"\n"+r.text)
    def copy_url(self):
        if self.note_url:
            QApplication.clipboard().setText(self.note_url)
            QMessageBox.information(self, "Copied", "Note URL copied to clipboard.")
    def save_to_local(self, title, content, images, link):
        d = load_data_sync()
        nid = str(uuid.uuid4())
        d["notes"].append({
            "id": nid,
            "title": title,
            "note_text": content,
            "images": images,
            "link": link,
            "timestamp": datetime.now().isoformat(),
            "category_id": None
        })
        try:
            with open(LOCAL_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Error", "Failed to save data: "+str(e))
    def reset_form(self, keep_url=False):
        self.title_edit.clear()
        self.note_edit.clear()
        self.image_list.clear()
        self.selected_images = []
        if not keep_url:
            self.url_label.hide()
            self.btn_copy_url.hide()

class NoteDetailWidget(QWidget):
    def __init__(self, note, back_callback):
        super().__init__()
        self.note = note
        self.back_callback = back_callback
        l = QVBoxLayout(self)
        l.addWidget(QLabel("Title: "+self.note.get("title", "Untitled")))
        c = QLabel(self.note.get("note_text", ""))
        c.setWordWrap(True)
        s = QScrollArea()
        s.setWidgetResizable(True)
        cw = QWidget()
        cl = QVBoxLayout(cw)
        cl.addWidget(c)
        s.setWidget(cw)
        l.addWidget(QLabel("Content:"))
        l.addWidget(s)
        im = self.note.get("images", [])
        if im:
            hl = QHBoxLayout()
            for i in im:
                if os.path.exists(i):
                    pm = QPixmap(i)
                else:
                    pm = QPixmap()
                if not pm.isNull():
                    th = pm.scaled(150,150,Qt.KeepAspectRatio,Qt.SmoothTransformation)
                    lb = QLabel()
                    lb.setPixmap(th)
                    hl.addWidget(lb)
            l.addWidget(QLabel("Images:"))
            l.addLayout(hl)
        bdel = QPushButton("Delete Note")
        bback = QPushButton("Back")
        l.addWidget(bdel)
        l.addWidget(bback)
        bdel.clicked.connect(self.delete_note)
        bback.clicked.connect(self.back_callback)
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

class MyNotesWidget(QWidget):
    def __init__(self, open_note_callback):
        super().__init__()
        self.open_note_callback = open_note_callback
        l = QHBoxLayout(self)
        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()
        self.cat_list = CategoryListWidget()
        self.note_list = NoteListWidget()
        self.btn_new_cat = QPushButton("New Category")
        self.btn_rename_cat = QPushButton("Rename Category")
        self.btn_del_cat = QPushButton("Delete Category")
        self.btn_refresh = QPushButton("Refresh")
        left_panel.addWidget(QLabel("Categories"))
        left_panel.addWidget(self.cat_list)
        left_panel.addWidget(self.btn_new_cat)
        left_panel.addWidget(self.btn_rename_cat)
        left_panel.addWidget(self.btn_del_cat)
        left_panel.addWidget(self.btn_refresh)
        right_panel.addWidget(QLabel("Notes"))
        right_panel.addWidget(self.note_list)
        l.addLayout(left_panel, 1)
        l.addLayout(right_panel, 2)
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
                    cit = self.cat_list.item(idx.row())
                    cid = cit.data(Qt.UserRole)
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
        unc_item = QListWidgetItem("Uncategorized")
        unc_item.setData(Qt.UserRole, None)
        self.cat_list.addItem(unc_item)
        for c in d["categories"]:
            it = QListWidgetItem(c["name"])
            it.setData(Qt.UserRole, c["id"])
            self.cat_list.addItem(it)
    def load_notes_for_category(self, item=None):
        d = load_data_sync()
        self.note_list.clear()
        cid = item.data(Qt.UserRole) if item else None
        for n in reversed(d["notes"]):
            if cid is None:
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
        d = load_data_sync()
        nn, ok = QInputDialog.getText(self, "Rename Category", "New Name:", text=sel.text())
        if ok and nn.strip():
            for c in d["categories"]:
                if c["id"] == cid:
                    c["name"] = nn.strip()
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
        r = QMessageBox.question(self, "Delete Category", "Delete this category?", QMessageBox.Yes|QMessageBox.No)
        if r == QMessageBox.Yes:
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

class SettingsWidget(QWidget):
    def __init__(self, theme_change_callback, current_theme="dark"):
        super().__init__()
        self.theme_change_callback = theme_change_callback
        self.current_theme = current_theme
        l = QVBoxLayout(self)
        l.addWidget(QLabel("Settings"))
        self.chk_dark_mode = QCheckBox("Enable Dark Mode")
        self.chk_dark_mode.setChecked(self.current_theme=="dark")
        l.addWidget(self.chk_dark_mode)
        l.addStretch()
        self.chk_dark_mode.stateChanged.connect(self.on_theme_toggled)
    def on_theme_toggled(self, s):
        self.current_theme = "dark" if s==Qt.Checked else "light"
        self.theme_change_callback(self.current_theme)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("icon.ico"))
        self.setWindowTitle("NoteToLink Desktop")
        self.resize(1200,700)
        self.setWindowOpacity(0.95)
        self.tray_icon = QSystemTrayIcon(QIcon("icon.ico"), self)
        self.current_theme = "dark"
        self.init_ui()
    def init_ui(self):
        mb = QMenuBar()
        self.setMenuBar(mb)
        fm = mb.addMenu("File")
        xa = fm.addAction("Exit")
        xa.triggered.connect(self.close)
        hm = mb.addMenu("Help")
        aa = hm.addAction("About...")
        aa.triggered.connect(self.show_about_dialog)
        mw = QWidget()
        self.setCentralWidget(mw)
        ml = QHBoxLayout(mw)
        self.stack = QStackedWidget()
        self.new_note_page = NewNoteWidget(self.on_notes_updated)
        self.my_notes_page = MyNotesWidget(self.open_note_detail)
        self.settings_page = SettingsWidget(self.change_theme, self.current_theme)
        self.stack.addWidget(self.new_note_page)
        self.stack.addWidget(self.my_notes_page)
        self.stack.addWidget(self.settings_page)
        menu_layout = QVBoxLayout()
        bnew = QPushButton("New Note")
        bnotes = QPushButton("My Notes")
        bset = QPushButton("Settings")
        for b in (bnew, bnotes, bset):
            b.setMinimumHeight(40)
        menu_layout.addWidget(bnew)
        menu_layout.addWidget(bnotes)
        menu_layout.addWidget(bset)
        menu_layout.addStretch()
        mwg = QWidget()
        mwg.setLayout(menu_layout)
        mwg.setFixedWidth(150)
        ml.addWidget(self.stack)
        ml.addWidget(mwg)
        bnew.clicked.connect(lambda: self.stack.setCurrentWidget(self.new_note_page))
        bnotes.clicked.connect(lambda: self.stack.setCurrentWidget(self.my_notes_page))
        bset.clicked.connect(lambda: self.stack.setCurrentWidget(self.settings_page))
        self.apply_dark_palette()
    def on_notes_updated(self):
        self.my_notes_page.refresh_data()
        self.stack.setCurrentWidget(self.my_notes_page)
    def open_note_detail(self, note):
        nd = NoteDetailWidget(note, back_callback=lambda: self.stack.setCurrentWidget(self.my_notes_page))
        c = self.stack.count()
        if c > 3:
            w = self.stack.widget(3)
            self.stack.removeWidget(w)
            w.deleteLater()
        self.stack.addWidget(nd)
        self.stack.setCurrentWidget(nd)
    def change_theme(self, th):
        self.current_theme = th
        if th=="dark":
            self.apply_dark_palette()
        else:
            self.apply_light_palette()
    def apply_dark_palette(self):
        p = QPalette()
        p.setColor(QPalette.Window, QColor(45,45,45))
        p.setColor(QPalette.WindowText, Qt.white)
        p.setColor(QPalette.Base, QColor(30,30,30))
        p.setColor(QPalette.AlternateBase, QColor(45,45,45))
        p.setColor(QPalette.ToolTipBase, Qt.white)
        p.setColor(QPalette.ToolTipText, Qt.white)
        p.setColor(QPalette.Text, Qt.white)
        p.setColor(QPalette.Button, QColor(45,45,45))
        p.setColor(QPalette.ButtonText, Qt.white)
        p.setColor(QPalette.BrightText, Qt.red)
        p.setColor(QPalette.Highlight, QColor(100,100,200))
        p.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.instance().setPalette(p)
    def apply_light_palette(self):
        p = QPalette()
        p.setColor(QPalette.Window, QColor(250,250,250))
        p.setColor(QPalette.WindowText, Qt.black)
        p.setColor(QPalette.Base, QColor(240,240,240))
        p.setColor(QPalette.AlternateBase, QColor(250,250,250))
        p.setColor(QPalette.ToolTipBase, Qt.black)
        p.setColor(QPalette.ToolTipText, Qt.black)
        p.setColor(QPalette.Text, Qt.black)
        p.setColor(QPalette.Button, QColor(240,240,240))
        p.setColor(QPalette.ButtonText, Qt.black)
        p.setColor(QPalette.BrightText, Qt.red)
        p.setColor(QPalette.Highlight, QColor(76,163,224))
        p.setColor(QPalette.HighlightedText, Qt.white)
        QApplication.instance().setPalette(p)
    def show_about_dialog(self):
        t = "NoteToLink Desktop - Advanced\n\nContact: toxi360@workmail.com\nGitHub: https://github.com/Efeckc17\nWebsite: toxi360.org\n\nDeveloped with PyQt5."
        QMessageBox.information(self, "About NoteToLink", t)
    def show_main_window(self):
        self.showNormal()
        self.activateWindow()

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    tray_icon = QSystemTrayIcon(QIcon("icon.ico"), app)
    tray_menu = QMenu()
    show_action = QAction("Show", tray_icon)
    exit_action = QAction("Exit", tray_icon)
    tray_menu.addAction(show_action)
    tray_menu.addAction(exit_action)
    tray_icon.setContextMenu(tray_menu)
    show_action.triggered.connect(lambda: main_window.show_main_window())
    exit_action.triggered.connect(app.quit)
    tray_icon.show()
    app.tray_icon = tray_icon
    app.setStyleSheet("""
        QPushButton { border: 1px solid #555; border-radius: 5px; padding: 5px; }
        QPushButton:hover { background-color: #777; }
        QLineEdit, QTextEdit { background-color: #333; color: white; border: 1px solid #555; }
        QListWidget { background-color: #333; color: white; }
        QLabel { color: white; }
    """)
    global main_window
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
