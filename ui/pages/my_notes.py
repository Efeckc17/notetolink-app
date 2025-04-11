import uuid
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QListWidgetItem, QInputDialog, QMessageBox
from PyQt5.QtCore import Qt, QEvent

from core.data import load_data_sync, save_data_sync
from ui.widgets import CategoryListWidget, NoteListWidget

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
                            save_data_sync(d)
                        except Exception:
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
                    it = QListWidgetItem(n["title"] + " - " + n["timestamp"])
                    it.setData(Qt.UserRole, n["id"])
                    self.note_list.addItem(it)
            elif cid is None:
                if n["category_id"] is None:
                    it = QListWidgetItem(n["title"] + " - " + n["timestamp"])
                    it.setData(Qt.UserRole, n["id"])
                    self.note_list.addItem(it)
            else:
                if n["category_id"] == cid:
                    it = QListWidgetItem(n["title"] + " - " + n["timestamp"])
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
                save_data_sync(d)
            except Exception:
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
                save_data_sync(d)
            except Exception:
                pass
            self.refresh_data()

    def delete_category(self):
        sel = self.cat_list.currentItem()
        if not sel:
            return
        cid = sel.data(Qt.UserRole)
        if cid in ("favorites", None):
            return
        res = QMessageBox.question(self, "Delete Category", "Delete this category?", QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            d = load_data_sync()
            d["categories"] = [c for c in d["categories"] if c["id"] != cid]
            for n in d["notes"]:
                if n["category_id"] == cid:
                    n["category_id"] = None
            try:
                save_data_sync(d)
            except Exception:
                pass
            self.refresh_data()
