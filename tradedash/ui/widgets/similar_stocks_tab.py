import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QMessageBox, QDateEdit, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QProgressBar
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor, QBrush
import yfinance as yf
from datetime import datetime, timedelta
import requests
import json
from tradedash.core.data_service import YahooFinanceService
from tradedash.config.settings import DEFAULT_LOOKBACK_DAYS, COLORS

class SimilarityAnalyzer:
    """Analyzes stocks to find similar ones based on various metrics."""
    
    def __init__(self):
        self.service = YahooFinanceService()
        
    def find_similar_stocks(self, ticker, sector_match=True, days=120):
        """Finds similar stocks to the given ticker based on price movements and characteristics."""
        try:
            # Get stock info
            stock_info = self.service.get_stock_info(ticker)
            if not stock_info:
                return [], f"Could not find information for stock {ticker}"
                
            # Get sector and industry information
            sector = stock_info.get('sector', 'Unknown')
            
            # Get historical price data
            start_date = datetime.now() - timedelta(days=days)
            data = self.service.fetch_data(ticker, start_date, datetime.now())
            
            if data is None or data.empty:
                return [], f"No price data found for {ticker}"
            
            # Calculate returns for the target stock
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)
                
            close_col = None
            for col in data.columns:
                if isinstance(col, str) and col.upper() == 'CLOSE':
                    close_col = col
                    break
                    
            if close_col is None:
                return [], f"No close price data for {ticker}"
                
            # Calculate daily returns
            data['Return'] = data[close_col].pct_change()
            target_returns = data['Return'].dropna()
            
            # Get comparable stocks
            comparable_stocks = self._find_comparable_stocks(ticker, sector_match)
            
            if not comparable_stocks:
                return [], f"No comparable stocks found for {ticker}"
                
            # Analyze each comparable stock
            similarity_scores = []
            
            for comp_ticker in comparable_stocks:
                try:
                    # Skip if it's the same ticker
                    if comp_ticker == ticker:
                        continue
                        
                    comp_data = self.service.fetch_data(comp_ticker, start_date, datetime.now())
                    
                    if comp_data is None or comp_data.empty:
                        continue
                        
                    # Standardize column names
                    if isinstance(comp_data.columns, pd.MultiIndex):
                        comp_data.columns = comp_data.columns.droplevel(1)
                        
                    close_col = None
                    for col in comp_data.columns:
                        if isinstance(col, str) and col.upper() == 'CLOSE':
                            close_col = col
                            break
                            
                    if close_col is None:
                        continue
                        
                    # Calculate returns
                    comp_data['Return'] = comp_data[close_col].pct_change()
                    comp_returns = comp_data['Return'].dropna()
                    
                    # Calculate correlation but only if we have enough data
                    if len(comp_returns) < 30 or len(target_returns) < 30:
                        continue
                        
                    # Make sure indexes align for correlation calculation
                    common_index = target_returns.index.intersection(comp_returns.index)
                    if len(common_index) < 30:
                        continue
                        
                    # Calculate correlation coefficient
                    correlation = target_returns.loc[common_index].corr(comp_returns.loc[common_index])
                    
                    # Get stock info
                    comp_info = self.service.get_stock_info(comp_ticker)
                    
                    # Calculate similarity score (weighted combination of correlation and other factors)
                    similarity_score = self._calculate_similarity_score(correlation)
                    
                    # Get current price, 52-week change, and market cap
                    current_price = comp_info.get('currentPrice', 0)
                    market_cap = comp_info.get('market_cap', 0)
                    
                    # Get name
                    name = comp_info.get('name', comp_ticker)
                    
                    # Generate a rating score (0-5 stars)
                    rating = self._calculate_rating(correlation, comp_data)
                    
                    similarity_scores.append({
                        'symbol': comp_ticker,
                        'name': name,
                        'correlation': correlation,
                        'similarity_score': similarity_score,
                        'current_price': current_price,
                        'market_cap': market_cap,
                        'rating': rating
                    })
                except Exception as e:
                    print(f"Error analyzing {comp_ticker}: {str(e)}")
                    continue
            
            # Sort by similarity score
            similarity_scores = sorted(similarity_scores, key=lambda x: x['similarity_score'], reverse=True)
            
            # Return top 5 most similar stocks
            return similarity_scores[:5], None
        except Exception as e:
            return [], f"Error finding similar stocks: {str(e)}"

    def _find_comparable_stocks(self, ticker, sector_match=True):
        """Find comparable stocks to the given ticker."""
        try:
            # Get stock info
            stock_info = self.service.get_stock_info(ticker)
            if not stock_info:
                return []
                
            # Get sector
            sector = stock_info.get('sector', 'Unknown')
            
            # Some common stock lists by market
            if ticker.endswith('.NS'):  # Indian market
                all_stocks = ['SBIN.NS', 'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 
                             'ICICIBANK.NS', 'KOTAKBANK.NS', 'HINDUNILVR.NS', 'ITC.NS', 
                             'BHARTIARTL.NS', 'LT.NS', 'BAJFINANCE.NS', 'AXISBANK.NS',
                             'ASIANPAINT.NS', 'MARUTI.NS', 'TITAN.NS', 'SUNPHARMA.NS']
            else:  # Default to US market
                all_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'FB', 'TSLA', 'BRK-B', 'JNJ',
                             'JPM', 'V', 'PG', 'UNH', 'HD', 'MA', 'BAC', 'DIS', 'NVDA',
                             'PYPL', 'ADBE', 'CRM', 'NFLX', 'INTC', 'CSCO', 'VZ', 'KO']
            
            # If we want to filter by sector, do more detailed analysis
            if sector_match and sector != 'Unknown':
                matching_stocks = []
                
                for potential_ticker in all_stocks:
                    # Skip checking the same ticker
                    if potential_ticker == ticker:
                        continue
                        
                    try:
                        potential_info = self.service.get_stock_info(potential_ticker)
                        if potential_info and potential_info.get('sector') == sector:
                            matching_stocks.append(potential_ticker)
                    except Exception:
                        continue
                
                return matching_stocks if matching_stocks else all_stocks
            else:
                # If no sector filtering, return all stocks except the current one
                return [s for s in all_stocks if s != ticker]
        except Exception as e:
            print(f"Error finding comparable stocks: {str(e)}")
            return []
            
    def _calculate_similarity_score(self, correlation):
        """Calculate a similarity score based on correlation and other factors."""
        # Simple transformation of correlation to a 0-100 scale
        # We take the absolute value because negative correlation is still important
        return (abs(correlation) * 100)
        
    def _calculate_rating(self, correlation, price_data):
        """Calculate a rating (0-5) for a stock based on correlation and technical indicators."""
        try:
            # Base score from correlation (0-3)
            if abs(correlation) > 0.8:
                base_score = 3
            elif abs(correlation) > 0.6:
                base_score = 2
            elif abs(correlation) > 0.4:
                base_score = 1
            else:
                base_score = 0
                
            # Additional score from recent performance (0-2)
            # First, check if we have enough data
            if len(price_data) < 20:
                return base_score
                
            # Get recent returns
            if isinstance(price_data.columns, pd.MultiIndex):
                price_data.columns = price_data.columns.droplevel(1)
                
            close_col = None
            for col in price_data.columns:
                if isinstance(col, str) and col.upper() == 'CLOSE':
                    close_col = col
                    break
                    
            if close_col is None:
                return base_score
                
            # Calculate short-term momentum
            recent_return = (price_data[close_col].iloc[-1] / price_data[close_col].iloc[-20] - 1) * 100
            
            # Add points for momentum
            if recent_return > 10:  # More than 10% in last 20 days
                base_score += 2
            elif recent_return > 5:  # More than 5% in last 20 days
                base_score += 1
                
            # Cap at 5
            return min(5, base_score)
        except Exception:
            return 0

