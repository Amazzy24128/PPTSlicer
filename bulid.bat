@echo off
echo Building executable for PPTSlicer...

pyinstaller --name PPTSlicer ^
            --onefile ^
            --windowed ^
            --icon="assets/icon.ico" ^
            main.py

echo Build finished! Check the 'dist' folder.
pause