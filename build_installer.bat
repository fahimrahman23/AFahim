@echo off
echo Compiling Windows 11 Installer (Setup.exe)...
if not exist "dist\MeWeAutoFollow\MeWeAutoFollow.exe" call build_exe.bat
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" inno_setup.iss
echo Done! Output saved to: release\MeWe_AutoFollow_Setup.exe
pause
