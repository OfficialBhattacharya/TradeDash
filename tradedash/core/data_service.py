import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.DEBUG)

def get_stock_suffix(symbol):
    """Add .NS suffix for NSE stocks if needed"""
    # Don't add suffix if it already has one (like .NS, .BO, .L, etc.)
    if '.' in symbol:
        return symbol
    # Default to US exchange if no suffix
    return symbol

def _get_stock_info_internal(symbol):
    """Get stock information for a given symbol (internal implementation)."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            'name': info.get('longName', info.get('shortName', symbol)),
            'sector': info.get('sector', 'Unknown'),
            'market_cap': info.get('marketCap', 0),
            'currentPrice': info.get('currentPrice', info.get('regularMarketPrice', info.get('previousClose', 0))),
            'longName': info.get('longName', info.get('shortName', symbol)),
            'symbol': symbol
        }
    except Exception as e:
        print(f"Error getting stock info: {e}")
        return {
            'name': symbol,
            'sector': 'Unknown',
            'market_cap': 0,
            'currentPrice': 0,
            'longName': symbol,
            'symbol': symbol
        }

def _fetch_stock_data_internal(symbol, start_date, end_date):
    """Fetch stock data for a given symbol and date range (internal implementation)."""
    try:
        # Check for None dates
        if start_date is None or end_date is None:
            print(f"Error: start_date or end_date is None. start_date={start_date}, end_date={end_date}")
            return pd.DataFrame()
            
        # Ensure dates are properly formatted
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
            
        # Add one day to end_date to include the actual end date in results
        adjusted_end_date = end_date + timedelta(days=1)
        
        data = yf.download(symbol, start=start_date, end=adjusted_end_date)
        
        if data.empty:
            print(f"No data found for {symbol}")
            return pd.DataFrame()
            
        return data
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return pd.DataFrame()

class YahooFinanceService:
    """Service for fetching stock data from Yahoo Finance."""
    
    def fetch_data(self, symbol, start_date, end_date):
        """Fetch stock data for a given symbol and date range."""
        # Ensure dates are properly set
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
            print(f"Setting default start_date to {start_date}")
            
        if end_date is None:
            end_date = datetime.now()
            print(f"Setting default end_date to {end_date}")
            
        # Try with original symbol first
        data = _fetch_stock_data_internal(symbol, start_date, end_date)
        
        # If no data found and symbol doesn't have a suffix, try with .NS (for Indian stocks)
        if data.empty and '.' not in symbol:
            ns_symbol = f"{symbol}.NS"
            print(f"No data found for {symbol}, trying {ns_symbol}")
            data = _fetch_stock_data_internal(ns_symbol, start_date, end_date)
            
        return data
    
    def get_stock_info(self, symbol):
        """Get stock information for a given symbol."""
        return _get_stock_info_internal(symbol)
    
    def fetch_stock_data(self, symbol, start_date, end_date):
        """Alias for fetch_data to maintain compatibility."""
        return self.fetch_data(symbol, start_date, end_date)

# Convenience functions - renamed to avoid recursion
def fetch_stock_data(symbol, start_date=None, end_date=None):
    if start_date is None:
        start_date = datetime.now() - timedelta(days=365)
    if end_date is None:
        end_date = datetime.now()
    service = YahooFinanceService()
    return service.fetch_data(symbol, start_date, end_date)

def get_stock_info(symbol):
    service = YahooFinanceService()
    return service.get_stock_info(symbol) 