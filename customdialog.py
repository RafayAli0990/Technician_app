import os
import ipaddress
import csv
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QApplication, QLabel, QMessageBox, QDialogButtonBox, QFileDialog, QPushButton, QLineEdit, QComboBox, QWidget, QHBoxLayout, QCheckBox, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QDir, QMutexLocker, QMutex, QThread, QObject, pyqtSignal, QTimer
from copy import deepcopy
import time
from PyQt5.QtGui import QPixmap
import remote_works
import sys
from remote_device import RemoteDevice

from PyQt5.QtWidgets import *
from ui_main import Ui_MainWindow
from ui_splash_screen import Ui_SplashScreen
from PyQt5.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter, QPixmap, QRadialGradient)

class CustomDialog(QDialog):
    def __init__(self, parentWidget, prompt_title:str, prompt_msg:str , waiting_prompt:bool, popup_window_size:tuple=None):
        super().__init__(parentWidget)
        if waiting_prompt:
            self.setWindowFlag(Qt.WindowCloseButtonHint, False)

        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(prompt_title)
        if popup_window_size:
            self.setFixedSize(popup_window_size[0], popup_window_size[1])
        QBtn = QDialogButtonBox.Ok

        # button
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        if waiting_prompt:
            self.buttonBox.setEnabled(False)

        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel(prompt_msg))
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

class LoginDialog(QDialog):
    def __init__(self, parent=None, package_dir=""):
        super(LoginDialog, self).__init__(parent)
        uic.loadUi(os.path.join(package_dir, "UIFiles", "login.ui"), self)
        self.package_dir = package_dir

        self.loginButton = self.findChild(QPushButton, 'loginButton')
        self.cancelButton = self.findChild(QPushButton, 'cancelButton')
        self.loginButton.clicked.connect(self.login)
        self.cancelButton.clicked.connect(self.cancel)

        self.passwordLineEdit = self.findChild(QLineEdit, 'passwordLineEdit')
        self.passwordLineEdit.setEchoMode(QLineEdit.Password)

    def login(self):
        username = self.findChild(QLineEdit, 'usernameLineEdit').text()
        password = self.passwordLineEdit.text()

        
        if username == "admin" and password == "Support01" or username == "dev" and password == "Ktc@123$-dv": 
            self.accept()
            QMessageBox.information(self, "Login Successful", "Welcome, " + username + "!")
            # print(f"{username} login successful!")
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password. Please try again.")
            # print(f"{username} login failed!")

        self.cancelButton =self.findChild(QPushButton, 'cancelButton')
        self.loginButton = self.findChild(QPushButton, 'loginButton')
        username = self.findChild(QLineEdit, 'usernameLineEdit').text()
        password = self.findChild(QLineEdit, 'passwordLineEdit').text()

    def cancel(self):
        print("Exiting the application.")
        self.close()
        QApplication.instance().quit()
        sys.exit(0)
    def closeEvent(self, event):
        event.ignore()  

class FlashDialog(QDialog):
    def __init__(self, parentWidget, package_dir):
        super().__init__(parentWidget)
        self.package_dir = package_dir
        uic.loadUi(os.path.join(self.package_dir,"UIFiles","flashDialog.ui"), self)

        self.browseFileButton = self.findChild(QPushButton, 'browseFileButton')
        self.flashFileButton = self.findChild(QPushButton, 'flashFileButton')
        self.flashFilePathLineEdit = self.findChild(QLineEdit,'flashFilePath')
        self.flashFilePathLineEdit.setReadOnly(True)

        self.flashFileButton.hide()

        self.browseFileButton.clicked.connect(self.browse_file)
        self.flashFileButton.clicked.connect(self.flash_file)
        
        self.flashFilePath = None

    def flash_file(self):
        self.accept()

    def browse_file(self):
        # fileDialog = QFileDialog(self)
        # options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        # options |= QFileDialog.DontUseCustomDirectoryIcons
        dialog = QFileDialog()
        # dialog.setOptions(options)

        dialog.setFilter(dialog.filter() | QDir.Hidden)
        dialog.setDefaultSuffix('kfl')
        # dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setNameFilters(['KFL (*.kfl)'])

        if dialog.exec_() == QDialog.Accepted:
            self.flashFilePath = dialog.selectedFiles()[0]
            self.flashFilePathLineEdit.setText(dialog.selectedFiles()[0])
            self.flashFileButton.show()
        else:
            # cancelled
            self.flashFilePath = None
            self.flashFileButton.hide()

