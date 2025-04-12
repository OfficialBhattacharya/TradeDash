import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QMessageBox, QDateEdit, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor, QBrush
import yfinance as yf
import ta
from tradedash.core.data_service import fetch_stock_data, get_stock_info, YahooFinanceService
from tradedash.config.settings import DEFAULT_LOOKBACK_DAYS, COLORS
from datetime import datetime, timedelta

class StockAnalyzer:
    def __init__(self):
        self.service = YahooFinanceService()
        
    def analyze_stock(self, symbol, start_date=None, end_date=None):
        """Analyze a single stock and return technical indicators."""
        try:
            # Ensure dates are properly set if they are None
            if start_date is None:
                start_date = datetime.now() - timedelta(days=DEFAULT_LOOKBACK_DAYS)
                print(f"Setting default start_date to {start_date}")
                
            if end_date is None:
                end_date = datetime.now()
                print(f"Setting default end_date to {end_date}")
                
            print(f"Analyzing stock: {symbol} from {start_date} to {end_date}")
            df = self.service.fetch_data(symbol, start_date, end_date)
            if df is None or df.empty:
                print(f"No data available for {symbol}")
                return None
            
            print(f"Data shape: {df.shape}")
            print(f"Data columns: {df.columns.tolist()}")
            
            # Handle multi-index columns if present
            if isinstance(df.columns, pd.MultiIndex):
                print("Detected MultiIndex columns - flattening")
                # Convert multi-index columns to single level
                df.columns = df.columns.droplevel(1)
                print(f"Columns after flattening: {df.columns.tolist()}")
                
            # Check and standardize column names
            column_mapping = {}
            for col in df.columns:
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
                df = df.rename(columns=column_mapping)
                
            print(f"Final columns: {df.columns.tolist()}")
                
            # Ensure 'Close' column exists
            if 'Close' not in df.columns:
                print(f"Error: Cannot find Close price column in {df.columns.tolist()}")
                return None
                
            # Ensure the dataframe is properly structured
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.DatetimeIndex(df.index)
                
            # Calculate technical indicators
            try:
                print("Calculating technical indicators...")
                df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
                macd = ta.trend.MACD(df['Close'])
                df['MACD'] = macd.macd()
                df['MACD_Signal'] = macd.macd_signal()
                df['SMA_20'] = ta.trend.SMAIndicator(df['Close'], window=20).sma_indicator()
                df['SMA_50'] = ta.trend.SMAIndicator(df['Close'], window=50).sma_indicator()
                df['SMA_200'] = ta.trend.SMAIndicator(df['Close'], window=200).sma_indicator()
            except Exception as e:
                print(f"Error calculating indicators: {e}")
                return None
            
            # Drop NaN values
            print(f"Data shape before dropping NaN values: {df.shape}")
            df = df.dropna()
            print(f"Data shape after dropping NaN values: {df.shape}")
            
            if df.empty:
                print(f"Not enough data for {symbol} to calculate indicators")
                return None
                
            # Get latest values
            latest = df.iloc[-1]
            
            return {
                'RSI': float(latest['RSI']),
                'MACD': float(latest['MACD']),
                'MACD_Signal': float(latest['MACD_Signal']),
                'SMA_20': float(latest['SMA_20']),
                'SMA_50': float(latest['SMA_50']),
                'SMA_200': float(latest['SMA_200']),
                'Close': float(latest['Close'])
            }
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None
    
    def get_recommendations(self, start_date=None, end_date=None):
        """Get recommendations for multiple stocks."""
        # Ensure dates are properly set
        if start_date is None:
            start_date = datetime.now() - timedelta(days=DEFAULT_LOOKBACK_DAYS)
            print(f"Setting default start_date for recommendations to {start_date}")
            
        if end_date is None:
            end_date = datetime.now()
            print(f"Setting default end_date for recommendations to {end_date}")
            
        # Default to analyzing major Indian stocks
        symbols = ['SBIN.NS', 'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS']
        recommendations = []
        
        print(f"Getting recommendations for {len(symbols)} stocks...")
        
        for symbol in symbols:
            print(f"Processing {symbol}...")
            analysis = self.analyze_stock(symbol, start_date, end_date)
            if analysis:
                score = self._calculate_score(analysis)
                info = self.service.get_stock_info(symbol)
                
                stock_name = info.get('name', symbol)
                recommendation = self._get_recommendation(score)
                
                print(f"Recommendation for {symbol} ({stock_name}): {recommendation} (Score: {score})")
                
                recommendations.append({
                    'symbol': symbol,
                    'name': stock_name,
                    'recommendation': recommendation,
                    'score': score
                })
        
        if not recommendations:
            print("No recommendations could be generated")
            return []
            
        print(f"Generated {len(recommendations)} recommendations")
        return sorted(recommendations, key=lambda x: x['score'], reverse=True)
    
    def _calculate_score(self, analysis):
        """Calculate a recommendation score based on technical indicators."""
        score = 0
        
        # RSI
        rsi = analysis['RSI']
        if rsi < 30:  # Oversold
            score += 2
        elif rsi < 40:
            score += 1
        elif rsi > 70:  # Overbought
            score -= 2
        elif rsi > 60:
            score -= 1
            
        # MACD
        if analysis['MACD'] > analysis['MACD_Signal']:
            score += 1
        else:
            score -= 1
            
        # Moving Averages
        close = analysis['Close']
        if close > analysis['SMA_20']:
            score += 1
        if close > analysis['SMA_50']:
            score += 1
        if close > analysis['SMA_200']:
            score += 2
            
        return score
    
    def _get_recommendation(self, score):
        """Convert score to recommendation."""
        if score >= 4:
            return "Strong Buy"
        elif score >= 2:
            return "Buy"
        elif score <= -4:
            return "Strong Sell"
        elif score <= -2:
            return "Sell"
        else:
            return "Hold"

class ControlFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background_secondary']};
                border-radius: 8px;
                padding: 16px;
            }}
            QLabel {{
                color: {COLORS['text_bright']};
                font-size: 14px;
                font-weight: bold;
            }}
            QLineEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text_bright']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_bright']};
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['hover']};
            }}
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Stock symbol input
        symbol_label = QLabel("Stock Symbol:")
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Enter stock symbol (e.g., SBIN.NS)")
        self.symbol_input.setFixedWidth(200)
        
        # Analyze button
        self.analyze_button = QPushButton("Analyze")
        
        layout.addWidget(symbol_label)
        layout.addWidget(self.symbol_input)
        layout.addWidget(self.analyze_button)
        layout.addStretch()
        
        self.setLayout(layout)

class RecommendationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.analyzer = StockAnalyzer()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Control panel
        self.control_frame = ControlFrame()
        self.control_frame.analyze_button.clicked.connect(self.analyze_stock)
        layout.addWidget(self.control_frame)
        
        # Add title for results
        results_title = QLabel("Technical Analysis Results")
        results_title.setStyleSheet(f"""
            color: {COLORS['text_bright']}; 
            font-size: 16px; 
            font-weight: bold;
            margin-top: 10px;
        """)
        layout.addWidget(results_title)
        
        # Results table with improved styling
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Indicator", "Value", "Signal", "Strength"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['background_secondary']};
                color: {COLORS['text_bright']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                gridline-color: {COLORS['border']};
                selection-background-color: {COLORS['primary']};
                selection-color: {COLORS['text_bright']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['secondary']};
                color: {COLORS['text_bright']};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['primary']}80;
            }}
        """)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def analyze_stock(self):
        symbol = self.control_frame.symbol_input.text().strip()
        if not symbol:
            QMessageBox.warning(self, "Input Error", "Please enter a stock symbol")
            return
            
        try:
            # Show analyzing message
            results_title = self.findChild(QLabel, "results_title")
            if results_title:
                results_title.setText(f"Analyzing {symbol.upper()}...")
            
            print(f"User requested analysis for stock: {symbol}")
            
            # Get analysis results
            analysis = self.analyzer.analyze_stock(symbol)
            if not analysis:
                print(f"No analysis data returned for {symbol}")
                QMessageBox.warning(self, "Data Error", f"No data available for {symbol}")
                if results_title:
                    results_title.setText("Technical Analysis Results - No Data Available")
                return
                
            print(f"Analysis completed successfully for {symbol}")
            print(f"Analysis data: {analysis}")
            
            # Update table with results
            results = []
            
            # RSI
            rsi = analysis['RSI']
            signal = "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral"
            strength = "Strong" if rsi < 20 or rsi > 80 else "Moderate"
            rsi_formatted = f"{rsi:.2f}"
            results.append(["RSI (14)", rsi_formatted, signal, strength])
            
            # MACD
            macd = analysis['MACD']
            macd_signal = analysis['MACD_Signal']
            signal = "Buy" if macd > macd_signal else "Sell"
            strength = "Strong" if abs(macd - macd_signal) > 0.5 else "Moderate"
            macd_formatted = f"{macd:.2f}"
            results.append(["MACD", macd_formatted, signal, strength])
            
            # Moving Averages
            close = float(analysis['Close'])
            sma_signals = []
            if close > analysis['SMA_20']:
                sma_signals.append(1)
            else:
                sma_signals.append(-1)
            if close > analysis['SMA_50']:
                sma_signals.append(1)
            else:
                sma_signals.append(-1)
            if close > analysis['SMA_200']:
                sma_signals.append(1)
            else:
                sma_signals.append(-1)
                
            signal_sum = sum(sma_signals)
            if signal_sum > 1:
                ma_signal = "Strong Buy"
                ma_strength = "Strong"
            elif signal_sum > 0:
                ma_signal = "Buy"
                ma_strength = "Moderate"
            elif signal_sum < -1:
                ma_signal = "Strong Sell"
                ma_strength = "Strong"
            elif signal_sum < 0:
                ma_signal = "Sell"
                ma_strength = "Moderate"
            else:
                ma_signal = "Neutral"
                ma_strength = "Weak"
                
            results.append(["Moving Averages", "-", ma_signal, ma_strength])
            
            # Add overall recommendation
            score = self.analyzer._calculate_score(analysis)
            recommendation = self.analyzer._get_recommendation(score)
            results.append(["Overall", f"Score: {score}", recommendation, ""])
            
            # Update table
            self.table.setRowCount(len(results))
            for i, row in enumerate(results):
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # Apply colors based on signal type for better visibility
                    if j == 2:  # Signal column
                        if "Buy" in value:
                            item.setForeground(QBrush(QColor(COLORS['success'])))
                            item.setFont(self.make_bold_font(item.font()))
                        elif "Sell" in value:
                            item.setForeground(QBrush(QColor(COLORS['error'])))
                            item.setFont(self.make_bold_font(item.font()))
                        elif "Overbought" in value:
                            item.setForeground(QBrush(QColor(COLORS['error'])))
                        elif "Oversold" in value:
                            item.setForeground(QBrush(QColor(COLORS['success'])))
                    
                    self.table.setItem(i, j, item)
            
            # Get stock info and show in title
            info = self.analyzer.service.get_stock_info(symbol)
            company_name = info.get('name', symbol.upper())
            if results_title:
                results_title.setText(f"Technical Analysis Results for {company_name} ({symbol.upper()})")
                    
        except Exception as e:
            print(f"Error analyzing stock: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Analysis Error", f"Error analyzing stock: {str(e)}")
            if results_title:
                results_title.setText("Technical Analysis Results - Error")
    
    def make_bold_font(self, font):
        font.setBold(True)
        return font 