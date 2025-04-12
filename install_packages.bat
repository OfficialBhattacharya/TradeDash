@echo off
echo Installing required packages for TradeDash...
call C:\Users\offic\anaconda3\Scripts\activate.bat tradedash
pip install -r requirements.txt
pip install yfinance pandas matplotlib PyQt5 ta 
echo Installation complete!
pause 