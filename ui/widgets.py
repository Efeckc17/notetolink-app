import os
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QIcon, QPixmap

class NoteListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setDragDropMode(QListWidget.DragDrop)
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
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setDragDropMode(QListWidget.DragDrop)
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
