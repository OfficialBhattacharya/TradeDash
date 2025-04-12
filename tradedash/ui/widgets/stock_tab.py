import sys
import datetime
import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QMessageBox, QDateEdit, QTableWidget, 
    QTableWidgetItem, QFrame, QHeaderView
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor, QBrush
from tradedash.core.data_service import fetch_stock_data, get_stock_info, YahooFinanceService
from tradedash.config.settings import COLORS, DEFAULT_LOOKBACK_DAYS, BORDER_RADIUS, GRADIENT_BACKGROUND, ELEMENT_PADDING, BUTTON_PADDING

class ControlFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("controlFrame")
        self.setStyleSheet(f"""
            #controlFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                             stop:0 {COLORS['background_secondary']}, 
                             stop:1 {COLORS['secondary']});
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS};
                padding: {ELEMENT_PADDING};
            }}
            QLabel {{
                color: {COLORS['text_bright']};
                font-size: 14px;
                font-weight: bold;
            }}
            QLineEdit, QDateEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text_bright']};
                border: 1px solid {COLORS['accent']};
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
                min-width: 150px;
                selection-background-color: {COLORS['accent']};
            }}
            QLineEdit:focus, QDateEdit:focus {{
                border: 1px solid {COLORS['accent_tertiary']};
                background-color: {COLORS['secondary']};
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_dim']};
            }}
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                             stop:0 {COLORS['primary']}, 
                             stop:1 {COLORS['accent_secondary']});
                color: {COLORS['text_bright']};
                border: none;
                border-radius: 4px;
                padding: {BUTTON_PADDING};
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                             stop:0 {COLORS['accent_secondary']}, 
                             stop:1 {COLORS['primary']});
            }}
            QPushButton:pressed {{
                background: {COLORS['accent']};
            }}
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Stock symbol input
        symbol_label = QLabel("STOCK SYMBOL")
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Enter symbol (e.g., SBIN.NS)")
        
        # Date range inputs
        start_label = QLabel("START DATE")
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        
        end_label = QLabel("END DATE")
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        
        # Fetch button
        self.fetch_button = QPushButton("FETCH DATA")
        
        # Add widgets to layout
        for widget in [symbol_label, self.symbol_input, start_label, self.start_date, 
                      end_label, self.end_date, self.fetch_button]:
            layout.addWidget(widget)
        
        layout.addStretch()
        self.setLayout(layout)

class InfoCard(QFrame):
    def __init__(self, title, value="-", parent=None):
        super().__init__(parent)
        self.setObjectName("infoCard")
        self.setStyleSheet(f"""
            #infoCard {{
                background-color: {COLORS['secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS};
                padding: {ELEMENT_PADDING};
            }}
            QLabel#titleLabel {{
                color: {COLORS['text_dim']};
                font-size: 12px;
                font-weight: bold;
            }}
            QLabel#valueLabel {{
                color: {COLORS['text_bright']};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        self.title_label = QLabel(title)
        self.title_label.setObjectName("titleLabel")
        
        self.value_label = QLabel(value)
        self.value_label.setObjectName("valueLabel")
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        self.setLayout(layout)
    
    def update_value(self, value):
        self.value_label.setText(value)

class StockTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = YahooFinanceService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Control panel
        self.control_frame = ControlFrame()
        self.control_frame.fetch_button.clicked.connect(self.fetch_data)
        layout.addWidget(self.control_frame)
        
        # Stock info cards
        info_layout = QHBoxLayout()
        info_layout.setSpacing(15)
        
        self.company_card = InfoCard("COMPANY")
        self.sector_card = InfoCard("SECTOR")
        self.market_cap_card = InfoCard("MARKET CAP")
        
        info_layout.addWidget(self.company_card)
        info_layout.addWidget(self.sector_card)
        info_layout.addWidget(self.market_cap_card)
        
        info_container = QWidget()
        info_container.setLayout(info_layout)
        layout.addWidget(info_container)
        
        # Data table
        table_container = QFrame()
        table_container.setObjectName("tableContainer")
        table_container.setStyleSheet(f"""
            #tableContainer {{
                background-color: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS};
                padding: 2px;
            }}
        """)
        
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(10, 10, 10, 10)
        
        table_title = QLabel("PRICE DATA")
        table_title.setObjectName("tableTitle")
        table_title.setStyleSheet(f"""
            #tableTitle {{
                color: {COLORS['accent']};
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 5px;
            }}
        """)
        table_layout.addWidget(table_title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "DATE", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"
        ])
        
        # Set column widths proportionally
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Open
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # High
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Low
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Close
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Volume
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                border: none;
                gridline-color: {COLORS['border']};
                selection-background-color: {COLORS['accent_secondary']};
                selection-color: {COLORS['text_bright']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['secondary']};
                color: {COLORS['accent']};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['accent_secondary']}80;
            }}
        """)
        
        table_layout.addWidget(self.table)
        table_container.setLayout(table_layout)
        layout.addWidget(table_container)
        
        self.setLayout(layout)

    def fetch_data(self):
        symbol = self.control_frame.symbol_input.text().strip()
        if not symbol:
            return
            
        try:
            # Get date range
            start_date = self.control_frame.start_date.date().toPyDate()
            end_date = self.control_frame.end_date.date().toPyDate()
            
            print(f"Fetching data for {symbol} from {start_date} to {end_date}")
            
            # Fetch stock data
            df = self.service.fetch_data(symbol, start_date, end_date)
            print(f"Dataframe empty: {df.empty}")
            print(f"Dataframe shape: {df.shape if not df.empty else 'Empty'}")
            
            if not df.empty:
                print(f"Dataframe columns: {df.columns.tolist()}")
                print(f"Dataframe first row: {df.iloc[0]}")
                
                # Handle multi-index columns if present
                if isinstance(df.columns, pd.MultiIndex):
                    print("Detected MultiIndex columns - flattening")
                    # Convert multi-index columns to single level
                    df.columns = df.columns.droplevel(1)
                
                # Ensure we can access the expected columns, regardless of case
                # Yahoo Finance typically uses 'Open', 'High', 'Low', 'Close', 'Volume'
                column_mapping = {}
                for col in df.columns:
                    if isinstance(col, str):  # Only process string column names
                        if col.upper() == 'OPEN':
                            column_mapping[col] = 'Open'
                        elif col.upper() == 'HIGH':
                            column_mapping[col] = 'High'
                        elif col.upper() == 'LOW':
                            column_mapping[col] = 'Low'
                        elif col.upper() == 'CLOSE':
                            column_mapping[col] = 'Close'
                        elif col.upper() == 'VOLUME':
                            column_mapping[col] = 'Volume'
                
                if column_mapping:
                    df = df.rename(columns=column_mapping)
                
                print(f"Columns after mapping: {df.columns.tolist()}")
                
                # Check that all required columns exist
                required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    error_msg = f"Missing required columns: {', '.join(missing_columns)}"
                    print(error_msg)
                    QMessageBox.warning(self, "Data Error", error_msg)
                    return
            
            if df.empty:
                print("No data returned from service")
                QMessageBox.warning(self, "No Data", f"No data available for {symbol}")
                return
                
            # Update stock info
            info = self.service.get_stock_info(symbol)
            self.company_card.update_value(info.get('name', '-'))
            self.sector_card.update_value(info.get('sector', '-'))
            market_cap = info.get('market_cap', 0)
            market_cap_str = f"₹{market_cap/1e9:.2f}B" if market_cap > 1e9 else f"₹{market_cap/1e6:.2f}M"
            self.market_cap_card.update_value(market_cap_str)
            
            # Update table
            self.table.setRowCount(len(df))
            
            # Create pens for positive/negative values
            increase_brush = QBrush(QColor(COLORS['success']))
            decrease_brush = QBrush(QColor(COLORS['error']))
            neutral_brush = QBrush(QColor(COLORS['text']))
            
            for i, (index, row) in enumerate(df.iterrows()):
                try:
                    # Date
                    date_item = QTableWidgetItem(index.strftime('%Y-%m-%d'))
                    date_item.setTextAlignment(Qt.AlignCenter)
                    date_item.setForeground(neutral_brush)
                    self.table.setItem(i, 0, date_item)
                    
                    # Determine if price increased or decreased
                    price_change = row['Close'] - row['Open']
                    
                    # OHLCV data
                    for j, value in enumerate([
                        row['Open'], row['High'], row['Low'], 
                        row['Close'], row['Volume']
                    ]):
                        try:
                            if j < 4:  # OHLC values
                                display_value = f"{value:.2f}"
                            else:  # Volume values
                                display_value = f"{int(value):,}"
                                
                            item = QTableWidgetItem(display_value)
                            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                            
                            # Apply colors based on price direction (green for up, red for down)
                            if j == 3:  # Close price
                                if price_change > 0:
                                    item.setForeground(increase_brush)
                                elif price_change < 0:
                                    item.setForeground(decrease_brush)
                                else:
                                    item.setForeground(neutral_brush)
                            else:
                                item.setForeground(neutral_brush)
                            
                            self.table.setItem(i, j + 1, item)
                        except Exception as e:
                            print(f"Error with column {j}: {e}")
                except Exception as e:
                    print(f"Error processing row {i}: {e}")
                    
        except Exception as e:
            print(f"Error fetching data: {e}")
            QMessageBox.warning(self, "Error", f"Could not fetch data for {symbol}: {str(e)}")