class ManualDeviceAdditionDialog(QDialog):
    def __init__(self, parentWidget, package_dir:str):
        super().__init__(parentWidget)
        self.package_dir = package_dir
        uic.loadUi(os.path.join(self.package_dir,"UIFiles","manualDeviceAdditionDialog.ui"), self)

        # Single Device
        self.addSingleDeviceButton = self.findChild(QPushButton, "addSingleDeviceButton")
        self.addSingleDeviceButton.clicked.connect(self.cvs_add_single_device)
        self.ipAddressLineEdit = self.findChild(QLineEdit,"ipAddressLineEdit")
        self.swPNLineEdit = self.findChild(QLineEdit,"swPNLineEdit")
        self.hwPNLineEdit = self.findChild(QLineEdit,"hwPNLineEdit")
        self.productLineEdit = self.findChild(QLineEdit,"productLineEdit")

        # Multiple Device
        self.csvBrowseFileButton = self.findChild(QPushButton, 'browseFileButton')
        self.csvConfirmFileButton = self.findChild(QPushButton, 'addCSVFileButton')
        self.csvFilePathLabel = self.findChild(QLabel,'fileNameLabel')

        self.csvConfirmFileButton.hide()

        self.csvBrowseFileButton.clicked.connect(self.browse_file)
        self.csvConfirmFileButton.clicked.connect(self.cvs_add_multi_device)
        
        # default inits
        self.csvFilePath = None
        self.csvBasedDeviceAddition = False
        self.multiAddDeviceList = []

    def cvs_add_multi_device(self):
        self.csvBasedDeviceAddition = True

        # Parse CSV and populate data into LineEdits
        with open(self.csvFilePath, 'r') as csvfile:
            # creating a csv reader object
            csvreader = csv.reader(csvfile)
        
            # extracting field names through first row
            fields = next(csvreader) # TODO: use fields to map
        
            # extracting each data row one by one
            for row in csvreader:
                _device = {'ip_addr': row[0], 'sw_info': row[1], 'hw_info': row[2], 'product_name': row[3]}
                self.multiAddDeviceList.append(_device)
        
        self.accept()

    def cvs_add_single_device(self):
        try:
            ipaddress.IPv4Address(self.ipAddressLineEdit.text().strip())
            self.csvBasedDeviceAddition = False
            self.accept()
        except Exception as e:
            CustomDialog(self, prompt_title="Error", prompt_msg=f"Check IPv4 address provided.\nRetry. Failed due to error: {e}" ,  waiting_prompt=False).show()

    def browse_file(self):
        # fileDialog = QFileDialog(self)
        # options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        # options |= QFileDialog.DontUseCustomDirectoryIcons
        dialog = QFileDialog()
        # dialog.setOptions(options)

        dialog.setFilter(dialog.filter() | QDir.Hidden)
        dialog.setDefaultSuffix('csv')
        # dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setNameFilters(['CSV (*.csv)'])

        if dialog.exec_() == QDialog.Accepted:
            self.csvFilePath = dialog.selectedFiles()[0]
            self.csvFilePathLabel.setText(dialog.selectedFiles()[0])
            self.csvConfirmFileButton.show()
        else:
            # cancelled
            self.csvFilePath = None
            self.csvConfirmFileButton.hide()
class Communicate(QObject):
    signal = pyqtSignal(str)

class Progresses(QObject):
    progress = pyqtSignal(int)

class SMARTConfigSaveTimer(QThread):
    def __init__(self, frequent=20):
        QThread.__init__(self)
        self.stopped = False
        self.frequent = frequent
        self.timeSignal = Communicate()
        # self.processes = Progresses()
        self.mutex = QMutex()
        print("1")

    def run(self):
        with QMutexLocker(self.mutex):
            self.stopped = False
        while True:
            if self.stopped:
                return
            self.timeSignal.signal.emit("1")
            time.sleep(1 / self.frequent)

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    def is_stopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped

    def set_fps(self, fps):
        self.frequent = fps

