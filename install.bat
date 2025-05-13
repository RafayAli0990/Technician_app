SET CURRENTDIR=%cd%
SET PYTHON_PATH=%userprofile%\AppData\Local\Programs\Python\Python38
if exist "%PYTHON_PATH%\python.exe" (
    ECHO "%PYTHON_PATH%\python.exe" exists already. Skipping..
) else (
    .\python-3.8.10-amd64
)
::ECHO %userprofile%\AppData\Local\Programs\Python\Python38
::ECHO %PYTHON_PATH%
::ECHO %CURRENTDIR%
::ECHO %PATH%
::ECHO %PATH%
::setx PYTHON "" /m
::ECHO "%PYTHON_PATH%\python" -m pip install wheel build setuptools pyyaml pyqt5 paramiko zeroconf scp pyqt5-tools "kivy[base]" "kivy[sdl2]" kivymd easydict opencv-python pyinstaller qtsasstheme lxml
"%PYTHON_PATH%\python" -m pip install wheel build setuptools pyyaml pyqt5 paramiko zeroconf scp pyqt5-tools "kivy[base]" "kivy[sdl2]" kivymd easydict opencv-python pyinstaller==6.1.0 qtsasstheme lxml
"%PYTHON_PATH%\python" -m PyInstaller --add-data "logger.py:." --add-data "app_settings_format.yaml:." --add-data "app_settings_format_ldms.yaml:." --add-data "inference_manager_settings_format.yaml:." --add-data "config.py:." --add-data "remote_works.py:." --add-data "remote_device.py:." --add-data "icons:icons" --add-data "fonts:fonts" --add-data "kv:kv" --add-data "libs:libs" --add-data "baseclass:baseclass" --add-data "UIFiles:UIFiles" --add-data "utils.py:."  --add-data "SFTPClient.py:." --add-data "customdialog.py:." --add-data "globals.py:." --name "Technician" -y --hidden-import "baseclass\root_screen.py" --collect-all "kivymd" --collect-all "zeroconf" --hide-console hide-early -i ktc_logo.ico --add-data "qt_sass_theme;./qt_sass_theme" main.py --onefile --upx-dir upx-4.2.1-win64
::ECHO %CURRENTDIR%\dist\Technician
ECHO Adding to Desktop folder: %userprofile%\Desktop\Technician.exe
xcopy "%CURRENTDIR%\dist\Technician.exe" "%userprofile%\Desktop\*" /S /Y /D
ECHO Desktop folder: %userprofile%\Desktop\Technician.exe
if exist "%userprofile%\Desktop\Technician.exe" (
    msg "%username%" Installation successful. Desktop folder: %userprofile%\Desktop\Technician.exe
) else (
    msg "%username%" Installation failed. Report or try again.
)
PAUSE
