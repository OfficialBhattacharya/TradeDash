# TradeDash

A professional trading application built with Python and PyQt5, featuring real-time stock data visualization, market analysis, and stock recommendations.

![TradeDash_Preview](https://github.com/user-attachments/assets/59b51a3b-6a45-4d4a-a615-6713e06513eb)
![TradeDash_Preview2](https://github.com/user-attachments/assets/a4d968b4-5ac1-41a6-845c-ea1cf7069f52)
![TradeDash_Preview3](https://github.com/user-attachments/assets/66eff660-3fd6-42ec-8e16-781db2cde4a7)
![TradeDash_Preview4](https://github.com/user-attachments/assets/d9ccf6d9-34ab-438d-85d1-6138f8889654)
![TradeDash_Preview5](https://github.com/user-attachments/assets/3b58d543-7fb6-4603-9749-cb02cbd7c19f)
![TradeDash_Preview6](https://github.com/user-attachments/assets/fff66665-f884-4026-9010-1cfa6744a60d)
![TradeDash_Preview7](https://github.com/user-attachments/assets/93312523-c175-4739-a363-ce46dba11129)

## Requirements

- Anaconda or Miniconda installed on your system
- Windows operating system

## Installation & Running

### One-Click Setup and Launch
1. Clone or download this repository
2. Simply double-click the `run_app.bat` file:
   - It will check if Conda is installed
   - Create a "tradedash" conda environment if it doesn't exist
   - Install all required dependencies automatically
   - Launch the application

### Desktop Shortcut (Optional)
1. Run `create_desktop_shortcut.bat` to create a desktop shortcut
2. Double-click the Desktop shortcut "TradeDash" to launch the application

## Troubleshooting

If you encounter issues:
1. Make sure Anaconda or Miniconda is properly installed
2. Check if the PATH environment variable includes the Conda installation
3. If you get missing package errors, try running `install_packages.bat` separately
4. Review any error messages displayed in the console window

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
