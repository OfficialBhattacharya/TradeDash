import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QMessageBox, QDateEdit, QScrollArea, QFrame,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox, QSplitter,
    QDoubleSpinBox, QFormLayout, QGroupBox, QStackedWidget
)
from PyQt5.QtCore import QDate, Qt, pyqtSlot
from PyQt5.QtWidgets import QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import ta
from tradedash.core.data_service import YahooFinanceService
from tradedash.config.settings import (
    COLORS, 
    CHART_DPI, 
    CHART_WIDTH, 
    CHART_HEIGHT,
    DEFAULT_LOOKBACK_DAYS
)
from PyQt5.QtGui import QColor

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=CHART_WIDTH, height=CHART_HEIGHT, dpi=CHART_DPI):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor(COLORS['chart_bg'])
        self.axes = self.fig.add_subplot(111)
        self.axes_volume = self.axes.twinx()  # Create a twin axis for volume
        
        # Set dark theme with better visibility
        self.axes.set_facecolor(COLORS['chart_bg'])
        self.axes_volume.set_facecolor(COLORS['chart_bg'])
        
        # Style the grid for better visibility
        self.axes.grid(True, linestyle='--', alpha=0.4, color=COLORS['chart_grid'])
        
        # Style the spines for better visibility
        for spine in self.axes.spines.values():
            spine.set_color(COLORS['border'])
            spine.set_linewidth(1.0)
        for spine in self.axes_volume.spines.values():
            spine.set_color(COLORS['border'])
            spine.set_linewidth(1.0)
        
        # Style the labels with more visible text
        self.axes.tick_params(colors=COLORS['text_bright'], which='both', labelsize=10)
        self.axes_volume.tick_params(colors=COLORS['text_dim'], which='both', labelsize=10)
        self.axes.xaxis.label.set_color(COLORS['text_bright'])
        self.axes.yaxis.label.set_color(COLORS['text_bright'])
        
        self.fig.tight_layout(pad=3.0)
        
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)
        
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

