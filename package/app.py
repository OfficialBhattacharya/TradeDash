import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow
from package.ui.mainwindow import Ui_MainWindow

# Add the package path to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class MainApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

def run():
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    return app.exec_()