class SMARTServiceDialog(QDialog):
    progress = pyqtSignal(int)
    def __init__(self, parentWidget, package_dir:str, device_ip:str, active_services:dict):
        # print("ParentWidgets :: ---->>>", parentWidget)
        # if not isinstance(parentWidget, QWidget):
        #     parentWidget = None
        super().__init__(parentWidget)
        self.package_dir = package_dir
        uic.loadUi(os.path.join(self.package_dir, "UIFiles", "configSMARTServices.ui"), self)
        self.device_ip = device_ip
        self.mobile_service_checkbox = self.findChild(QCheckBox, "mobileSeatbeltCheckbox")
        self.mobile_service_checkbox.stateChanged.connect(self.mobile_service_clicked)

        self.ped_service_checkbox = self.findChild(QCheckBox, "PedetrianBox")
        self.ped_service_checkbox.stateChanged.connect(self.ped_service_clicked)

        self.Lane_service_checkbox = self.findChild(QCheckBox, "LaneDCheckBox")
        self.Lane_service_checkbox.stateChanged.connect(self.ldms_service_clicked)

        self.noentry_service_checkbox = self.findChild(QCheckBox, "NoentryCheckBox")
        self.noentry_service_checkbox.stateChanged.connect(self.noentry_service_clicked)

        self.uturn_service_checkbox = self.findChild(QCheckBox, "UturnCheckBox")
        self.uturn_service_checkbox.stateChanged.connect(self.uturn_service_clicked)
        
        self.activeServices = active_services.copy()  # {"detect_mobile": False, "detect": False}
        self.last_values_dict = active_services.copy()
        
        self.InformationSectionDialog(device_ip, active_services)
        self._initialize_service_checkboxes(device_ip)
        # self.progress.connect(self.splash_screen.progressBarValue)
        self.savetimer = SMARTConfigSaveTimer(frequent=1)
        self.savetimer.timeSignal.signal[str].connect(self.save)
        self.savetimer.set_fps(1)
        self.savetimer.start()
        _, self.remoteDevice = remote_works.just_connect(device_ip)
    def _initialize_service_checkboxes(self, device_ip):
        remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia")  # TODO: get password dynamically?
        retVal = remoteDevice.connect()
        if retVal:
            _, str_stdout, _ = remoteDevice.exec_cmd("systemctl list-unit-files | grep detect")
            if "detect_mobile" in str_stdout:
                self.mobile_service_checkbox.setChecked(self.activeServices.get("detect_mobile", False))
            else:
                self.mobile_service_checkbox.setDisabled(True)
            if "detect" in str_stdout:
                self.ped_service_checkbox.setChecked(self.activeServices.get("detect", False))
            else:
                self.ped_service_checkbox.setDisabled(True)
            if "detect_ldms" in str_stdout:
                self.Lane_service_checkbox.setChecked(self.activeServices.get("detect_ldms", False))
            else:
                self.Lane_service_checkbox.setDisabled(True)
            if "detect_noentry" in str_stdout:
                self.noentry_service_checkbox.setChecked(self.activeServices.get("detect_noentry", False))
            else:
                self.noentry_service_checkbox.setDisabled(True)
            if "detect_rlms" in str_stdout:
                self.uturn_service_checkbox.setChecked(self.activeServices.get("detect_rlms", False))
            else:
                self.uturn_service_checkbox.setDisabled(True)        
            
            # remoteDevice.disconnect()
            
    def InformationSectionDialog(self, device_ip, active_services):
        print("               __________Calls this_________              ")
        software_info = remote_works.Software(device_ip)
        deepstream_info = remote_works.Deepstream(device_ip)
        active_services_info = remote_works.check_active_services_part2(device_ip)
        inactive_services_info = remote_works.Inactive_services(device_ip, active_services)
        device_info = remote_works.DeviceInstallation(device_ip)

        self.software_version = self.findChild(QLabel, "retrievedSoftwareVersion").setText(software_info["retrievedSoftwareVersion"])
        self.deepstream_version = self.findChild(QLabel, "retrievedDeepStreamVersion").setText(deepstream_info["retrievedDeepStreamVersion"])
        self.active_services = self.findChild(QLabel, "retrievedActiveServices").setText(", ".join(active_services_info["retrievedActiveServices"]))
        self.inactive_services = self.findChild(QLabel, "retrievedInactiveServices").setText(", ".join(inactive_services_info["retrievedInactiveServices"]))
        self.installation_date = self.findChild(QLabel, "retrievedDeviceInstallationDate").setText(device_info["retrievedDeviceInstallationDate"])

        # self.findChild(QLabel, "softwareVersionLabel").setText(software_info["retrievedSoftwareVersion"])
        # self.findChild(QLabel, "deepStreamVersionLabel").setText(deepstream_info["retrievedDeepStreamVersion"])
        # self.findChild(QLabel, "activeServicesLabel").setText(", ".join(active_services_info["retrievedActiveServices"]))
        # self.findChild(QLabel, "inactiveServicesLabel").setText(", ".join(inactive_services_info["retrievedInactiveServices"]))
        # self.findChild(QLabel, "deviceInstallationDateLabel").setText(device_info["retrievedDeviceInstallationDate"])

    def save(self):
        update_dict = {}
        for k, v in self.activeServices.items():
            if self.last_values_dict[k] != self.activeServices[k]:
                update_dict[k] = v

        if len(update_dict) > 0:
            # loading_screen = CustomDialog(self, prompt_title=f"Saving. Please wait!!",
            #                               prompt_msg=f"Loading",
            #                               waiting_prompt=True,
            #                               popup_window_size=(400,0))
            # loading_screen.show()
            print(update_dict)
            try:
                retVal = remote_works.set_services_state(self.device_ip, update_dict, self.remoteDevice)
            except Exception as e:
                print(f"This is an Exception: {e}")

            if retVal == "SUCCESS":
                # self.progress.emit(100)
                # loading_screen.accept()
                self.last_values_dict = self.activeServices.copy()
                CustomDialog(self, prompt_title="Status change successfully",
                             prompt_msg=f"{update_dict}",
                             waiting_prompt=False).show()
            else:
                # loading_screen.accept()
                CustomDialog(self, prompt_title="Status change unsuccessfully",
                             prompt_msg="Failed to update services",
                             waiting_prompt=False).show()

    def mobile_service_clicked(self, value):
        self.activeServices["detect_mobile"] = bool(value)

    def ped_service_clicked(self, value):
        self.activeServices["detect"] = bool(value)

    def noentry_service_clicked(self, value):
        self.activeServices["detect_noentry"] = bool(value)

    def ldms_service_clicked(self, value):
        self.activeServices["detect_ldms"] = bool(value)

    def uturn_service_clicked(self, value):
        self.activeServices["detect_rlms"] = bool(value)

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QApplication, QGraphicsDropShadowEffect

