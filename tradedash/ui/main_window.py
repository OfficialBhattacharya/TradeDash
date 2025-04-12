import sys
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from tradedash.config.settings import (
    COLORS, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE,
    BORDER_RADIUS, ELEMENT_PADDING, GRADIENT_BACKGROUND
)
from tradedash.ui.widgets.stock_tab import StockTab
from tradedash.ui.widgets.chart_tab import ChartTab
from tradedash.ui.widgets.recommendation_tab import RecommendationTab
from tradedash.ui.widgets.strategy_tab import StrategyTab
from tradedash.ui.widgets.pnl_simulation_tab import PnLSimulationTab
from tradedash.ui.widgets.similar_stocks_tab import SimilarStocksTab
from tradedash.ui.widgets.market_scanner_tab import MarketScannerTab

class Ui_MainWindow:
    """
    Main window UI setup for the trading dashboard application.
    """
    def setup_ui(self, main_window):
        # Set window properties
        main_window.setObjectName("MainWindow")
        main_window.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        main_window.setWindowTitle(WINDOW_TITLE)
        main_window.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
            }}
            QTabWidget {{
                background-color: {COLORS['background']};
            }}
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                background-color: {COLORS['background']};
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background-color: {COLORS['background_secondary']};
                color: {COLORS['text']};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_bright']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {COLORS['hover']};
            }}
        """)
        
        # Get central widget and set its style
        self.central_widget = main_window.centralWidget()
        self.central_widget.setStyleSheet(f"background-color: {COLORS['background']};")
        
        # Create layout for central widget
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("tabWidget")
        self.tab_widget.setDocumentMode(True)
        
        # Create tabs
        self.stock_tab = StockTab()
        self.chart_tab = ChartTab()
        self.recommendation_tab = RecommendationTab()
        self.strategy_tab = StrategyTab()
        self.pnl_simulation_tab = PnLSimulationTab()
        self.similar_stocks_tab = SimilarStocksTab()
        self.market_scanner_tab = MarketScannerTab()
        
        # Add tabs to the widget
        self.tab_widget.addTab(self.stock_tab, "Stocks")
        self.tab_widget.addTab(self.chart_tab, "Charts")
        self.tab_widget.addTab(self.recommendation_tab, "Recommendations")
        self.tab_widget.addTab(self.strategy_tab, "Strategy")
        self.tab_widget.addTab(self.pnl_simulation_tab, "P&L Simulation")
        self.tab_widget.addTab(self.similar_stocks_tab, "Similar Stocks")
        self.tab_widget.addTab(self.market_scanner_tab, "Market Scanner")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
