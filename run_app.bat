@echo off
echo Activating conda environment 'tradedash'...
call C:\Users\offic\anaconda3\Scripts\activate.bat tradedash
echo Environment activated. Running TradeDash application...
python -m tradedash.main
if %errorlevel% neq 0 (
    echo Application exited with error code %errorlevel%
    echo Check error messages above
    pause
) else (
    echo Application closed successfully
    pause
) 