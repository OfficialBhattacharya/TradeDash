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
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

from tradedash.core.data_service import YahooFinanceService
from tradedash.config.settings import (
    COLORS, 
    CHART_DPI, 
    CHART_WIDTH, 
    CHART_HEIGHT,
    DEFAULT_LOOKBACK_DAYS
)

class PnLControlFrame(QFrame):
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
        self.stock_input.setPlaceholderText("Enter symbol (e.g., AAPL)")
        stock_layout.addWidget(stock_label)
        stock_layout.addWidget(self.stock_input)
        self.layout.addLayout(stock_layout)
        
        # Time Period
        time_layout = QHBoxLayout()
        from_label = QLabel("From:")
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-DEFAULT_LOOKBACK_DAYS))
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
        self.strategy_combo.addItems(["Buy and Hold", "Moving Average", "Mean Reversion", "Momentum"])
        self.strategy_combo.currentIndexChanged.connect(self.show_strategy_parameters)
        strategy_layout.addWidget(strategy_label)
        strategy_layout.addWidget(self.strategy_combo)
        self.layout.addLayout(strategy_layout)
        
        # Strategy Parameters
        self.params_layout = QVBoxLayout()
        self.layout.addLayout(self.params_layout)
        
        # Initial parameters (Buy and Hold)
        self.show_strategy_parameters(0)
        
        # Initial investment amount
        investment_layout = QHBoxLayout()
        investment_label = QLabel("Initial Investment ($):")
        self.investment_amount = QSpinBox()
        self.investment_amount.setRange(1000, 1000000)
        self.investment_amount.setSingleStep(1000)
        self.investment_amount.setValue(10000)
        investment_layout.addWidget(investment_label)
        investment_layout.addWidget(self.investment_amount)
        self.layout.addLayout(investment_layout)
        
        # Simulate Button
        self.simulate_button = QPushButton("Simulate P&L")
        self.layout.addWidget(self.simulate_button)
    
    def show_strategy_parameters(self, index):
        # Clear existing parameters
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add new parameters based on selected strategy
        if index == 0:  # Buy and Hold
            # No parameters needed
            pass
            
        elif index == 1:  # Moving Average
            param_layout = QHBoxLayout()
            param_layout.addWidget(QLabel("Fast MA (days):"))
            self.fast_ma = QSpinBox()
            self.fast_ma.setRange(5, 50)
            self.fast_ma.setValue(10)
            param_layout.addWidget(self.fast_ma)
            
            param_layout.addWidget(QLabel("Slow MA (days):"))
            self.slow_ma = QSpinBox()
            self.slow_ma.setRange(20, 200)
            self.slow_ma.setValue(30)
            param_layout.addWidget(self.slow_ma)
            
            self.params_layout.addLayout(param_layout)
            
        elif index == 2:  # Mean Reversion
            param_layout = QHBoxLayout()
            param_layout.addWidget(QLabel("Lookback (days):"))
            self.lookback = QSpinBox()
            self.lookback.setRange(5, 100)
            self.lookback.setValue(20)
            param_layout.addWidget(self.lookback)
            
            param_layout.addWidget(QLabel("Z-Score Threshold:"))
            self.z_score = QDoubleSpinBox()
            self.z_score.setRange(0.5, 3.0)
            self.z_score.setSingleStep(0.1)
            self.z_score.setValue(1.5)
            param_layout.addWidget(self.z_score)
            
            self.params_layout.addLayout(param_layout)
            
        elif index == 3:  # Momentum
            param_layout = QHBoxLayout()
            param_layout.addWidget(QLabel("Momentum Period (days):"))
            self.momentum_period = QSpinBox()
            self.momentum_period.setRange(5, 250)
            self.momentum_period.setValue(90)
            param_layout.addWidget(self.momentum_period)
            
            param_layout.addWidget(QLabel("Holding Period (days):"))
            self.holding_period = QSpinBox()
            self.holding_period.setRange(5, 100)
            self.holding_period.setValue(30)
            param_layout.addWidget(self.holding_period)
            
            self.params_layout.addLayout(param_layout)