# Import the SplashScreen UI file generated from Qt Designer
from ui_splash_screen import Ui_SplashScreen
counter = 0 
jumper = 10

class SplashScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_SplashScreen()
        self.ui.setupUi(self)
        self.counter = 0

        # self.timer = QtCore.QTimer()
        # self.timer.timeout.connect(self.increment_progress)
        # self.timer.start(50)  # Adjust the interval for smoothness or speed of progress

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 120))
        self.ui.circularBg.setGraphicsEffect(self.shadow)

        # self.show()

    def increment_progress(self):
        self.counter += 1
        self.progressBarValue(self.counter)  # Update the circular progress bar

        htmlText = """<p><span style=" font-size:68pt;">{VALUE}</span><span style=" font-size:58pt; vertical-align:super;">%</span></p>"""
        newHtml = htmlText.replace("{VALUE}", str(self.counter))
        self.ui.labelPercentage.setText(newHtml)

        # Close splash screen when progress is complete
        if self.counter >= 100:
            self.timer.stop()
            self.close()  

    def progressBarValue(self, value):
        """Update the style of the circular progress bar based on the given value."""
        styleSheet = """
        QFrame{
            border-radius: 150px;
            background-color: qconicalgradient(cx:0.5, cy:0.5, angle:90, stop:{STOP_1} rgba(255, 0, 127, 0), stop:{STOP_2} rgba(85, 170, 255, 255));
        }
        """

        # Clamp the value to the valid range (0 to 100)
        value = max(0, min(value, 100))

        htmlText = """<p><span style=" font-size:56pt;">{VALUE}</span><span style=" font-size:58pt; vertical-align:super;">%</span></p>"""
        newHtml = htmlText.replace("{VALUE}", str(value))
        self.ui.labelPercentage.setText(newHtml)

        # Calculate the progress as a value between 0.0 and 1.0
        progress = (100 - value) / 100.0
        stop_1 = max(0.0, min(progress - 0.001, 1.0))
        stop_2 = max(0.0, min(progress, 1.0))

        # Replace placeholders in the stylesheet with calculated values
        newStylesheet = styleSheet.replace("{STOP_1}", str(stop_1)).replace("{STOP_2}", str(stop_2))
        self.ui.circularProgress.setStyleSheet(newStylesheet)

    def progress(self):
        """Simulate progress for the progress bar."""
        global counter
        global jumper
        value = counter

        # Update the percentage text
        htmlText = """<p><span style=" font-size:68pt;">{VALUE}</span><span style=" font-size:58pt; vertical-align:super;">%</span></p>"""
        newHtml = htmlText.replace("{VALUE}", str(jumper))

        if value > jumper:
            self.ui.labelPercentage.setText(newHtml)
            jumper += 10

        # Update the progress bar value
        if value >= 100:
            value = 1.000  # Maximum value
        self.progressBarValue(value)

        # Close the splash screen when progress completes
        if counter > 100:
            self.timer.stop()
            self.close()

        counter += 0.5