class ControlFrame(QFrame):
    """Control panel for similar stocks finder."""
    
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
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Stock Input
        input_layout = QHBoxLayout()
        stock_label = QLabel("Stock Symbol:")
        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText("Enter symbol (e.g., AAPL or SBIN.NS)")
        input_layout.addWidget(stock_label)
        input_layout.addWidget(self.stock_input)
        self.layout.addLayout(input_layout)
        
        # Options
        options_layout = QHBoxLayout()
        
        # Match by sector checkbox
        sector_label = QLabel("Match by Sector:")
        self.sector_combo = QComboBox()
        self.sector_combo.addItems(["Yes", "No"])
        options_layout.addWidget(sector_label)
        options_layout.addWidget(self.sector_combo)
        
        # Time period
        time_label = QLabel("Lookback Period:")
        self.time_combo = QComboBox()
        self.time_combo.addItems(["30 Days", "90 Days", "180 Days", "1 Year"])
        self.time_combo.setCurrentIndex(1)  # Default to 90 days
        options_layout.addWidget(time_label)
        options_layout.addWidget(self.time_combo)
        
        self.layout.addLayout(options_layout)
        
        # Find button
        self.find_button = QPushButton("Find Similar Stocks")
        self.layout.addWidget(self.find_button)

class SimilarStocksTab(QWidget):
    """Tab for finding similar stocks."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analyzer = SimilarityAnalyzer()
        self.service = YahooFinanceService()
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Control panel
        self.control_frame = ControlFrame(self)
        self.control_frame.find_button.clicked.connect(self.find_similar_stocks)
        main_layout.addWidget(self.control_frame)
        
        # Results table
        results_label = QLabel("Similar Stocks")
        results_label.setStyleSheet(f"color: {COLORS['text_bright']}; font-weight: bold; font-size: 14px;")
        main_layout.addWidget(results_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Symbol", "Name", "Price", "Similarity", "Rating", "Market Cap", "Correlation"
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
        main_layout.addWidget(self.results_table)
        
        # Status label
        self.status_label = QLabel("Enter a stock symbol to find similar stocks")
        self.status_label.setStyleSheet(f"color: {COLORS['text_dim']}; padding: 5px;")
        main_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                width: 10px;
                margin: 0px;
            }}
        """)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)
        
    def find_similar_stocks(self):
        # Get ticker from input
        ticker = self.control_frame.stock_input.text().strip()
        if not ticker:
            QMessageBox.warning(self, "Input Error", "Please enter a stock symbol")
            return
            
        # Get options
        sector_match = self.control_frame.sector_combo.currentText() == "Yes"
        
        # Get time period
        time_option = self.control_frame.time_combo.currentText()
        if time_option == "30 Days":
            days = 30
        elif time_option == "90 Days":
            days = 90
        elif time_option == "180 Days":
            days = 180
        else:  # 1 Year
            days = 365
            
        # Update status
        self.status_label.setText(f"Finding similar stocks to {ticker}...")
        self.progress_bar.show()
        self.progress_bar.setValue(10)
        
        # Clear previous results
        self.results_table.setRowCount(0)
        
        try:
            # Get stock info first to validate
            info = self.service.get_stock_info(ticker)
            if not info or info.get('currentPrice', 0) == 0:
                self.status_label.setText(f"Could not find stock information for {ticker}")
                self.progress_bar.hide()
                return
                
            self.progress_bar.setValue(30)
                
            # Find similar stocks
            similar_stocks, error = self.analyzer.find_similar_stocks(ticker, sector_match, days)
            
            self.progress_bar.setValue(80)
            
            if error:
                self.status_label.setText(f"Error: {error}")
                self.progress_bar.hide()
                return
                
            if not similar_stocks:
                self.status_label.setText(f"No similar stocks found for {ticker}")
                self.progress_bar.hide()
                return
                
            # Display the results
            self.display_results(similar_stocks, ticker)
            
            self.progress_bar.setValue(100)
            self.status_label.setText(f"Found {len(similar_stocks)} similar stocks to {ticker}")
            
            # Hide progress bar after 1 second
            def hide_progress():
                self.progress_bar.hide()
                
            # Use QTimer to hide progress bar after a delay
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1000, hide_progress)
            
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.progress_bar.hide()
            
    def display_results(self, similar_stocks, ticker):
        # Set row count
        self.results_table.setRowCount(len(similar_stocks))
        
        # Add data to table
        for i, stock in enumerate(similar_stocks):
            # Symbol
            self.results_table.setItem(i, 0, QTableWidgetItem(stock['symbol']))
            
            # Name
            self.results_table.setItem(i, 1, QTableWidgetItem(stock['name']))
            
            # Price
            price_item = QTableWidgetItem(f"${stock['current_price']:.2f}")
            self.results_table.setItem(i, 2, price_item)
            
            # Similarity score
            similarity_item = QTableWidgetItem(f"{stock['similarity_score']:.1f}%")
            self.results_table.setItem(i, 3, similarity_item)
            
            # Rating (stars)
            rating = stock['rating']
            rating_text = "★" * rating + "☆" * (5 - rating)
            rating_item = QTableWidgetItem(rating_text)
            
            # Color based on rating
            if rating >= 4:
                rating_item.setForeground(QBrush(QColor(COLORS['success'])))
            elif rating >= 3:
                rating_item.setForeground(QBrush(QColor(COLORS['accent'])))
            elif rating <= 1:
                rating_item.setForeground(QBrush(QColor(COLORS['error'])))
                
            self.results_table.setItem(i, 4, rating_item)
            
            # Market cap
            market_cap = stock['market_cap']
            if market_cap > 1_000_000_000_000:  # Trillion
                market_cap_text = f"${market_cap/1_000_000_000_000:.2f}T"
            elif market_cap > 1_000_000_000:  # Billion
                market_cap_text = f"${market_cap/1_000_000_000:.2f}B"
            elif market_cap > 1_000_000:  # Million
                market_cap_text = f"${market_cap/1_000_000:.2f}M"
            else:
                market_cap_text = f"${market_cap:,.0f}"
                
            self.results_table.setItem(i, 5, QTableWidgetItem(market_cap_text))
            
            # Correlation
            correlation = stock['correlation']
            correlation_item = QTableWidgetItem(f"{correlation:.2f}")
            
            # Color correlation by strength
            if abs(correlation) > 0.7:
                correlation_item.setForeground(QBrush(QColor(COLORS['success'])))
            elif abs(correlation) < 0.3:
                correlation_item.setForeground(QBrush(QColor(COLORS['error'])))
                
            self.results_table.setItem(i, 6, correlation_item) 