class PnLSimulationTab(QWidget):
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
        self.control_frame = PnLControlFrame()
        self.control_frame.simulate_button.clicked.connect(self.simulate_pnl)
        splitter.addWidget(self.control_frame)
        
        # Results area
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(0, 0, 0, 0)
        
        # Results table
        results_label = QLabel("P&L Simulation Results")
        results_label.setStyleSheet(f"color: {COLORS['text_bright']}; font-weight: bold; font-size: 14px;")
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "Metric", "Value", "Holding Period", "Max Drawdown", "Sharpe Ratio"
        ])
        
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
        chart_label = QLabel("P&L Chart")
        chart_label.setStyleSheet(f"color: {COLORS['text_bright']}; font-weight: bold; font-size: 14px;")
        
        self.chart_canvas = FigureCanvas(Figure(figsize=(CHART_WIDTH, CHART_HEIGHT), dpi=CHART_DPI))
        self.chart_fig = self.chart_canvas.figure
        self.chart_fig.patch.set_facecolor(COLORS['chart_bg'])
        
        results_layout.addWidget(chart_label)
        results_layout.addWidget(self.chart_canvas)
        
        splitter.addWidget(results_widget)
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Set sizes for splitter
        splitter.setSizes([300, 700])
    
    def simulate_pnl(self):
        symbol = self.control_frame.stock_input.text().strip()
        if not symbol:
            QMessageBox.warning(self, "Input Error", "Please enter a stock symbol")
            return
        
        # Get date range
        from_date = self.control_frame.from_date.date().toPyDate()
        to_date = self.control_frame.to_date.date().toPyDate()
        initial_investment = self.control_frame.investment_amount.value()
        
        try:
            # Fetch data
            data = self.yahoo_service.fetch_data(symbol, from_date, to_date)
            
            if data is None or data.empty:
                QMessageBox.warning(self, "Data Error", f"No data found for {symbol}. Please check the symbol and date range.")
                return
                
            # Ensure data is properly formatted
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)
                
            # Standardize column names
            col_mapping = {}
            for col in data.columns:
                if col.upper() == 'OPEN':
                    col_mapping[col] = 'Open'
                elif col.upper() == 'HIGH':
                    col_mapping[col] = 'High'
                elif col.upper() == 'LOW':
                    col_mapping[col] = 'Low'
                elif col.upper() == 'CLOSE':
                    col_mapping[col] = 'Close'
                elif col.upper() == 'VOLUME':
                    col_mapping[col] = 'Volume'
            
            if col_mapping:
                data = data.rename(columns=col_mapping)
                
            # Apply strategy and calculate P&L
            strategy_index = self.control_frame.strategy_combo.currentIndex()
            results = self._apply_strategy(data, strategy_index, initial_investment)
            
            # Update results table
            self._update_results_table(results, symbol)
            
            # Plot P&L chart
            self._plot_pnl_chart(results, symbol, strategy_index)
            
        except Exception as e:
            import traceback
            print(f"Error in P&L simulation: {e}")
            print(traceback.format_exc())
            QMessageBox.warning(self, "Simulation Error", f"Error simulating P&L: {str(e)}")
    
    def _apply_strategy(self, data, strategy_index, initial_investment):
        # Create a copy of data for simulation
        df = data.copy()
        
        # Common P&L and metrics calculation helper function
        def calculate_metrics(df, positions, initial_investment):
            # Calculate portfolio value over time
            df['Position'] = positions
            df['PrevPosition'] = df['Position'].shift(1).fillna(0)
            df['PositionChange'] = df['Position'] - df['PrevPosition']
            
            # Shares bought/sold at each step
            df['Price'] = df['Close']
            df['Cash'] = initial_investment
            
            # Initialize portfolio and cash
            portfolio_value = initial_investment
            cash = initial_investment
            shares = 0
            
            # Track daily portfolio value
            portfolio_values = []
            cash_values = []
            share_values = []
            
            for i in range(len(df)):
                # Process position changes
                if i > 0:
                    pos_change = df.iloc[i]['PositionChange']
                    price = df.iloc[i]['Price']
                    
                    if pos_change > 0:  # Buy
                        # Buy with available cash
                        new_shares = min(cash // price, pos_change)
                        cash -= new_shares * price
                        shares += new_shares
                    elif pos_change < 0:  # Sell
                        # Sell shares we own
                        sell_shares = min(shares, abs(pos_change))
                        cash += sell_shares * price
                        shares -= sell_shares
                
                # Calculate portfolio value
                share_value = shares * df.iloc[i]['Price']
                portfolio_value = cash + share_value
                
                portfolio_values.append(portfolio_value)
                cash_values.append(cash)
                share_values.append(share_value)
            
            # Store values in dataframe
            df['PortfolioValue'] = portfolio_values
            df['Cash'] = cash_values
            df['ShareValue'] = share_values
            
            # Calculate returns
            df['Returns'] = df['PortfolioValue'].pct_change().fillna(0)
            
            # Calculate P&L metrics
            total_return = (df['PortfolioValue'].iloc[-1] / initial_investment) - 1
            annualized_return = (1 + total_return) ** (252 / len(df)) - 1
            
            # Calculate drawdown
            df['CumMaxValue'] = df['PortfolioValue'].cummax()
            df['Drawdown'] = (df['PortfolioValue'] - df['CumMaxValue']) / df['CumMaxValue']
            max_drawdown = df['Drawdown'].min()
            
            # Calculate Sharpe ratio (simplified)
            risk_free_rate = 0.02 / 252  # Assume 2% annual risk-free rate
            excess_returns = df['Returns'] - risk_free_rate
            sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
            
            # Determine optimal holding period
            holding_periods = [10, 20, 30, 60, 90, 180]
            period_returns = {}
            
            for period in holding_periods:
                if len(df) > period:
                    # Calculate returns for each possible holding period start
                    period_return = []
                    for i in range(0, len(df) - period):
                        start_value = df['Close'].iloc[i]
                        end_value = df['Close'].iloc[i + period]
                        ret = (end_value / start_value) - 1
                        period_return.append(ret)
                    
                    period_returns[period] = np.mean(period_return)
            
            optimal_holding_period = max(period_returns.items(), key=lambda x: x[1])[0] if period_returns else 30
            
            return {
                'df': df,
                'total_return': total_return,
                'annualized_return': annualized_return,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'optimal_holding_period': optimal_holding_period,
                'final_value': df['PortfolioValue'].iloc[-1],
                'buy_and_hold_return': (df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1
            }
        
        # Apply the selected strategy
        if strategy_index == 0:  # Buy and Hold
            # Full allocation to stock at start
            positions = pd.Series(1, index=df.index)
            
            return calculate_metrics(df, positions, initial_investment)
            
        elif strategy_index == 1:  # Moving Average
            # Get parameters
            fast_period = self._get_strategy_param('fast_ma', 10)
            slow_period = self._get_strategy_param('slow_ma', 30)
            
            # Calculate moving averages
            df['FastMA'] = df['Close'].rolling(window=fast_period).mean()
            df['SlowMA'] = df['Close'].rolling(window=slow_period).mean()
            
            # Generate signals: 1 when fast > slow (bullish), 0 when fast < slow (bearish)
            positions = pd.Series(0, index=df.index)
            positions[df['FastMA'] > df['SlowMA']] = 1
            
            return calculate_metrics(df, positions, initial_investment)
            
        elif strategy_index == 2:  # Mean Reversion
            # Get parameters
            lookback = self._get_strategy_param('lookback', 20)
            z_threshold = self._get_strategy_param('z_score', 1.5)
            
            # Calculate z-score
            df['Mean'] = df['Close'].rolling(window=lookback).mean()
            df['Std'] = df['Close'].rolling(window=lookback).std()
            df['ZScore'] = (df['Close'] - df['Mean']) / df['Std']
            
            # Generate signals: 1 when oversold (buy), 0 when overbought (sell)
            positions = pd.Series(0, index=df.index)
            positions[df['ZScore'] < -z_threshold] = 1  # Buy when oversold
            positions[df['ZScore'] > z_threshold] = 0   # Sell when overbought
            
            return calculate_metrics(df, positions, initial_investment)
            
        elif strategy_index == 3:  # Momentum
            # Get parameters
            momentum_period = self._get_strategy_param('momentum_period', 90)
            holding_period = self._get_strategy_param('holding_period', 30)
            
            # Calculate momentum (returns over lookback period)
            df['Momentum'] = df['Close'].pct_change(periods=momentum_period)
            
            # Generate signals: buy when momentum positive, hold for holding_period
            positions = pd.Series(0, index=df.index)
            
            for i in range(len(df)):
                if i > momentum_period:
                    if df['Momentum'].iloc[i] > 0:
                        end_idx = min(i + holding_period, len(df) - 1)
                        positions.iloc[i:end_idx] = 1
            
            return calculate_metrics(df, positions, initial_investment)
    
    def _update_results_table(self, results, symbol):
        self.results_table.setRowCount(6)
        
        # Format percentages
        total_return_pct = f"{results['total_return'] * 100:.2f}%"
        annual_return_pct = f"{results['annualized_return'] * 100:.2f}%"
        max_drawdown_pct = f"{results['max_drawdown'] * 100:.2f}%"
        
        # Set stock info row
        self.results_table.setItem(0, 0, QTableWidgetItem("Stock"))
        self.results_table.setItem(0, 1, QTableWidgetItem(symbol))
        stock_info = self.yahoo_service.get_stock_info(symbol)
        if stock_info:
            self.results_table.setItem(0, 2, QTableWidgetItem(stock_info.get('name', '')))
        
        # Set P&L metrics
        self.results_table.setItem(1, 0, QTableWidgetItem("Total Return"))
        self.results_table.setItem(1, 1, QTableWidgetItem(total_return_pct))
        
        self.results_table.setItem(2, 0, QTableWidgetItem("Annualized Return"))
        self.results_table.setItem(2, 1, QTableWidgetItem(annual_return_pct))
        
        self.results_table.setItem(3, 0, QTableWidgetItem("Final Value"))
        self.results_table.setItem(3, 1, QTableWidgetItem(f"${results['final_value']:.2f}"))
        
        self.results_table.setItem(4, 0, QTableWidgetItem("Max Drawdown"))
        self.results_table.setItem(4, 1, QTableWidgetItem(max_drawdown_pct))
        self.results_table.setItem(4, 3, QTableWidgetItem(max_drawdown_pct))
        
        self.results_table.setItem(5, 0, QTableWidgetItem("Optimal Holding"))
        self.results_table.setItem(5, 1, QTableWidgetItem(f"{results['optimal_holding_period']} days"))
        self.results_table.setItem(5, 2, QTableWidgetItem(f"{results['optimal_holding_period']} days"))
        
        # Set Sharpe ratio
        self.results_table.setItem(3, 3, QTableWidgetItem(f"{results['sharpe_ratio']:.2f}"))
        self.results_table.setItem(3, 4, QTableWidgetItem(f"{results['sharpe_ratio']:.2f}"))
        
        # Highlight cells based on performance
        for row in range(1, 4):
            item = self.results_table.item(row, 1)
            if item:
                value_text = item.text()
                if '-' in value_text:  # Negative return
                    item.setBackground(QColor(COLORS['error']))
                    item.setForeground(QColor(COLORS['text_bright']))
                else:  # Positive return
                    item.setBackground(QColor(COLORS['success']))
                    item.setForeground(QColor(COLORS['text_bright']))
    
    def _plot_pnl_chart(self, results, symbol, strategy_index):
        # Clear the figure
        self.chart_fig.clear()
        
        # Create plot
        ax1 = self.chart_fig.add_subplot(211)  # Portfolio value
        ax2 = self.chart_fig.add_subplot(212, sharex=ax1)  # Drawdown
        
        df = results['df']
        
        # Plot portfolio value
        ax1.plot(df.index, df['PortfolioValue'], label='Portfolio Value', color=COLORS['success'], linewidth=2)
        
        # Calculate buy and hold value for comparison
        initial_investment = self.control_frame.investment_amount.value()
        shares_bh = initial_investment / df['Close'].iloc[0]
        buy_hold_value = shares_bh * df['Close']
        
        ax1.plot(df.index, buy_hold_value, label='Buy & Hold', color=COLORS['accent_tertiary'], linestyle='--', linewidth=1.5)
        
        # Plot drawdown
        ax2.fill_between(df.index, 0, df['Drawdown'] * 100, color=COLORS['error'], alpha=0.3, label='Drawdown %')
        ax2.plot(df.index, df['Drawdown'] * 100, color=COLORS['error'], linewidth=1)
        
        # Add strategy specific elements
        strategy_names = {
            0: "Buy and Hold",
            1: f"Moving Average ({self._get_strategy_param('fast_ma', 10)}/{self._get_strategy_param('slow_ma', 30)})",
            2: f"Mean Reversion (Z-Score: {self._get_strategy_param('z_score', 1.5)})",
            3: f"Momentum ({self._get_strategy_param('momentum_period', 90)} days)"
        }
        
        # Styling
        for ax in [ax1, ax2]:
            ax.set_facecolor(COLORS['chart_bg'])
            ax.grid(True, linestyle='--', alpha=0.3, color=COLORS['chart_grid'])
            # Style the tick labels
            ax.tick_params(colors=COLORS['text_bright'], which='both', labelsize=9)
            # Style the spines
            for spine in ax.spines.values():
                spine.set_color(COLORS['border'])
                spine.set_linewidth(1.0)
        
        # Set titles and labels
        ax1.set_title(f"{symbol} - {strategy_names[strategy_index]} P&L Simulation", 
                     color=COLORS['text_bright'], fontsize=12, fontweight='bold')
        ax1.set_ylabel('Portfolio Value ($)', color=COLORS['text_bright'], fontsize=10)
        ax2.set_ylabel('Drawdown (%)', color=COLORS['text_bright'], fontsize=10)
        ax2.set_xlabel('Date', color=COLORS['text_bright'], fontsize=10)
        
        # Set y-axis for drawdown to be positive percentages from top to bottom
        ax2.set_ylim(df['Drawdown'].min() * 100 * 1.1, 0)
        
        # Add a horizontal line at 0% drawdown
        ax2.axhline(y=0, color=COLORS['border'], linestyle='-', linewidth=0.5)
        
        # Format dates on x-axis
        date_format = DateFormatter('%Y-%m-%d')
        ax2.xaxis.set_major_formatter(date_format)
        
        # Add legends
        ax1.legend(loc='upper left', frameon=True, 
                  facecolor=COLORS['background_secondary'], 
                  edgecolor=COLORS['border'], 
                  labelcolor=COLORS['text_bright'])
        
        ax2.legend(loc='lower left', frameon=True, 
                  facecolor=COLORS['background_secondary'], 
                  edgecolor=COLORS['border'], 
                  labelcolor=COLORS['text_bright'])
        
        # Rotate date labels
        plt.setp(ax2.get_xticklabels(), rotation=30, ha='right')
        
        # Adjust layout
        self.chart_fig.tight_layout()
        self.chart_canvas.draw()
    
    def _get_strategy_param(self, param_name, default_value):
        """Safely get a strategy parameter, returning a default if not yet initialized."""
        try:
            attr = getattr(self.control_frame, param_name)
            return attr.value()
        except (AttributeError, Exception):
            return default_value 