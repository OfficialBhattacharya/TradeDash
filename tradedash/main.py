"""Main application entry point for TradeDash"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtCore import Qt

from tradedash.ui.main_window import Ui_MainWindow
from tradedash.config.settings import WINDOW_TITLE

class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        # Setup window properties
        self.setWindowTitle(WINDOW_TITLE)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Set up the UI
        self.ui = Ui_MainWindow()
        self.ui.setup_ui(self)

def run():
    """Initialize and run the application"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for better cross-platform appearance
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    run()
