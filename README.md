pyrcc5 -o qrc_resources.py resources.qrc  

# Prerequisite
Python is not providing executable to install it in WINDOWS 7 after PYTHON3.8.10 release: So stick with this version  
0, Download or clone this repo  
1, Download python 3.8.10 - https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe and install and add PYTHON installed location to path  
2, Install dependencies:  
```bash
pip install wheel build setuptools pyyaml pyqt5 paramiko zeroconf scp pyqt5-tools "kivy[base]" "kivy[sdl2]" kivymd easydict opencv-python pyinstaller lxml qtsasstheme  
```
3, Build executable  
```bash
python -m PyInstaller --add-data "logger.py:." --add-data "app_settings_format.yaml:." --add-data "inference_manager_settings_format.yaml:." --add-data "config.py:." --add-data "remote_works.py:." --add-data "remote_device.py:." --add-data "config:config" --add-data "fonts:fonts" --add-data "kv:kv" --add-data "libs:libs" --add-data "baseclass:baseclass" --add-data "UIFiles:UIFiles" --add-data "utils.py:."  --add-data "SFTPClient.py:." --add-data "customdialog.py:." --add-data "globals.py:." --name "Technician" -y --hidden-import "baseclass\root_screen.py" --collect-all "kivymd" --collect-all "zeroconf" --hide-console hide-early -i ktc_logo.ico --add-data "qt_sass_theme;./qt_sass_theme" main.py --onefile --upx-dir upx-4.2.1-win64  

--windowed --noconsole
```

# Helper
E:\user_3179\software\Lib\site-packages\qt5_applications\Qt\bin\designer.exe  
~/01_user_3179/repos/ktc-technician-app/venv/lib/python3.9/site-packages/qt5_applications/Qt/bin/designer  

For Linux:  
*python 3.9*  
sudo apt-get install python3.9 python3.9-pip python3.9-venv qttools5-dev-tools qtcreator python3-pyqt5 pyqt5-dev-tools xclip xsel
pip install pyyaml pyqt5 paramiko zeroconf scp pyqt5-tools "kivy[base]" "kivy[sdl2]" kivymd easydict opencv-python pyinstaller  
pip install pyqt5 --config-settings --confirm-license= --verbose  
pip install --config-settings="--confirm-license=" --verbose pyqt5  
pip install --config-settings --confirm-license= --verbose pyqt5  
pip install pyqt5 --confirm-license= --verbose  



Class RTSPStreamSource:
  + sourceURL
  + startStream()
  + stopStream()

Class RTSPStreamWriter:
  + buffer
  + storageLocation
  + captureStream()
  + writeToStorage()

Class DeviceMonitor:
  + deviceStatus
  + checkDeviceStatus()
  + alertUser()

Class Storage:
  + storagePath
  + storageType
  + saveData()
  + retrieveData()

Class UserInterface:
  + display
  + userInputs
  + showStreams()
  + manageDevices()

RTSPStreamSource --> RTSPStreamWriter: startStream()
RTSPStreamWriter --> Storage: writeToStorage()
DeviceMonitor --> RTSPStreamWriter: checkDeviceStatus()
RTSPStreamWriter --> DeviceMonitor: alertUser()
UserInterface --> DeviceMonitor: manageDevices()
UserInterface --> Storage: retrieveData()






























