from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox
from PyQt5.QtCore import Qt

class SettingsWidget(QWidget):
    def __init__(self, theme_change_callback, current_theme="dark"):
        super().__init__()
        self.theme_change_callback = theme_change_callback
        self.current_theme = current_theme
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout(self)
        lbl = QLabel("Settings")
        self.chk_dark_mode = QCheckBox("Enable Dark Mode")
        self.chk_dark_mode.setChecked(self.current_theme == "dark")
        layout.addWidget(lbl)
        layout.addWidget(self.chk_dark_mode)
        layout.addStretch()
        self.chk_dark_mode.stateChanged.connect(self.on_theme_toggled)
    def on_theme_toggled(self, state):
        self.current_theme = "dark" if state == Qt.Checked else "light"
        self.theme_change_callback(self.current_theme)
