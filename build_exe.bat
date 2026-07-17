@echo off
chcp 65001 >nul
echo =====================================================
echo   building
echo =====================================================

REM 1) create venu
if not exist venv (
    echo [1/4] create venu...
    python -m venv venv
)

REM 2) activate venu
call venv\Scripts\activate.bat

REM 3) install requirements + PyInstaller
echo [2/4] install requirements...
pip install -r requirements.txt
pip install pyinstaller

REM 4) building exe
echo [3/4] building exe, may take time...
pyinstaller app.spec --noconfirm

echo [4/4] exe file created at: dist\MemberBoardGASystem.exe
echo you can copy exe file to any pc
pause
