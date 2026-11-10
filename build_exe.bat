@echo off
echo ========================================================
echo   MeWe AutoFollow - PyInstaller Windows 11 Build Tool
echo ========================================================
echo [1/3] Installing dependencies...
python -m pip install -r requirements.txt
echo [2/3] Installing Playwright Chromium browser...
python -m playwright install chromium
echo [3/3] Compiling EXE with PyInstaller...
python -m PyInstaller --noconfirm mewe_autofollow.spec
echo BUILD COMPLETE! Check dist\MeWeAutoFollow\MeWeAutoFollow.exe
pause
