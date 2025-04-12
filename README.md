# TradeDash

A professional trading application built with Python and PyQt5, featuring real-time stock data visualization, market analysis, and stock recommendations.

## Features

- **Real-time Stock Data**: Access live and historical stock data from Yahoo Finance
- **Professional Charting**: Interactive charts with zoom, scroll, and technical indicators
- **Market Scanner**: Find top stocks based on performance, volatility, and trends
- **Similar Stocks Finder**: Discover stocks with similar price movements and characteristics
- **Stock Recommendations**: Get personalized stock recommendations based on technical analysis
- **Strategy Backtesting**: Test trading strategies with historical data
- **PnL Simulation**: Simulate potential profits and losses for different scenarios
- **Clean, Modern UI**: Dark theme interface with intuitive navigation

## Key Components

### Market Scanner
- Scan for top 5 stocks turning bullish, bearish, or to hold
- Identify volatile stocks for trading opportunities
- Filter by market (NSE, NYSE, or both) and price range
- Customizable lookback periods for analysis

### Similar Stocks Finder
- Find 5 similar stocks based on price movement correlation
- Match by sector or company characteristics
- Star rating system (0-5) for quick evaluation
- Detailed similarity metrics and correlation coefficients

## Installation

1. Clone the repository:
```bash
git clone https://github.com/OfficialBhattacharya/TradeDash.git
cd tradedash
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

Or run the installation script:
```bash
install_packages.bat
```

## Usage

Run the application using:
```bash
python -m tradedash.main
```

Or use the provided script:
```bash
run_app.bat
```

## Requirements

- Python 3.8+
- PyQt5
- yfinance
- pandas
- numpy
- matplotlib
- ta (Technical Analysis library)

## Project Structure

```
tradedash/
├── config/         # Configuration files and settings
├── core/           # Core functionality and data services
├── ui/             # User interface components
│   └── widgets/    # UI widgets and tabs
├── main.py         # Application entry point
└── __init__.py     # Package initialization
```

## License

MIT License 