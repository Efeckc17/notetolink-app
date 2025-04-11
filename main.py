import sys
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from ui.mainwindow import MainWindow
from ui.pages.quick_note import QuickNoteDialog

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
