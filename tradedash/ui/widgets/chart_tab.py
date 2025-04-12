import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QMessageBox, QDateEdit, QScrollArea, QFrame, QComboBox, QSplitter
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from tradedash.core.data_service import fetch_stock_data, get_stock_info, YahooFinanceService
from tradedash.config.settings import (
    COLORS, 
    CHART_DPI, 
    CHART_WIDTH, 
    CHART_HEIGHT,
    DEFAULT_LOOKBACK_DAYS,
    BORDER_RADIUS,
    GRADIENT_BACKGROUND,
    ELEMENT_PADDING,
    BUTTON_PADDING
)
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import mplfinance as mpf
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Qt5Agg')

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=CHART_WIDTH, height=CHART_HEIGHT, dpi=CHART_DPI):
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor=COLORS['chart_bg'])
        self.axes = fig.add_subplot(111)
        self.axes_volume = self.axes.twinx()  # Create a twin axis for volume
        
        # Set dark theme
        self.axes.set_facecolor(COLORS['chart_bg'])
        self.axes_volume.set_facecolor(COLORS['chart_bg'])
        fig.patch.set_facecolor(COLORS['chart_bg'])
        
        # Style the grid
        self.axes.grid(True, linestyle='--', alpha=0.2, color=COLORS['chart_grid'])
        
        # Style the spines
        for spine in self.axes.spines.values():
            spine.set_color(COLORS['border'])
        for spine in self.axes_volume.spines.values():
            spine.set_color(COLORS['border'])
        
        # Style the labels
        self.axes.tick_params(colors=COLORS['text'], which='both', labelsize=10)
        self.axes_volume.tick_params(colors=COLORS['text_dim'], which='both', labelsize=10)
        
        fig.tight_layout(pad=3.0)
        
        super().__init__(fig)
        self.setParent(parent)
        
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

class ControlFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("controlFrame")
        self.setStyleSheet(f"""
            QFrame#controlFrame {{
                background-color: {COLORS['background_secondary']};
                border-radius: 8px;
                padding: 10px;
            }}
            QLabel {{
                color: {COLORS['text_bright']};
                font-weight: bold;
            }}
            QLineEdit, QComboBox, QDateEdit {{
                background-color: {COLORS['secondary']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 5px;
                selection-background-color: {COLORS['primary']};
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_bright']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['hover']};
            }}
        """)
        
        # Setup layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # Symbol input row
        symbol_layout = QHBoxLayout()
        symbol_label = QLabel("Stock Symbol:")
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Enter symbol (e.g., SBIN.NS)")
        symbol_layout.addWidget(symbol_label)
        symbol_layout.addWidget(self.symbol_input, 1)
        self.layout.addLayout(symbol_layout)
        
        # Time period row
        time_layout = QHBoxLayout()
        
        from_label = QLabel("From:")
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-365))
        self.from_date.setCalendarPopup(True)
        
        to_label = QLabel("To:")
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        
        time_layout.addWidget(from_label)
        time_layout.addWidget(self.from_date)
        time_layout.addWidget(to_label)
        time_layout.addWidget(self.to_date)
        self.layout.addLayout(time_layout)
        
        # Chart type row
        chart_type_layout = QHBoxLayout()
        chart_type_label = QLabel("Chart Type:")
        self.chart_type = QComboBox()
        self.chart_type.addItems(["Candlestick", "OHLC", "Line"])
        
        interval_label = QLabel("Interval:")
        self.interval = QComboBox()
        self.interval.addItems(["1d", "1wk", "1mo"])
        
        chart_type_layout.addWidget(chart_type_label)
        chart_type_layout.addWidget(self.chart_type)
        chart_type_layout.addWidget(interval_label)
        chart_type_layout.addWidget(self.interval)
        self.layout.addLayout(chart_type_layout)
        
        # Load button
        self.load_button = QPushButton("Load Chart")
        self.layout.addWidget(self.load_button)