class CameraDetailsDialog(QDialog):
    def __init__(self, parentWidget, package_dir:str):
        super().__init__(parentWidget)
        self.package_dir = package_dir
        uic.loadUi(os.path.join(self.package_dir,"UIFiles","cameraDetailsDialog.ui"), self)

        self.PEDcameraRTSPURLEdit = self.findChild(QLineEdit,"PEDcameraRTSPURL")
        self.PEDpredefinedDropDown = self.findChild(QComboBox, "predefinedPEDDropDown")
        # self.ped_camera_uri = ""

        self.MOBcameraRTSPURLEdit = self.findChild(QLineEdit,"MOBcameraRTSPURL")
        self.MOBpredefinedDropDown = self.findChild(QComboBox, "predefinedMOBDropDown")
        # self.mob_camera_uri = ""

        self.setPEDCameraRTSPURLEdit()
        self.setMOBCameraRTSPURLEdit()

        self.PEDpredefinedDropDown.currentIndexChanged.connect(self.setPEDCameraRTSPURLEdit)
        self.MOBpredefinedDropDown.currentIndexChanged.connect(self.setMOBCameraRTSPURLEdit)
        
    
    def setPEDCameraRTSPURLEdit(self):
        currentSelectedText = self.PEDpredefinedDropDown.currentText()

        rtsp_uri = ''
        if currentSelectedText == "HIKVISION":
            rtsp_uri = "rtsp://admin:Support01@192.168.1.10:554/Streaming/channels/1/"
        elif currentSelectedText == "DAHUA":
            rtsp_uri = "rtsp://admin:Support01@192.168.1.10:554/cam/realmonitor?channel=1&subtype=0"

        # self.ped_camera_uri = rtsp_uri
        self.PEDcameraRTSPURLEdit.setText(rtsp_uri)

    def setMOBCameraRTSPURLEdit(self):
        currentSelectedText = self.MOBpredefinedDropDown.currentText()

        rtsp_uri = ''
        if currentSelectedText == "HIKVISION":
            rtsp_uri = "rtsp://admin:Support01@192.168.1.20:554/Streaming/channels/1/"
        elif currentSelectedText == "DAHUA":
            rtsp_uri = "rtsp://admin:Support01@192.168.1.20:554/cam/realmonitor?channel=1&subtype=0"

        # self.mob_camera_uri = rtsp_uri
        self.MOBcameraRTSPURLEdit.setText(rtsp_uri)