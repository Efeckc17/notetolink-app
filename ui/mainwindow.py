from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtGui import QIcon
from ui.pages.new_note import NewNoteWidget
from ui.pages.my_notes import MyNotesWidget
from ui.pages.settings import SettingsWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NoteToLink Desktop")
        self.setWindowIcon(QIcon("icon.ico"))
        self.resize(1200, 700)
        self.setWindowOpacity(0.95)
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
        from ui.pages.note_detail import NoteDetailWidget
        from ui.pages.edit_note import EditNoteWidget
        detail = NoteDetailWidget(note, back_callback=lambda: self.stack.setCurrentWidget(self.my_notes_page), edit_callback=self.open_edit_note)
        if self.stack.count() > 3:
            w = self.stack.widget(3)
            self.stack.removeWidget(w)
            w.deleteLater()
        self.stack.addWidget(detail)
        self.stack.setCurrentWidget(detail)
    def open_edit_note(self, note):
        from ui.pages.edit_note import EditNoteWidget
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