class ChartTab(QWidget):
    def __init__(self):
        super().__init__()
        self.service = YahooFinanceService()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Create splitter for control panel and chart
        splitter = QSplitter(Qt.Vertical)
        
        # Control panel
        self.control_frame = ControlFrame()
        self.control_frame.load_button.clicked.connect(self.load_chart)
        splitter.addWidget(self.control_frame)
        
        # Chart container
        chart_container = QFrame()
        chart_container.setObjectName("chartContainer")
        chart_container.setStyleSheet(f"""
            #chartContainer {{
                background-color: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS};
                padding: 10px;
            }}
        """)
        
        chart_layout = QVBoxLayout()
        chart_layout.setContentsMargins(10, 10, 10, 10)
        chart_layout.setSpacing(5)
        
        # Chart title
        self.chart_title = QLabel("CHART VIEW")
        self.chart_title.setObjectName("chartTitle")
        self.chart_title.setStyleSheet(f"""
            #chartTitle {{
                color: {COLORS['accent']};
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 5px;
            }}
        """)
        chart_layout.addWidget(self.chart_title)
        
        # Chart area
        self.figure = Figure(figsize=(CHART_WIDTH, CHART_HEIGHT), dpi=CHART_DPI)
        self.figure.patch.set_facecolor(COLORS['chart_bg'])
        
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {COLORS['secondary']};
                border: none;
                spacing: 8px;
                padding: 8px;
                border-radius: 4px;
            }}
            QToolButton {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px;
            }}
            QToolButton:hover {{
                background-color: {COLORS['hover']};
                border: 1px solid {COLORS['accent']};
            }}
            QToolButton:pressed {{
                background-color: {COLORS['primary']};
            }}
        """)
        
        chart_layout.addWidget(self.toolbar)
        chart_layout.addWidget(self.canvas)
        
        chart_container.setLayout(chart_layout)
        splitter.addWidget(chart_container)
        
        # Add splitter to main layout
        layout.addWidget(splitter)
        
        # Set sizes for the splitter (control panel smaller than chart)
        splitter.setSizes([200, 800])
        
        self.setLayout(layout)
    
    def load_chart(self):
        symbol = self.control_frame.symbol_input.text().strip()
        if not symbol:
            QMessageBox.warning(self, "Input Error", "Please enter a stock symbol")
            return
            
        try:
            self.chart_title.setText(f"LOADING CHART FOR {symbol.upper()}...")
            
            # Get period and convert to days
            period = self.control_frame.interval.currentText()
            days = {
                "1d": 1, "1wk": 7, "1mo": 30
            }[period]
            
            # Fetch data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # Get one year of data
            print(f"Fetching data for {symbol} from {start_date} to {end_date}")
            df = self.service.fetch_data(symbol, start_date, end_date)
            
            print(f"Dataframe empty: {df is None or df.empty}")
            if df is not None and not df.empty:
                print(f"Dataframe shape: {df.shape}")
                print(f"Dataframe columns: {df.columns.tolist()}")
                print(f"Dataframe first row: {df.iloc[0]}")
                
                # Handle multi-index columns if present
                if isinstance(df.columns, pd.MultiIndex):
                    print("Detected MultiIndex columns - flattening")
                    # Convert multi-index columns to single level
                    df.columns = df.columns.droplevel(1)
                    print(f"Columns after flattening: {df.columns.tolist()}")
                
            if df is None or df.empty:
                QMessageBox.warning(self, "Data Error", f"No data available for {symbol}")
                return
                
            # Update chart title with company name
            info = self.service.get_stock_info(symbol)
            company_name = info.get('name', symbol.upper())
            self.chart_title.setText(f"{company_name} ({symbol.upper()}) - {period} CHART")
            
            # Clear the figure
            self.figure.clear()
            
            # Create plot
            ax = self.figure.add_subplot(111)
            volume_ax = ax.twinx()
            
            # Set dark theme for the axes
            ax.set_facecolor(COLORS['chart_bg'])
            volume_ax.set_facecolor(COLORS['chart_bg'])
            
            # Style the grid
            ax.grid(True, linestyle='--', alpha=0.3, color=COLORS['chart_grid'])
            
            # Style the spines
            for spine in ax.spines.values():
                spine.set_color(COLORS['border'])
            for spine in volume_ax.spines.values():
                spine.set_color(COLORS['border'])
            
            # Style the labels
            ax.tick_params(colors=COLORS['text_bright'], which='both', labelsize=10)
            volume_ax.tick_params(colors=COLORS['text_bright'], which='both', labelsize=10)
            
            # Rotate x-axis labels
            for label in ax.get_xticklabels():
                label.set_rotation(45)
                label.set_ha('right')
            
            # Plot based on chart type
            chart_type = self.control_frame.chart_type.currentText()
            
            if chart_type == "Candlestick" or chart_type == "OHLC":
                # Check if dataframe has required columns for mpf
                required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                
                # If columns are named differently, rename them to expected names
                column_mapping = {}
                for required_col in required_columns:
                    for col in df.columns:
                        if isinstance(col, str) and col.upper() == required_col.upper() and col != required_col:
                            column_mapping[col] = required_col
                
                if column_mapping:
                    print(f"Renaming columns: {column_mapping}")
                    df = df.rename(columns=column_mapping)
                
                # Check if all required columns exist after renaming
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    error_msg = f"Missing required columns for OHLC chart: {', '.join(missing_columns)}"
                    print(error_msg)
                    QMessageBox.warning(self, "Chart Error", error_msg)
                    return
                
                # Use mplfinance for candlestick/OHLC chart
                self.figure.clear()
                chart_style = 'candle' if chart_type == "Candlestick" else 'ohlc'
                
                try:
                    # Create a separate figure for mpf and then transfer it to our canvas
                    mpf_fig, mpf_axes = mpf.plot(
                        df,
                        type=chart_style,
                        style='charles',
                        title=f'{company_name} ({symbol.upper()}) - {period}',
                        ylabel='Price',
                        ylabel_lower='Volume',
                        volume=True,
                        figsize=(CHART_WIDTH, CHART_HEIGHT),
                        panel_ratios=(4, 1),
                        tight_layout=True,
                        datetime_format='%Y-%m-%d',
                        xrotation=45,
                        returnfig=True,
                        warn_too_much_data=100000,
                        mav=(20, 50, 100),
                        mavcolors=(COLORS['accent'], COLORS['accent_tertiary'], COLORS['warning'])
                    )
                    
                    # Copy the MPF figure to our canvas
                    self.figure = mpf_fig
                    self.canvas.figure = mpf_fig
                except Exception as e:
                    print(f"Error creating {chart_type} chart: {e}")
                    QMessageBox.warning(self, "Chart Error", f"Error creating {chart_type} chart: {str(e)}")
                    return
            else:  # Line chart
                # Check if 'Close' and 'Volume' columns exist
                close_col = None
                volume_col = None
                
                # Find Close column (case-insensitive)
                for col in df.columns:
                    if isinstance(col, str) and col.upper() == 'CLOSE':
                        close_col = col
                        break
                
                # Find Volume column (case-insensitive)
                for col in df.columns:
                    if isinstance(col, str) and col.upper() == 'VOLUME':
                        volume_col = col
                        break
                
                if close_col is None:
                    print(f"Error: 'Close' column not found in {df.columns.tolist()}")
                    QMessageBox.warning(self, "Chart Error", "Close price data not available")
                    return
                
                # Line chart for Close prices
                ax.plot(df.index, df[close_col], color=COLORS['chart_line'], linewidth=2, label='Close Price')
                
                # Add moving averages
                ax.plot(df.index, df[close_col].rolling(window=20).mean(), color=COLORS['accent'], 
                        linewidth=1.5, alpha=0.8, label='20 Day MA')
                ax.plot(df.index, df[close_col].rolling(window=50).mean(), color=COLORS['accent_tertiary'], 
                        linewidth=1.5, alpha=0.8, label='50 Day MA')
                ax.plot(df.index, df[close_col].rolling(window=100).mean(), color=COLORS['warning'], 
                        linewidth=1.5, alpha=0.8, label='100 Day MA')
                
                # Volume bars (if available)
                if volume_col:
                    volume_ax.bar(df.index, df[volume_col], color=COLORS['chart_volume'], alpha=0.5, width=0.8, label='Volume')
                    volume_ax.set_ylabel('Volume', color=COLORS['text_dim'])
                else:
                    print("Volume data not available")
                    # Hide volume axis if no volume data
                    volume_ax.set_visible(False)
                
                # Labels and legend
                ax.set_ylabel('Price', color=COLORS['text_bright'])
                if volume_col:
                    volume_ax.set_ylabel('Volume', color=COLORS['text_dim'])
                ax.legend(loc='upper left', facecolor=COLORS['secondary'], edgecolor=COLORS['border'], 
                         framealpha=0.8, labelcolor=COLORS['text_bright'])
                
                # Set title
                ax.set_title(f'{company_name} ({symbol.upper()}) - {period}', color=COLORS['text_bright'])
                
                # Format dates on x-axis
                ax.tick_params(axis='x', rotation=45)
                
                # Adjust the figure layout
                self.figure.tight_layout()
            
            # Refresh the canvas
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error updating chart: {e}")
            QMessageBox.warning(self, "Chart Error", f"Failed to update chart: {str(e)}")
            self.chart_title.setText("CHART VIEW - ERROR LOADING DATA")