class StrategyControlFrame(QFrame):
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
            QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {{
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
            QGroupBox {{
                color: {COLORS['text_bright']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                margin-top: 1ex;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # Stock Input
        stock_layout = QHBoxLayout()
        stock_label = QLabel("Stock Symbol:")
        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText("Enter symbol (e.g., SBIN.NS)")
        stock_layout.addWidget(stock_label)
        stock_layout.addWidget(self.stock_input)
        self.layout.addLayout(stock_layout)
        
        # Time Period
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
        
        # Strategy Selector
        strategy_layout = QHBoxLayout()
        strategy_label = QLabel("Strategy:")
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["SMA Crossover", "RSI", "MACD", "Bollinger Bands"])
        self.strategy_combo.currentIndexChanged.connect(self.show_strategy_parameters)
        strategy_layout.addWidget(strategy_label)
        strategy_layout.addWidget(self.strategy_combo)
        self.layout.addLayout(strategy_layout)
        
        # Strategy Parameters
        self.params_layout = QVBoxLayout()
        self.layout.addLayout(self.params_layout)
        
        # Initial parameters (SMA Crossover)
        self.show_strategy_parameters(0)
        
        # Analyze Button
        self.analyze_button = QPushButton("Analyze Strategy")
        self.layout.addWidget(self.analyze_button)
    
    def show_strategy_parameters(self, index):
        # Clear existing parameters
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add new parameters based on selected strategy
        if index == 0:  # SMA Crossover
            param_layout = QHBoxLayout()
            param_layout.addWidget(QLabel("Fast SMA:"))
            self.fast_sma = QSpinBox()
            self.fast_sma.setRange(5, 50)
            self.fast_sma.setValue(10)
            param_layout.addWidget(self.fast_sma)
            
            param_layout.addWidget(QLabel("Slow SMA:"))
            self.slow_sma = QSpinBox()
            self.slow_sma.setRange(20, 200)
            self.slow_sma.setValue(30)
            param_layout.addWidget(self.slow_sma)
            
            self.params_layout.addLayout(param_layout)
            
        elif index == 1:  # RSI
            param_layout = QHBoxLayout()
            param_layout.addWidget(QLabel("Period:"))
            self.rsi_period = QSpinBox()
            self.rsi_period.setRange(5, 30)
            self.rsi_period.setValue(14)
            param_layout.addWidget(self.rsi_period)
            
            param_layout.addWidget(QLabel("Overbought:"))
            self.rsi_overbought = QSpinBox()
            self.rsi_overbought.setRange(60, 90)
            self.rsi_overbought.setValue(70)
            param_layout.addWidget(self.rsi_overbought)
            
            param_layout.addWidget(QLabel("Oversold:"))
            self.rsi_oversold = QSpinBox()
            self.rsi_oversold.setRange(10, 40)
            self.rsi_oversold.setValue(30)
            param_layout.addWidget(self.rsi_oversold)
            
            self.params_layout.addLayout(param_layout)
            
        elif index == 2:  # MACD
            param_layout = QHBoxLayout()
            param_layout.addWidget(QLabel("Fast Period:"))
            self.macd_fast = QSpinBox()
            self.macd_fast.setRange(5, 20)
            self.macd_fast.setValue(12)
            param_layout.addWidget(self.macd_fast)
            
            param_layout.addWidget(QLabel("Slow Period:"))
            self.macd_slow = QSpinBox()
            self.macd_slow.setRange(20, 40)
            self.macd_slow.setValue(26)
            param_layout.addWidget(self.macd_slow)
            
            param_layout.addWidget(QLabel("Signal Period:"))
            self.macd_signal = QSpinBox()
            self.macd_signal.setRange(5, 15)
            self.macd_signal.setValue(9)
            param_layout.addWidget(self.macd_signal)
            
            self.params_layout.addLayout(param_layout)
            
        elif index == 3:  # Bollinger Bands
            param_layout = QHBoxLayout()
            param_layout.addWidget(QLabel("Period:"))
            self.bb_period = QSpinBox()
            self.bb_period.setRange(5, 50)
            self.bb_period.setValue(20)
            param_layout.addWidget(self.bb_period)
            
            param_layout.addWidget(QLabel("Std Dev:"))
            self.bb_std = QSpinBox()
            self.bb_std.setRange(1, 4)
            self.bb_std.setValue(2)
            param_layout.addWidget(self.bb_std)
            
            self.params_layout.addLayout(param_layout)

class StrategyTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.yahoo_service = YahooFinanceService()
        self.setup_ui()
    
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Control panel and results area
        splitter = QSplitter(Qt.Vertical)
        
        # Control Panel
        self.control_frame = StrategyControlFrame()
        self.control_frame.analyze_button.clicked.connect(self.analyze_strategy)
        splitter.addWidget(self.control_frame)
        
        # Results area
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(0, 0, 0, 0)
        
        # Results table
        results_label = QLabel("Backtest Results")
        results_label.setStyleSheet(f"color: {COLORS['text_bright']}; font-weight: bold; font-size: 14px;")
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Metric", "Value", "Buy Signals", "Sell Signals"])
        
        # Set table style
        self.results_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['background_secondary']};
                color: {COLORS['text']};
                gridline-color: {COLORS['border']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['secondary']};
                color: {COLORS['text_bright']};
                padding: 5px;
                border: 1px solid {COLORS['border']};
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_bright']};
            }}
        """)
        
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setMinimumHeight(150)
        self.results_table.setMaximumHeight(200)
        
        results_layout.addWidget(results_label)
        results_layout.addWidget(self.results_table)
        
        # Chart
        chart_label = QLabel("Strategy Chart")
        chart_label.setStyleSheet(f"color: {COLORS['text_bright']}; font-weight: bold; font-size: 14px;")
        
        self.chart_canvas = MplCanvas(self)
        
        results_layout.addWidget(chart_label)
        results_layout.addWidget(self.chart_canvas)
        
        splitter.addWidget(results_widget)
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Set sizes for splitter
        splitter.setSizes([300, 700])
    
    def analyze_strategy(self):
        symbol = self.control_frame.stock_input.text().strip()
        if not symbol:
            QMessageBox.warning(self, "Input Error", "Please enter a stock symbol")
            return
        
        # Get date range
        from_date = self.control_frame.from_date.date().toPyDate()
        to_date = self.control_frame.to_date.date().toPyDate()
        
        # Show loading status in console
        print(f"Loading data for {symbol}...")
        
        try:
            # Fetch data
            print(f"Fetching data for {symbol} from {from_date} to {to_date}")
            data = self.yahoo_service.fetch_data(symbol, from_date, to_date)
            
            if data is None or data.empty:
                print(f"No data found for {symbol}")
                QMessageBox.warning(self, "Data Error", f"No data found for {symbol}. Please check the symbol and date range.")
                return
            
            print(f"Data shape: {data.shape}")
            print(f"Data columns: {data.columns.tolist()}")
            
            # Handle multi-index columns if present
            if isinstance(data.columns, pd.MultiIndex):
                print("Detected MultiIndex columns - flattening")
                # Convert multi-index columns to single level
                data.columns = data.columns.droplevel(1)
                print(f"Columns after flattening: {data.columns.tolist()}")
                
            # Check and standardize column names
            column_mapping = {}
            for col in data.columns:
                if isinstance(col, str):
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
                print(f"Standardizing column names: {column_mapping}")
                data = data.rename(columns=column_mapping)
                
            print(f"Final columns: {data.columns.tolist()}")
                
            # Ensure 'Close' column exists for indicators
            if 'Close' not in data.columns:
                close_col = None
                for col in data.columns:
                    if isinstance(col, str) and col.upper() == 'CLOSE':
                        close_col = col
                        break
                        
                if close_col is None:
                    print(f"Error: Cannot find Close price column in {data.columns.tolist()}")
                    QMessageBox.warning(self, "Data Error", "Close price data not available for analysis")
                    return
                
                # Rename the column for consistency
                data = data.rename(columns={close_col: 'Close'})
                
            # Ensure data is properly indexed
            if not isinstance(data.index, pd.DatetimeIndex):
                data.index = pd.DatetimeIndex(data.index)
                
            # Apply strategy
            strategy_index = self.control_frame.strategy_combo.currentIndex()
            
            try:
                # Add signals based on strategy
                if strategy_index == 0:  # SMA Crossover
                    fast_period = self.control_frame.fast_sma.value()
                    slow_period = self.control_frame.slow_sma.value()
                    
                    print(f"Calculating SMA Crossover strategy with fast={fast_period}, slow={slow_period}")
                    
                    # Calculate SMAs
                    data['SMA_Fast'] = data['Close'].rolling(window=fast_period).mean()
                    data['SMA_Slow'] = data['Close'].rolling(window=slow_period).mean()
                    
                    # Generate signals - make a copy to avoid SettingWithCopyWarning
                    data = data.copy()
                    data.loc[:, 'Signal'] = 0
                    data.loc[data['SMA_Fast'] > data['SMA_Slow'], 'Signal'] = 1
                    data.loc[data['SMA_Fast'] < data['SMA_Slow'], 'Signal'] = -1
                    
                    # Signal changes (buy/sell)
                    data['Position'] = data['Signal'].diff()
                    
                    strategy_name = f"SMA Crossover ({fast_period}/{slow_period})"
                    
                elif strategy_index == 1:  # RSI
                    period = self.control_frame.rsi_period.value()
                    overbought = self.control_frame.rsi_overbought.value()
                    oversold = self.control_frame.rsi_oversold.value()
                    
                    print(f"Calculating RSI strategy with period={period}, overbought={overbought}, oversold={oversold}")
                    
                    # Calculate RSI
                    try:
                        data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=period).rsi()
                    except Exception as e:
                        print(f"Error calculating RSI: {e}")
                        QMessageBox.warning(self, "Strategy Error", f"Failed to calculate RSI: {str(e)}")
                        return
                    
                    # Generate signals - make a copy to avoid SettingWithCopyWarning
                    data = data.copy()
                    data.loc[:, 'Signal'] = 0
                    data.loc[data['RSI'] < oversold, 'Signal'] = 1
                    data.loc[data['RSI'] > overbought, 'Signal'] = -1
                    
                    # Signal changes (buy/sell)
                    data['Position'] = data['Signal'].diff()
                    
                    strategy_name = f"RSI Strategy (Period: {period}, Overbought: {overbought}, Oversold: {oversold})"
                    
                elif strategy_index == 2:  # MACD
                    fast_period = self.control_frame.macd_fast.value()
                    slow_period = self.control_frame.macd_slow.value()
                    signal_period = self.control_frame.macd_signal.value()
                    
                    print(f"Calculating MACD strategy with fast={fast_period}, slow={slow_period}, signal={signal_period}")
                    
                    # Calculate MACD
                    try:
                        macd = ta.trend.MACD(
                            data['Close'], 
                            window_fast=fast_period, 
                            window_slow=slow_period, 
                            window_sign=signal_period
                        )
                        data['MACD'] = macd.macd()
                        data['MACD_Signal'] = macd.macd_signal()
                        data['MACD_Hist'] = macd.macd_diff()
                    except Exception as e:
                        print(f"Error calculating MACD: {e}")
                        QMessageBox.warning(self, "Strategy Error", f"Failed to calculate MACD: {str(e)}")
                        return
                    
                    # Generate signals - make a copy to avoid SettingWithCopyWarning
                    data = data.copy()
                    data.loc[:, 'Signal'] = 0
                    data.loc[data['MACD'] > data['MACD_Signal'], 'Signal'] = 1
                    data.loc[data['MACD'] < data['MACD_Signal'], 'Signal'] = -1
                    
                    # Signal changes (buy/sell)
                    data['Position'] = data['Signal'].diff()
                    
                    strategy_name = f"MACD Strategy ({fast_period}/{slow_period}/{signal_period})"
                    
                elif strategy_index == 3:  # Bollinger Bands
                    period = self.control_frame.bb_period.value()
                    std_dev = self.control_frame.bb_std.value()
                    
                    print(f"Calculating Bollinger Bands strategy with period={period}, std_dev={std_dev}")
                    
                    # Calculate Bollinger Bands
                    try:
                        bollinger = ta.volatility.BollingerBands(
                            data['Close'], 
                            window=period, 
                            window_dev=std_dev
                        )
                        data['BB_Upper'] = bollinger.bollinger_hband()
                        data['BB_Middle'] = bollinger.bollinger_mavg()
                        data['BB_Lower'] = bollinger.bollinger_lband()
                    except Exception as e:
                        print(f"Error calculating Bollinger Bands: {e}")
                        QMessageBox.warning(self, "Strategy Error", f"Failed to calculate Bollinger Bands: {str(e)}")
                        return
                    
                    # Generate signals - make a copy to avoid SettingWithCopyWarning
                    data = data.copy()
                    data.loc[:, 'Signal'] = 0
                    data.loc[data['Close'] < data['BB_Lower'], 'Signal'] = 1
                    data.loc[data['Close'] > data['BB_Upper'], 'Signal'] = -1
                    
                    # Signal changes (buy/sell)
                    data['Position'] = data['Signal'].diff()
                    
                    strategy_name = f"Bollinger Bands Strategy (Period: {period}, StdDev: {std_dev})"
            except Exception as e:
                print(f"Error applying strategy: {e}")
                QMessageBox.warning(self, "Strategy Error", f"Error calculating strategy: {str(e)}")
                return
            
            # Drop NaN values
            print(f"Data shape before dropping NaN values: {data.shape}")
            data = data.dropna()
            print(f"Data shape after dropping NaN values: {data.shape}")
            
            if data.empty:
                print("Not enough data after applying indicators")
                QMessageBox.warning(self, "Analysis Error", "Not enough data for analysis after applying indicators")
                return
                
            # Calculate backtest metrics
            buy_signals = len(data[data['Position'] > 0])
            sell_signals = len(data[data['Position'] < 0])
            total_trades = buy_signals + sell_signals
            
            # Add metrics to results table
            self.results_table.setRowCount(4)  # Increased to include win rate
            
            # Set metrics
            self.results_table.setItem(0, 0, QTableWidgetItem("Total Trades"))
            self.results_table.setItem(0, 1, QTableWidgetItem(str(total_trades)))
            self.results_table.setItem(0, 2, QTableWidgetItem(str(buy_signals)))
            self.results_table.setItem(0, 3, QTableWidgetItem(str(sell_signals)))
            
            # Add stock info
            stock_info = self.yahoo_service.get_stock_info(symbol)
            if stock_info is not None:
                self.results_table.setItem(1, 0, QTableWidgetItem("Stock Name"))
                self.results_table.setItem(1, 1, QTableWidgetItem(str(stock_info.get('name', symbol))))
                
                self.results_table.setItem(2, 0, QTableWidgetItem("Current Price"))
                current_price = stock_info.get('currentPrice', 'N/A')
                self.results_table.setItem(2, 1, QTableWidgetItem(str(current_price)))
                
                # Calculate win rate (simplified for demonstration)
                if total_trades > 0:
                    # Just a placeholder - in a real app, this would calculate actual P&L
                    buy_rate = round((buy_signals / total_trades) * 100, 2)
                    win_rate = f"{buy_rate}% Buy Rate"
                else:
                    win_rate = "N/A"
                    
                self.results_table.setItem(3, 0, QTableWidgetItem("Buy Rate"))
                self.results_table.setItem(3, 1, QTableWidgetItem(win_rate))
            
            # Plot results
            self.plot_results(data, strategy_index, strategy_name)
            
        except Exception as e:
            import traceback
            print(f"Error in strategy analysis: {e}")
            print(traceback.format_exc())
            QMessageBox.warning(self, "Analysis Error", f"Error analyzing strategy: {str(e)}")
    
    def plot_results(self, data, strategy_index, strategy_name):
        # Clear everything and create fresh figure
        self.chart_canvas.fig.clear()
        
        try:
            # Create a copy of data with date index for plotting
            plot_data = data.copy()
            
            # Ensure we're working with a datetime index
            if not isinstance(plot_data.index, pd.DatetimeIndex):
                plot_data.index = pd.to_datetime(plot_data.index)
            
            # Sort data by date to ensure proper plotting
            plot_data = plot_data.sort_index()
            
            print(f"Plot data shape: {plot_data.shape}")
            print(f"Plot data columns: {plot_data.columns.tolist()}")
            
            # If we have very few data points, increase line width for better visibility
            line_width = 2.0 if len(plot_data) < 100 else 1.5
            
            # Different figure setup based on strategy type
            if strategy_index == 0:  # SMA Crossover
                # Create single axis for price and SMAs
                ax_price = self.chart_canvas.fig.add_subplot(111)
                
                # Plot price and SMA lines
                ax_price.plot(plot_data.index, plot_data['Close'], label='Close Price', color=COLORS['chart_line'], linewidth=line_width)
                ax_price.plot(plot_data.index, plot_data['SMA_Fast'], label=f"SMA {self.control_frame.fast_sma.value()}", color=COLORS['accent'], linewidth=line_width)
                ax_price.plot(plot_data.index, plot_data['SMA_Slow'], label=f"SMA {self.control_frame.slow_sma.value()}", color=COLORS['accent_tertiary'], linewidth=line_width)
                
                # Buy/sell signals
                buy_signals = plot_data[plot_data['Position'] > 0]
                sell_signals = plot_data[plot_data['Position'] < 0]
                
                if not buy_signals.empty:
                    ax_price.scatter(buy_signals.index, buy_signals['Close'], marker='^', color=COLORS['success'], s=120, label='Buy', zorder=5)
                
                if not sell_signals.empty:
                    ax_price.scatter(sell_signals.index, sell_signals['Close'], marker='v', color=COLORS['error'], s=120, label='Sell', zorder=5)
                
                # Setup axis styling
                ax_price.set_facecolor(COLORS['chart_bg'])
                ax_price.grid(True, linestyle='--', alpha=0.4, color=COLORS['chart_grid'])
                ax_price.tick_params(colors=COLORS['text_bright'], which='both', labelsize=10)
                ax_price.set_title(strategy_name, color=COLORS['text_bright'], fontsize=14, fontweight='bold')
                ax_price.set_xlabel('Date', color=COLORS['text_bright'], fontsize=12)
                ax_price.set_ylabel('Price', color=COLORS['text_bright'], fontsize=12)
                
                for spine in ax_price.spines.values():
                    spine.set_color(COLORS['border'])
                    spine.set_linewidth(1.0)
                
                # Set up volume subplot at bottom if needed
                self._setup_volume_subplot(ax_price, plot_data)
                
                # Add legend
                lines, labels = ax_price.get_legend_handles_labels()
                ax_price.legend(lines, labels, 
                            loc='upper left', facecolor=COLORS['background_secondary'], 
                            edgecolor=COLORS['border'], framealpha=0.9, 
                            labelcolor=COLORS['text_bright'], fontsize=10)
                
            elif strategy_index == 1:  # RSI
                # Create subplot for price
                ax_price = self.chart_canvas.fig.add_subplot(211)  # Top 50%
                ax_rsi = self.chart_canvas.fig.add_subplot(212, sharex=ax_price)  # Bottom 50%
                
                # Plot price
                ax_price.plot(plot_data.index, plot_data['Close'], label='Close Price', color=COLORS['chart_line'], linewidth=line_width)
                
                # Plot RSI on separate axis
                ax_rsi.plot(plot_data.index, plot_data['RSI'], label='RSI', color=COLORS['accent_tertiary'], linewidth=line_width)
                ax_rsi.axhline(y=self.control_frame.rsi_overbought.value(), color=COLORS['error'], linestyle='--', alpha=0.7, linewidth=1.5)
                ax_rsi.axhline(y=self.control_frame.rsi_oversold.value(), color=COLORS['success'], linestyle='--', alpha=0.7, linewidth=1.5)
                ax_rsi.set_ylim(0, 100)
                
                # Add labels for overbought/oversold
                ax_rsi.text(plot_data.index[0], self.control_frame.rsi_overbought.value() + 2, 'Overbought', 
                         color=COLORS['text_bright'], fontsize=10)
                ax_rsi.text(plot_data.index[0], self.control_frame.rsi_oversold.value() - 5, 'Oversold', 
                         color=COLORS['text_bright'], fontsize=10)
                
                # Buy/sell signals on price chart
                buy_signals = plot_data[plot_data['Position'] > 0]
                sell_signals = plot_data[plot_data['Position'] < 0]
                
                if not buy_signals.empty:
                    ax_price.scatter(buy_signals.index, buy_signals['Close'], marker='^', color=COLORS['success'], s=120, label='Buy', zorder=5)
                
                if not sell_signals.empty:
                    ax_price.scatter(sell_signals.index, sell_signals['Close'], marker='v', color=COLORS['error'], s=120, label='Sell', zorder=5)
                
                # Setup styling for both axes
                for ax in [ax_price, ax_rsi]:
                    ax.set_facecolor(COLORS['chart_bg'])
                    ax.grid(True, linestyle='--', alpha=0.4, color=COLORS['chart_grid'])
                    ax.tick_params(colors=COLORS['text_bright'], which='both', labelsize=10)
                    for spine in ax.spines.values():
                        spine.set_color(COLORS['border'])
                        spine.set_linewidth(1.0)
                
                # Set labels
                ax_price.set_title(strategy_name, color=COLORS['text_bright'], fontsize=14, fontweight='bold')
                ax_price.set_ylabel('Price', color=COLORS['text_bright'], fontsize=12)
                ax_rsi.set_xlabel('Date', color=COLORS['text_bright'], fontsize=12)
                ax_rsi.set_ylabel('RSI', color=COLORS['text_bright'], fontsize=12)
                
                # Add legends to each subplot
                ax_price.legend(loc='upper left', facecolor=COLORS['background_secondary'], 
                            edgecolor=COLORS['border'], framealpha=0.9, 
                            labelcolor=COLORS['text_bright'], fontsize=10)
                
                ax_rsi.legend(loc='upper left', facecolor=COLORS['background_secondary'], 
                           edgecolor=COLORS['border'], framealpha=0.9, 
                           labelcolor=COLORS['text_bright'], fontsize=10)
                
            elif strategy_index == 2:  # MACD
                # Create subplot for price
                ax_price = self.chart_canvas.fig.add_subplot(211)  # Top 50%
                ax_macd = self.chart_canvas.fig.add_subplot(212, sharex=ax_price)  # Bottom 50%
                
                # Plot price
                ax_price.plot(plot_data.index, plot_data['Close'], label='Close Price', color=COLORS['chart_line'], linewidth=line_width)
                
                # Plot MACD
                ax_macd.plot(plot_data.index, plot_data['MACD'], label='MACD', color=COLORS['accent'], linewidth=line_width)
                ax_macd.plot(plot_data.index, plot_data['MACD_Signal'], label='Signal', color=COLORS['accent_tertiary'], linewidth=line_width)
                ax_macd.fill_between(plot_data.index, plot_data['MACD_Hist'], 0, where=(plot_data['MACD_Hist'] >= 0), color=COLORS['success'], alpha=0.5)
                ax_macd.fill_between(plot_data.index, plot_data['MACD_Hist'], 0, where=(plot_data['MACD_Hist'] < 0), color=COLORS['error'], alpha=0.5)
                
                # Buy/sell signals on price chart
                buy_signals = plot_data[plot_data['Position'] > 0]
                sell_signals = plot_data[plot_data['Position'] < 0]
                
                if not buy_signals.empty:
                    ax_price.scatter(buy_signals.index, buy_signals['Close'], marker='^', color=COLORS['success'], s=120, label='Buy', zorder=5)
                
                if not sell_signals.empty:
                    ax_price.scatter(sell_signals.index, sell_signals['Close'], marker='v', color=COLORS['error'], s=120, label='Sell', zorder=5)
                
                # Setup styling for both axes
                for ax in [ax_price, ax_macd]:
                    ax.set_facecolor(COLORS['chart_bg'])
                    ax.grid(True, linestyle='--', alpha=0.4, color=COLORS['chart_grid'])
                    ax.tick_params(colors=COLORS['text_bright'], which='both', labelsize=10)
                    for spine in ax.spines.values():
                        spine.set_color(COLORS['border'])
                        spine.set_linewidth(1.0)
                
                # Set labels
                ax_price.set_title(strategy_name, color=COLORS['text_bright'], fontsize=14, fontweight='bold')
                ax_price.set_ylabel('Price', color=COLORS['text_bright'], fontsize=12)
                ax_macd.set_xlabel('Date', color=COLORS['text_bright'], fontsize=12)
                ax_macd.set_ylabel('MACD', color=COLORS['text_bright'], fontsize=12)
                
                # Add legends to each subplot
                ax_price.legend(loc='upper left', facecolor=COLORS['background_secondary'], 
                            edgecolor=COLORS['border'], framealpha=0.9, 
                            labelcolor=COLORS['text_bright'], fontsize=10)
                
                ax_macd.legend(loc='upper left', facecolor=COLORS['background_secondary'], 
                           edgecolor=COLORS['border'], framealpha=0.9, 
                           labelcolor=COLORS['text_bright'], fontsize=10)
                
            elif strategy_index == 3:  # Bollinger Bands
                # Create single axis for price and Bollinger Bands
                ax_price = self.chart_canvas.fig.add_subplot(111)
                
                # Plot price and Bollinger Bands
                ax_price.plot(plot_data.index, plot_data['Close'], label='Close Price', color=COLORS['chart_line'], linewidth=line_width)
                ax_price.plot(plot_data.index, plot_data['BB_Upper'], label='Upper Band', color=COLORS['accent_tertiary'], linestyle='--', linewidth=line_width)
                ax_price.plot(plot_data.index, plot_data['BB_Middle'], label='Middle Band', color=COLORS['accent'], linestyle='-', linewidth=line_width)
                ax_price.plot(plot_data.index, plot_data['BB_Lower'], label='Lower Band', color=COLORS['accent_tertiary'], linestyle='--', linewidth=line_width)
                
                # Fill between bands for better visualization
                ax_price.fill_between(plot_data.index, plot_data['BB_Upper'], plot_data['BB_Lower'], 
                                   color=COLORS['accent'], alpha=0.1)
                
                # Buy/sell signals
                buy_signals = plot_data[plot_data['Position'] > 0]
                sell_signals = plot_data[plot_data['Position'] < 0]
                
                if not buy_signals.empty:
                    ax_price.scatter(buy_signals.index, buy_signals['Close'], marker='^', color=COLORS['success'], s=120, label='Buy', zorder=5)
                
                if not sell_signals.empty:
                    ax_price.scatter(sell_signals.index, sell_signals['Close'], marker='v', color=COLORS['error'], s=120, label='Sell', zorder=5)
                
                # Setup axis styling
                ax_price.set_facecolor(COLORS['chart_bg'])
                ax_price.grid(True, linestyle='--', alpha=0.4, color=COLORS['chart_grid'])
                ax_price.tick_params(colors=COLORS['text_bright'], which='both', labelsize=10)
                ax_price.set_title(strategy_name, color=COLORS['text_bright'], fontsize=14, fontweight='bold')
                ax_price.set_xlabel('Date', color=COLORS['text_bright'], fontsize=12)
                ax_price.set_ylabel('Price', color=COLORS['text_bright'], fontsize=12)
                
                for spine in ax_price.spines.values():
                    spine.set_color(COLORS['border'])
                    spine.set_linewidth(1.0)
                
                # Set up volume subplot at bottom if needed
                self._setup_volume_subplot(ax_price, plot_data)
                
                # Add legend
                lines, labels = ax_price.get_legend_handles_labels()
                ax_price.legend(lines, labels, 
                            loc='upper left', facecolor=COLORS['background_secondary'], 
                            edgecolor=COLORS['border'], framealpha=0.9, 
                            labelcolor=COLORS['text_bright'], fontsize=10)
            
            # Configure x-axis date formatting
            self._configure_dates(plot_data)
            
            # Adjust the layout to make better use of space
            self.chart_canvas.fig.tight_layout()
            self.chart_canvas.draw()
        except Exception as e:
            print(f"Error in plot_results: {e}")
            QMessageBox.warning(self, "Plot Error", f"Error plotting results: {str(e)}")
    
    def _setup_volume_subplot(self, ax_price, plot_data):
        """Helper method to set up volume subplot if needed"""
        # Check if Volume column exists and handle it safely
        has_volume = False
        volume_col = None
        
        # Find Volume column (case-insensitive)
        for col in plot_data.columns:
            if isinstance(col, str) and col.upper() == 'VOLUME':
                volume_col = col
                has_volume = True
                break
                
        # Plot volume if available
        if has_volume and not plot_data[volume_col].isnull().all():
            ax_volume = ax_price.twinx()
            
            # Calculate price changes for volume bar colors
            price_change = plot_data['Close'].pct_change()
            colors = [COLORS['chart_volume_up'] if change >= 0 else COLORS['chart_volume_down'] for change in price_change]
            
            # Plot volume bars with variable width based on number of points
            bar_width = 0.8  # Default width
            if len(plot_data) > 200:
                bar_width = 0.6
            elif len(plot_data) < 50:
                bar_width = 1.0
                
            # Normalize volume if the values are very large
            volume_data = plot_data[volume_col]
            if volume_data.max() > 1e6:
                volume_scale = 1e6
                volume_label = 'Volume (Million)'
            elif volume_data.max() > 1e3:
                volume_scale = 1e3
                volume_label = 'Volume (Thousand)'
            else:
                volume_scale = 1
                volume_label = 'Volume'
                
            ax_volume.bar(plot_data.index, plot_data[volume_col] / volume_scale, 
                          width=bar_width, color=colors, alpha=0.7, label=volume_label)
            ax_volume.set_ylabel(volume_label, color=COLORS['text_bright'], fontsize=12)
            ax_volume.tick_params(axis='y', colors=COLORS['text_bright'])
            ax_volume.spines['right'].set_position(('outward', 60))
            ax_volume.grid(False)
            
            # Style the spines for the volume axis
            for spine in ax_volume.spines.values():
                spine.set_color(COLORS['border'])
                spine.set_linewidth(1.0)
                
            return ax_volume
        return None
    
    def _configure_dates(self, plot_data):
        """Helper method to configure date formatting for all axes in the figure"""
        for ax in self.chart_canvas.fig.get_axes():
            if hasattr(ax, 'xaxis') and len(plot_data) > 0:
                date_range = (plot_data.index[-1] - plot_data.index[0]).days
                
                # Adjust date format based on the date range
                if date_range > 365:
                    date_format = '%Y-%m'  # Year-Month for long ranges
                elif date_range > 60:
                    date_format = '%b %d'  # Month-Day for medium ranges
                else:
                    date_format = '%m-%d'  # Month-Day for short ranges
                
                # Set number of ticks based on data size
                if len(plot_data) > 100:
                    ax.xaxis.set_major_locator(plt.MaxNLocator(10))
                else:
                    ax.xaxis.set_major_locator(plt.MaxNLocator(min(len(plot_data), 10)))
                    
                # Create the date formatter
                date_formatter = DateFormatter(date_format)
                ax.xaxis.set_major_formatter(date_formatter)
                
                # Improve x-axis labeling with more visible rotation
                ax.tick_params(axis='x', rotation=45, labelsize=10, colors=COLORS['text_bright'])
                
    def chart_title(self):
        return "Strategy Chart" 