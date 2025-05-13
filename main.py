import sys
import os
import yaml
import socket
import shutil
import platform
import paramiko
import subprocess

from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QProgressBar, QLabel, QStatusBar, QListWidget, QTextBrowser, QDialog, QAbstractItemView,QColorDialog
from PyQt5 import uic

from utils import load_yaml#, restart_xavier

from customdialog import CustomDialog, FlashDialog, ManualDeviceAdditionDialog, CameraDetailsDialog , SMARTServiceDialog, LoginDialog, SplashScreen
import ktc_device_scanner
import remote_works
from logger import LoggerUtils
from remote_device import RemoteDevice
import qrc_resources

from qt_sass_theme import QtSassTheme
import requests

UIWindow = None
os.environ["CONFIG_ROOT"] = os.path.dirname(os.path.abspath(__file__))

from PyQt5.QtCore import QThread, pyqtSignal
import os
import requests
import shutil
import subprocess
import platform
import time

from PyQt5.QtCore import Qt, QDir, QMutexLocker, QMutex, QThread, QObject, pyqtSignal, QTimer
from PyQt5.QtCore import QThread, QCoreApplication

class Worker(QThread):
    progress = pyqtSignal(int) 
    log_message = pyqtSignal(str, str, int)

    def __init__(self, device_ip, package_dir):
        super().__init__()
        self.device_ip = device_ip
        # print("Worker ", device_ip)
        self.package_dir = os.path.dirname(os.path.abspath(__file__))
        self.activeServicesDict = {}
        self.stopped = False
        self.mutex = QMutex()
        self.ssh = None

    def check_connectivity(self, device_ip: str):
        try:
            #self.log_message.emit("INFO", f"[STEP 1] Check connectivity for {self.device_ip}...", 0)
            remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia") # TODO: get password dynamically?
            retVal = remoteDevice.connect()
            parameter = "-n" if platform.system().lower() == "windows" else "-c"
            response = subprocess.call(["ping", parameter, "1", device_ip])
            #self.log_message.emit("INFO", f"[STEP 1] Checking connectivity for {self.device_ip}...", 0)
            if response != 0:
                CustomDialog(
                    self,
                    prompt_title="Connection Failed",
                    prompt_msg="Retry to try again!!",
                    waiting_prompt=False
                ).show()
                raise Exception(f"Failed to connect to {self.device_ip}. Exiting...")
            self.log_message.emit("INFO", f"[SUCCESS] Connectivity check passed for {self.device_ip}.", 0)
            return True
        except Exception as e:
            self.log_message.emit("INFO", f"[ERROR] Connectivity check failed: {str(e)}", 0)
            print(f"Exception: {e}")
            return False 

    def identify_device_type(self):
        try:
            remoteDevice = RemoteDevice(self.device_ip, "nvidia", "nvidia") # TODO: get password dynamically?
            retVal = remoteDevice.connect()
            if retVal:
                self.log_message.emit("INFO", f"[STEP 2] Identifying device type for {self.device_ip}...", 0)
                response_10 = requests.get(f'http://{self.device_ip}', timeout=5)
                strstdout_10 = '<title>WEB</title>' in response_10.text

                response_20 = requests.get(f'http://{self.device_ip}:443', timeout=5)
                strstdout_20 = '<title>WEB</title>' in response_20.text
                #self.log_message.emit("INFO", f"[SUCCESS] Device type identified (DAHUA or Other).", 0)

                self.camera_uris = {
                            "pedestrian_camera_uri": "rtsp://admin:Support01@192.168.1.10:554/cam/realmonitor?channel=1&subtype=0" if strstdout_10 else "rtsp://admin:Support01@192.168.1.10:554/Streaming/channels/1/",
                            "mobile_detection_camera_uri": "rtsp://admin:Support01@192.168.1.20:554/cam/realmonitor?channel=1&subtype=0" if strstdout_20 else "rtsp://admin:Support01@192.168.1.20:554/Streaming/channels/1/"
                        }
            #self.log_message.emit("INFO", f"[SUCCESS] Device type identified: {self.camera_uris}", 0)
            return True  

        except Exception as e:
            self.log_message.emit("INFO", f"[ERROR] Failed to identify device type: {str(e)}", 0)
            print(f"Exception: {e}")
            return False

    def prepare_local_folder(self):
        self.log_message.emit("INFO", "[STEP 3] Preparing local folder for downloads...", 0)
        local_folder = os.path.join(self.package_dir, f"remote_files_{self.device_ip.replace('.','_')}")
        if os.path.exists(local_folder):
            shutil.rmtree(local_folder)
        os.makedirs(local_folder, exist_ok=True)
        
        # if os.path.exists(local_folder):
            # print(local_folder,"Exists")
        #self.log_message.emit("INFO", "[SUCCESS] Local folder ready.", 0)
    
    def check_active_services(self, device_ip):
        self.log_message.emit("INFO", "[STEP 4] Checking active services on device...", 0)
        _, self.active_services = remote_works.check_active_services(device_ip)
        # self.active_services = [str(item) if not isinstance(item, list) else ','.join(map(str, item)) for item in self.active_services]
        self.activeServicesDict[self.device_ip] = ','.join(self.active_services)
        self.log_message.emit("INFO", f"[SUCCESS] Active services: {', '.join(self.active_services)}", 0)

    def download_files(self, device_ip: str, local_folder, camera_uris, active_services):
        
        try:        
            retVal = "FAILED"
            local_folder = os.path.join(self.package_dir, f"remote_files_{self.device_ip.replace('.','_')}")
            #print("form download_files ---->>>>",local_folder)
            retVal = remote_works.pull_camera_images_and_configs(device_ip, local_folder, camera_uris, active_services)


            if retVal == "SUCCESS":
                    self.log_message.emit("INFO", f"[DOWNLOAD CONFIGS] Active services check done - SUCCESS", 40)
    
            elif retVal == "FAILED" or len(active_services) == 0:
                CustomDialog(self, prompt_title="Config files download failed",
                                prompt_msg="No active services running or device unreachable. Retry to try again!!",
                                waiting_prompt=False).show()
                self.log_message.emit("INFO", f"[DOWNLOAD CONFIGS] Active services check done - Failed, No active services running or device unreachable. Retry to try again!!", 0)
            #self.log_message.emit("INFO", f"[DOWNLOAD CONFIGS] Fetching camera images...", 60)
                
        except Exception as e:
            print(f"Exception Error :{e}")
           
        self.log_message.emit("INFO", "[STEP 5] Downloading camera configurations and images...", 0)
        # time.sleep(2)
        self.log_message.emit("INFO", "[SUCCESS] Download complete!", 0)

    def run(self):
        with QMutexLocker(self.mutex):
            self.stopped = False
        
        if self.stopped == False:

            steps = [
                lambda: self.check_connectivity(self.device_ip),  
                self.identify_device_type, 
                self.prepare_local_folder, 
                lambda: self.check_active_services(self.device_ip),
                lambda: self.download_files(self.device_ip, self.package_dir, self.camera_uris, self.active_services)
            ]

            total_steps = len(steps)
            ret = None

            for i, step in enumerate(steps):
                try:
                    ret = step()
                    if ret == "FAILED":
                        return
                    #self.log_message.emit("INFO", f"[STEP {i + 1}] Completed step: {step.__name__}", 0)
                    #CustomDialog(self, prompt_title="Connection Failed", prompt_msg="Retry to try again!!", waiting_prompt=False).show()

                    progress_value = int(((i + 1) / total_steps) * 100)
                    # print("progress_value : ", progress_value)
                    self.progress.emit(progress_value)
        
                except Exception as e:
                    self.log_message.emit("INFO", f"[ERROR] An error occurred during step {i + 1}: {str(e)}", 0)
                    self.progress.emit(100)     
            self.stopped = True

class Worker_config(QThread):
    progress = pyqtSignal(int)
    log_message = pyqtSignal(str, str, int)

    def __init__(self, device_ip, package_dir, activeServicesDict):
        super().__init__()
        self.device_ip = device_ip
        self.package_dir = os.path.dirname(os.path.abspath(__file__))
        self.activeServicesDict = activeServicesDict

    def run(self):
        try:
            local_folder = os.path.join(self.package_dir, f"remote_files_{self.device_ip.replace('.', '_')}")
            if not os.path.exists(local_folder):
                self.log_message.emit("INFO", f"[Config] Config files not found locally, try downloading again", 0)
                return
            
            config_path = os.path.join(local_folder, 'ldms', 'config', 'app_settings.yaml')
            if not os.path.exists(config_path):
                config_path = os.path.join(local_folder, 'ldms', 'configs', 'app_settings.yaml')
            if not os.path.exists(config_path):
                config_path = os.path.join(local_folder, 'pms', 'config', 'app_settings.yaml')

            if os.path.exists(config_path):
                import platform
                if platform.system() != "Linux":
                    python_path = os.path.join(os.environ['USERPROFILE'], "AppData", "Local", "Programs", "Python", "Python38", "python.exe")
                self.log_message.emit("INFO", f"[Config] Config app initiated", 40)
                # print("[Config] Config app initiated")
                subprocess.run([python_path, os.path.join(self.package_dir, "config.py"), config_path, self.activeServicesDict.get(self.device_ip, "")])
                self.log_message.emit("INFO", f"[Config] Config app exited", 100)
            else:
                self.log_message.emit("INFO", f"[Config] app_settings.yaml file not found", 0)
        except Exception as e:
            print(f"Exception in Worker_config_dir: {e}")
            self.log_message.emit("INFO", f"[ERROR] Exception in Worker_config_dir: {e}", 0)

class Worker_smartServices(QThread):
    progress = pyqtSignal(int)
    log_message = pyqtSignal(str, str, int)
    finishedService = pyqtSignal(dict)

    def __init__(self, parent_widget, device_ip, package_dir):
        super().__init__()
        self.device_ip = device_ip
        self.package_dir = os.path.dirname(os.path.abspath(__file__))
        self.parent_widget = parent_widget
    def run(self):
        parameter = "-n" if platform.system().lower() == "windows" else "-c"
        response = subprocess.call(["ping", parameter, "1", self.device_ip])
        self.progress.emit(10)
        if response == 0:
            self.progress.emit(20)
            active_services = {"detect_mobile":False, "detect": False,"detect_ldms": False,"detect_noentry": False, "detect_rlms":False}
            self.progress.emit(30)
            l_act = remote_works.check_active_services(self.device_ip)
            # self.log_message.emit("INFO", f"[smartServices] started : {self.device_ip}", 20)
            self.progress.emit(40)
            #print("l_act--->>>....",l_act)
            for act_service in l_act[1]:
                self.progress.emit(60)
                active_services[act_service] = True
                self.progress.emit(80)
            #print("(self.active_services----->>>>....",active_services)
            # self.log_message.emit("INFO", f"[smartServices] loading : {self.device_ip}", 40)
            self.progress.emit(90)
            self.finishedService.emit(active_services)
            # self.log_message.emit("INFO", f"[smartServices] please wait : {self.device_ip}", 60)
            self.progress.emit(100)
        else:
            self.log_message.emit("ERROR", f"[REMOTE DEVICE] Device connection failed: {self.device_ip}", 0)
            self.log_message.emit("ERROR", f"[SMART SERVICE] Connection failed", 0)

# Create MainWindow class
class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        self.wd = os.getcwd()
        self.package_dir = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(os.path.join(self.package_dir,"UIFiles","configQT.ui"), self)

        # Path Settings for the application
        #if it is detect_mobile, detect, detect_noentry then use this path.
        self.app_settings_path = os.path.join(self.package_dir, 'config', 'app_settings.yaml')
        # Get handles to widgets and set callback slots
        self.setup_application()
        self.show_login_dialog()
        
        # Load app_settings.yaml
        if os.path.exists(self.app_settings_path):
            self.app_settings = load_yaml(self.app_settings_path)
        # else:
        #     disable_settings_buttons(self)

        # Display the app
        # self.show()
        self.showMaximized() 
        self.loggerObj = LoggerUtils()
        self.loggerObj.add_ui_elements_to_logger(self.statusBar, self.progressBar, self.textBrowser)

    # Get handles to widgets, set callback slots and do some basic validation
    def setup_application(self):
        self.textBrowser = self.findChild(QTextBrowser, 'textBrowser')
        self.device_lst_ui = self.findChild(QListWidget, 'devicesNameListWidget')

        # status bar
        self.statusBar = self.findChild(QStatusBar, 'statusBar') #self.statusBar()
        self.statusBar.showMessage('Ready')
        self.progressBar = QProgressBar()
        self.statusBar.addPermanentWidget(self.progressBar)
        self.statusBar.addPermanentWidget(QLabel(f"www.ktcco.net/tec/"))

        # signal - slot connect
        self.actionRestart.triggered.connect(self.restart_xavier_callback)
        self.actionConnect.triggered.connect(self.download_configs)
        self.actionConfigure.triggered.connect(self.run_config_app)
        self.actionScanDevices.triggered.connect(self.scan_for_devices)
        self.actionSoftwareFlash.triggered.connect(self.flash_device)
        self.actionAddDevice.triggered.connect(self.add_devices_ui)
        self.actionRemoveDevice.triggered.connect(self.remove_selected_listwidget_ui)
        self.actionSMART_Service_Selection.triggered.connect(self.smart_service_config)   
        self.actionSelectMultipleDevice.triggered.connect(self.select_multiple_devices_ui)
        self.actionReset_configs.triggered.connect(self.reset_last_config)

        # Theme change
        self.actionDark_Gray.triggered.connect(lambda x: self.set_theme("dark_gray"))
        self.actionDark_Blue.triggered.connect(lambda x: self.set_theme("dark_blue"))
        self.actionLight_Gray.triggered.connect(lambda x: self.set_theme("light_gray"))
        self.actionLight_Blue.triggered.connect(lambda x: self.set_theme("light_blue"))
        self.actionCustom_Color.triggered.connect(lambda x: self.set_theme("custom_color"))

        self.device_lst_ui.itemClicked.connect(self.device_selected)
        self.deviceMultiSelectMode = False
    
    def show_login_dialog(self):

        login_dialog = LoginDialog(self, self.package_dir)
        login_dialog.exec_()

    def smart_service_config(self):
        try:
            self.splash_screen = SplashScreen()
            self.splash_screen.show()
            self.device_ip = self.device_lst_ui.selectedItems()[0].text().split("-")[0].strip()
            
            self.worker_smart = Worker_smartServices(self, self.device_ip, self.package_dir)
            self.worker_smart.setParent(self)
            self.worker_smart.progress.connect(self.splash_screen.progressBarValue)
            self.worker_smart.log_message.connect(self.log_message)
            self.worker_smart.finishedService.connect(self.finishedService)
            self.worker_smart.finished.connect(self.worker_cleanup_smart)
            self.worker_smart.finished.connect(self.on_worker_finished)
            
            self.worker_smart.start()
            # self.worker_smart.finished.connect(self.closeEvent_smart)

            # print("Main Thread:", QCoreApplication.instance().thread())
            # print("Current Thread:", QThread.currentThread())
        except Exception as e:
            print(f"Failed to start application services: {e}")
            if hasattr(self, 'splash_screen') and self.splash_screen:
                self.splash_screen.close()
        # finally:
        #     if hasattr(self, 'splash_screen') and self.splash_screen:
        #         self.splash_screen.close()  
                        
    def finishedService(self, active_services):
        # active_services = {"detect_mobile":False, "detect": False,"detect_ldms": False,"detect_noentry": False, "detect_rlms":False}
        smart_services_dialog = SMARTServiceDialog(self,self.package_dir, self.device_ip, active_services)
        smart_services_dialog.exec_()
        
    def on_worker_finished(self):
        # print("Worker finished signal received.")
        self.splash_screen.close()

    def setup_worker(self):
        self.worker = Worker_smartServices()
        self.worker.stop_timer_signal.connect(self.stop_timer) 
        self.worker.start()

    def display_log_message(self, message):
        print(message)

    def worker_cleanup_smart(self):
        # print("cleanup is called from thread")
        self.worker_smart.wait()  
        self.worker_smart.deleteLater()  
        # if self.worker_smart:
        #     self.worker_smart.deleteLater()
        #     self.worker_smart = None

    def closeEvent_smart(self, event):
        # print("closeEvent is callded from thread")
        if self.worker_smart.isRunning():
            self.worker_smart.quit()  # Gracefully stop the thread
            self.worker_smart.wait()  # Wait for the thread to finish
        event.accept()

    def stop_worker_smart(self):
        # print("stop_worker_smart is called from thread")
        if self.worker_smart.isRunning():
            self.worker_smart.requestInterruption()  # Request the thread to stop
            self.worker_smart.quit()  # Quit the thread
            self.worker_smart.wait()  # Wait for the thread to finish
        
                    
    def set_theme(self, theme_str):
        global UIWindow
        if theme_str == "custom_color":
            color = QColorDialog.getColor()
            if color.isValid():
                g = QtSassTheme()
                g.getThemeFiles(theme=color.name())
                g.setThemeFiles(main_window=UIWindow)
        else:
            if UIWindow:
                g = QtSassTheme()
                g.getThemeFiles(theme=theme_str)
                g.setThemeFiles(main_window=UIWindow)

    def add_single_device_to_listwidget_ui(self, ip_address:str, sw_info:str="", hw_info:str="", product:str="", discovery_mode:str=""):
        if((self.device_lst_ui.count() == 1) and (self.device_lst_ui.item(0).text() == "No device found")):
            self.device_lst_ui.takeItem(0)

        str_vis = ""
        str_vis += ip_address
        str_vis += " - "
        str_vis += f"SW : {sw_info.upper()}"
        str_vis += " | "
        str_vis += f"HW : {hw_info.upper()}"
        str_vis += " | "
        str_vis += f"Product : {product.upper()}"
        str_vis += " | "
        str_vis += f"Discovery Mode: {discovery_mode.upper()}"


        new_device_discovered = True
        for i in range(0, self.device_lst_ui.count()):
            if ip_address in self.device_lst_ui.item(i).text(): # already existing device redetected
                new_device_discovered = False
                break

        if new_device_discovered:
            self.device_lst_ui.addItem(str_vis)
            self.log_message("INFO", f"[DEVICE ADDITION] Device list ui updated")

    def remove_selected_listwidget_ui(self):
        print(self.device_lst_ui.selectedItems())
        for dev_elem in self.device_lst_ui.selectedItems():
            # print(dev_elem.text())
            # self.device_lst_ui.removeItemWidget(dev_elem)
            self.device_lst_ui.takeItem(self.device_lst_ui.row(dev_elem))

        self.log_message("INFO", f"[DEVICE REMOVAL] Device list ui updated")
        if(self.device_lst_ui.count() == 0):
            self.device_lst_ui.addItem("No device found")

        
    def add_devices_ui(self):
        add_device_dialog = ManualDeviceAdditionDialog(self, package_dir=self.package_dir)
        if add_device_dialog.exec_() == QDialog.Accepted:
            if not add_device_dialog.csvBasedDeviceAddition: 
                # no need to validate ip address here, already verified
                self.log_message("INFO", f"[ADD DEVICE] Single device addition : {add_device_dialog.ipAddressLineEdit.text()}", 0)
                self.add_single_device_to_listwidget_ui(add_device_dialog.ipAddressLineEdit.text().strip(), add_device_dialog.swPNLineEdit.text().strip(),
                                                           add_device_dialog.hwPNLineEdit.text().strip(), add_device_dialog.productLineEdit.text().strip(), "manual_single")
                
            else:
                for device in add_device_dialog.multiAddDeviceList:
                    self.log_message("INFO", f"[ADD DEVICE] Multi device addition : {device['ip_addr']}", 0)
                    self.add_single_device_to_listwidget_ui(device['ip_addr'], device['sw_info'],
                                                            device['hw_info'], device['product_name'], "manual_multi")
    
    def select_multiple_devices_ui(self):
        if self.deviceMultiSelectMode:
            self.device_lst_ui.setSelectionMode(QAbstractItemView.SingleSelection)
            self.deviceMultiSelectMode = False
        else:
            self.device_lst_ui.setSelectionMode(QAbstractItemView.ExtendedSelection)
            self.deviceMultiSelectMode = True

    def flash_device(self):
        flash_dialog = FlashDialog(self, package_dir=self.package_dir)
        if flash_dialog.exec_() == QDialog.Accepted:
            self.log_message("INFO", f"[SW FLASH] Flash file selected: {flash_dialog.flashFilePath}", 0)
            for dev_elem in self.device_lst_ui.selectedItems():
                self.log_message("INFO", f"[SW FLASH] Initiating software flash for device {dev_elem.text()}", 1)
                # TODO: Give a non closeable prompt - may be for OS flashing
                device_ip = dev_elem.text().split("-")[0].strip()
                return_msg = remote_works.flash_sw(device_ip, flash_dialog.flashFilePath)
                self.log_message("INFO", f"[SW Flash] Flashing exited with {return_msg} status", 100)
                CustomDialog(self, prompt_title="Flash status", prompt_msg=f"Flash {return_msg}", waiting_prompt=False).show()

    # TODO: Set max lines limit and rotate the logs
    # TODO: Also write logs to some file
    # log_level : DEBUG, WARN, INFO
    def log_message(self, log_level:str="INFO", message:str="", progress_bar_level:int=None):
        self.loggerObj.log_message(log_level, message, progress_bar_level)

    def device_selected(self, item):
        self.log_message("INFO", f"[DEVICE SELECT] New device selected: {item.text()}", 0)
        if item.text() != "No device found":
            self.actionConfigure.setEnabled(True)
            self.actionRestart.setEnabled(True)
            self.actionConnect.setEnabled(True)
            self.actionReset_configs.setEnabled(True)
            self.actionSMART_Service_Selection.setEnabled(True)
            # self.actionSoftwareFlash.setEnabled(True)
        else:
            self.actionConfigure.setEnabled(False)
            self.actionRestart.setEnabled(False)
            self.actionConnect.setEnabled(False)
            self.actionReset_configs.setEnabled(False)
            self.actionSMART_Service_Selection.setEnabled(True)
            # self.actionSoftwareFlash.setEnabled(False)
            
    def clear_device_ui_list(self):
        self.device_lst_ui.clear()

    def scan_for_devices(self):
        self.actionConfigure.setEnabled(False)
        self.actionRestart.setEnabled(False)
        self.actionConnect.setEnabled(False)
        self.actionReset_configs.setEnabled(False)
        
        self.log_message("INFO", f"[DEVICE DISCOVERY] Scanning for devices initiated", 0)

        
        self.log_message("INFO", f"[DEVICE DISCOVERY] Clearing previous device list", 10)
        devices_lst = ktc_device_scanner.main()

        self.log_message("INFO", f"[DEVICE DISCOVERY] Received new device list", 80)
        if len(devices_lst) > 0:
            for device_info in devices_lst:
                self.add_single_device_to_listwidget_ui(socket.inet_ntoa(device_info.addresses[0]), (device_info.properties[b'sw_info']).decode(),
                                        (device_info.properties[b'hw_info']).decode(), (device_info.properties[b'product_name']).decode(), "autoscan")
        else:
            CustomDialog(self, prompt_title="Device discovery!", prompt_msg=f"No new device found", waiting_prompt=False).show()
            if not ((self.device_lst_ui.count() == 1) and (self.device_lst_ui.item(0).text() == "No device found")):
                self.device_lst_ui.addItem("No device found")

        self.log_message("INFO", f"[DEVICE DISCOVERY] Device list ui updated", 100)

    def reset_last_config(self):
        device_ip = self.device_lst_ui.selectedItems()[0].text().split("-")[0].strip()
        self.log_message("INFO", f"[RESET CONFIGS] Reset configs", 20)
        remote_works.reset_last_backup_config(device_ip)

        self.log_message("INFO", f"[RESET CONFIGS] Reset done remotely. Wait, deleting old config saved locally", 95)
        local_folder = os.path.join(self.package_dir, f"remote_files_{device_ip.replace('.','_')}")
        if os.path.exists(local_folder):
            shutil.rmtree(local_folder)
        self.log_message("INFO", f"[RESET CONFIGS] Config reset completed", 100)
    
    # def download_configs(self, device_ip: str):
    #     self.activeServicesDict = {}
    #     device_ip = self.device_lst_ui.selectedItems()[0].text().split("-")[0].strip()
    #     parameter = "-n" if platform.system().lower() == "windows" else "-c"
    #     response = subprocess.call(["ping", parameter, "1", device_ip])
    #     loading_screen = CustomDialog(self, prompt_title=f"Downloading file config. Please wait!!",
    #                                         prompt_msg="Downloading",
    #                                         waiting_prompt=True,
    #                                         popup_window_size=(500,0))
    #     if response == 0:  # Ping successful
    #         self.log_message("INFO", f"[DOWNLOAD CONFIGS] Ping successful: {device_ip}", 10)
            
    #         response_10 = requests.get(f'http://{device_ip}', timeout=5)
    #         strstdout_10 = '<title>WEB</title>' in response_10.text # its DAHUA if TRUE

    #         response_20 = requests.get(f'http://{device_ip}:443', timeout=5)
    #         strstdout_20 = '<title>WEB</title>' in response_20.text # its DAHUA if TRUE
            
    #         # camera_details_dialog = CameraDetailsDialog(self, package_dir=self.package_dir)
    #         # if camera_details_dialog.exec_() == QDialog.Accepted:
    #         if 1:
    #             local_folder = os.path.join(self.package_dir, f"remote_files_{device_ip.replace('.', '_')}")
    #             if os.path.exists(local_folder):
    #                 shutil.rmtree(local_folder)
    #             os.makedirs(local_folder, exist_ok=True)
    #             # camera_uris = {
    #             #     "pedestrian_camera_uri": camera_details_dialog.PEDcameraRTSPURLEdit.text(),
    #             #     "mobile_detection_camera_uri": camera_details_dialog.MOBcameraRTSPURLEdit.text()
    #             # }
    #             camera_uris = {
    #                 "pedestrian_camera_uri": "rtsp://admin:Support01@192.168.1.10:554/cam/realmonitor?channel=1&subtype=0" if strstdout_10 else "rtsp://admin:Support01@192.168.1.10:554/Streaming/channels/1/",
    #                 "mobile_detection_camera_uri": "rtsp://admin:Support01@192.168.1.20:554/cam/realmonitor?channel=1&subtype=0" if strstdout_20 else "rtsp://admin:Support01@192.168.1.20:554/Streaming/channels/1/"
    #             }
    #             loading_screen = CustomDialog(self, prompt_title=f"Downloading config. Please wait!!",
    #                                         prompt_msg="Downloading",
    #                                         waiting_prompt=True,
    #                                         popup_window_size=(500,0))
    #             loading_screen.show()
    #             self.log_message("INFO", f"[DOWNLOAD CONFIGS] Initiating.. checking services", 20)
    #             retVal, active_services = remote_works.check_active_services(device_ip)
    #             self.activeServicesDict[device_ip] = ','.join(active_services)
    #             self.log_message("INFO", f"[DOWNLOAD CONFIGS] Active services check done", 30)
    #             #print(self.activeServicesDict[device_ip])
    #             if retVal == "SUCCESS":
    #                 self.log_message("INFO", f"[DOWNLOAD CONFIGS] Active services check done - SUCCESS", 40)
    
    #             elif retVal == "FAILED" or len(active_services) == 0:
    #                 loading_screen.accept()
    #                 CustomDialog(self, prompt_title="Config files download failed",
    #                                 prompt_msg="No active services running or device unreachable. Retry to try again!!",
    #                                 waiting_prompt=False).show()
    #                 self.log_message("INFO", f"[DOWNLOAD CONFIGS] Active services check done - Failed, No active services running or device unreachable. Retry to try again!!", 0)
    #                 return
    #             self.log_message("INFO", f"[DOWNLOAD CONFIGS] Fetching camera images...", 60)
    #             retVal = remote_works.pull_camera_images_and_configs(device_ip, local_folder, camera_uris, active_services)
    #             self.log_message("INFO", f"[DOWNLOAD CONFIGS] Fetching camera images done", 70)
    #             loading_screen.accept()
    #             if retVal == ("SUCCESS", active_services):
    #                 CustomDialog(self, prompt_title="Config files download successful",
    #                                 prompt_msg="Configurations and camera images fetched successfully.",
    #                                 waiting_prompt=False).show()
    #                 self.log_message("INFO", f"[DOWNLOAD CONFIGS] Fetching camera images done - SUCCESS", 100)
    #             else:
    #                 loading_screen.accept()
    #                 CustomDialog(self, prompt_title="Config files download failed",
    #                                 prompt_msg="Maybe app_settings.yaml file not found on device or camera images failed to fetch, or device unreachable. Retry to try again!!",
    #                                 waiting_prompt=False).show()
    #                 self.log_message("INFO", f"[DOWNLOAD CONFIGS] Fetching camera images done - Failed", 0)
    #     else:
    #         loading_screen.accept()
    #         self.log_message("ERROR", f"[REMOTE DEVICE] Device connection failed: {device_ip}", 0)
    #         CustomDialog(self, prompt_title="Device connection failed",
    #                         prompt_msg="Failed to connect. Please check network or device status.", waiting_prompt=False).show()
    #         self.log_message("ERROR", f"[DOWNLOAD CONFIGS] Connection failed", 0)

    def download_configs(self, clicked_value):
        try:
            # Show SplashScreen
            self.splash_screen = SplashScreen()
            self.splash_screen.show()

            device_ip = self.device_lst_ui.selectedItems()[0].text().split("-")[0].strip()
            self.activeServicesDict = {}
            self.camera_uris = {}

            # Initialize Worker (QThread or similar)
            self.worker = Worker(device_ip, self.package_dir)
            self.worker.setParent(self)  # Optional: Set parent to manage lifecycle

            # Connect progress updates from worker to splash screen
            self.worker.progress.connect(self.splash_screen.progressBarValue)

            # Handle log messages from the worker
            self.worker.log_message.connect(self.log_message)

            # When the worker finishes, close the splash screen
            self.worker.finished.connect(self.splash_screen.close)

            # Clean up the worker thread after completion
            self.worker.finished.connect(self.worker_cleanup)

            # Start the worker thread
            self.worker.start()

        except Exception as e:
            # Handle exceptions and close the splash screen if it was started
            print(f"Failed to start download configurations: {e}")
            if hasattr(self, 'splash_screen') and self.splash_screen:
                self.splash_screen.close()



    # def update_progress(self, value):
    #     print(f"Progress: {value}%")

    def display_log_message(self, message):
        print(message)

    def worker_cleanup(self):
        # self.worker.wait()  # Ensure the thread finishes
        # self.worker.deleteLater()  # Clean up the thread
        if self.worker:
            self.activeServicesDict = self.worker.activeServicesDict
            #print(self.activeServicesDict)
            self.worker.deleteLater()
            self.worker = None
    def stop_worker(self):
        if self.worker.isRunning():
            self.worker.requestInterruption()  # Request the thread to stop
            self.worker.quit()  # Quit the thread
            self.worker.wait()  # Wait for the thread to finish
        

    # def run_config_app(self):
        # device_ip = self.device_lst_ui.selectedItems()[0].text().split("-")[0].strip()
        # local_folder = os.path.join(self.package_dir, f"remote_files_{device_ip.replace('.','_')}")
        # if not os.path.exists(local_folder):
        #     CustomDialog(self, prompt_title="Download configurations again", prompt_msg=f"Config files not found locally, try downloading again", waiting_prompt=False).show()
        #     self.log_message("INFO", f"[Config] Config files not found locally, try downloading again", 0)
        #     return
        # # os.makedirs(local_folder, exist_ok=True)
        # self.log_message("INFO", f"[Config] Initiating config app. Please wait, loading.......")
        # try:
        #     config_path = os.path.join(local_folder, 'ldms', 'config','app_settings.yaml')
            
        #     if (not os.path.exists(config_path)):
        #         config_path = os.path.join(local_folder, 'ldms', 'configs','app_settings.yaml')
            
        #     if (not os.path.exists(config_path)):
        #         #print("------------->>>>>>>>>",local_folder)
        #         config_path = os.path.join(local_folder, 'pms', 'config', 'app_settings.yaml')
                    
        #     if os.path.exists(config_path):
        #         import platform
        #         if platform.system() != "Linux":
        #             python_path = os.path.join(os.environ['USERPROFILE'],"AppData", "Local", "Programs", "Python", "Python38", "python.exe")
                    
        #         self.log_message("INFO", f"[Config] Config app initiated", 100)
        #         print("[Config] Config app initiated")
        #         subprocess.run([python_path, os.path.join(self.package_dir, "config.py"), config_path, self.activeServicesDict[device_ip]])
        #         self.log_message("INFO", f"[Config] Config app exited", 100)
        #     else:
        #         CustomDialog(self, prompt_title="Config application open error!", prompt_msg=f"May be app_settings.yaml file not found in device or device unreachable", waiting_prompt=False).show()
        #         self.log_message("INFO", f"[Config] May be app_settings.yaml not downloaded or file not found in device or device unreachable", 0)

        # except Exception  as e:
        #     print(e)

    def run_config_app(self):
        try:
            # Show SplashScreen
            self.splash_screen = SplashScreen()
            self.splash_screen.show()

            # self.active = self.download_configs.activeServicesDict

            self.device_ip = self.device_lst_ui.selectedItems()[0].text().split("-")[0].strip()
            
            self.worker_config = Worker_config(self.device_ip, self.package_dir, self.activeServicesDict)
            self.worker_config.setParent(self) 
            # print("from run_config_app opening config---->>>>", self.activeServicesDict)

            self.worker_config.progress.connect(self.splash_screen.progressBarValue)

            self.worker_config.log_message.connect(self.log_message)

            self.worker_config.finished.connect(self.splash_screen.close)

            self.worker_config.finished.connect(self.worker_cleanup_config)

            self.worker_config.start()

        except Exception as e:
            # Handle exceptions and close the splash screen if it was started
            print(f"Failed to start config application: {e}")
            if hasattr(self, 'splash_screen') and self.splash_screen:
                self.splash_screen.close()

    def display_log_message(self, message):
        print(message)

    def worker_cleanup_config(self):
        self.worker_config.wait()  # Ensure the thread finishes
        self.worker_config.deleteLater()  # Clean up the thread
        # if self.worker_config:
        #     self.Worker_config.deleteLater()
        #     self.Worker_config = None

    def closeEvent_config(self, event):
        if self.Worker_config.isRunning():
            self.Worker_config.quit()  # Gracefully stop the thread
            self.Worker_config.wait()  # Wait for the thread to finish
        event.accept()
    def stop_worker_config(self):
        if self.Worker_config.isRunning():
            self.Worker_config.requestInterruption()  # Request the thread to stop
            self.Worker_config.quit()  # Quit the thread
            self.Worker_config.wait()  # Wait for the thread to finish
        



    # Call back for run config button
    def run_config_app_old(self):
        camera_details_dialog = CameraDetailsDialog(self, package_dir=self.package_dir)
        if camera_details_dialog.exec_() == QDialog.Accepted:
            # print(camera_details_dialog.camera_uri)
            device_ip = self.device_lst_ui.selectedItems()[0].text().split("-")[0].strip()
            local_folder = os.path.join(self.package_dir, f"remote_files_{device_ip.replace('.','_')}")
            os.makedirs(local_folder, exist_ok=True)
            self.log_message("INFO", f"[Config] Initiating config app. Please wait, loading.......")
            # print({"pedestrian_camera_uri": camera_details_dialog.PEDcameraRTSPURLEdit.text(), "mobile_detection_camera_uri": camera_details_dialog.MOBcameraRTSPURLEdit.text()})
            remote_works.pull_camera_images_and_dms_configs(device_ip, local_folder, {"pedestrian_camera_uri": camera_details_dialog.PEDcameraRTSPURLEdit.text(), "mobile_detection_camera_uri": camera_details_dialog.MOBcameraRTSPURLEdit.text()}) # pass camera rtsp url
            try:
                #config_path = os.path.join(local_folder, 'user_configs','app_settings.yaml')
                if (not os.path.exists(config_path)):
                    config_path = os.path.join(local_folder, 'config', 'app_settings.yaml')
                        
                if os.path.exists(config_path):
                    # config.main(config_path) # pass camera
                    # p1 = multiprocessing.Process(target=config.main, args=(config_path,))
                    # p1 = threading.Thread(target=config.main, args=(config_path,))
                    # p1.start()

                    # from kivy.clock import Clock
                    # Clock.schedule_once(lambda x: threading.Thread(target=config.main, args=(config_path,)).start())
                    # best way to call kivy apps from qt apps (couldnt close neatly and reopen again with above methods of instantiating)
                    python_path = os.path.join(os.environ['USERPROFILE'],"AppData", "Local", "Programs", "Python", "Python38", "python.exe")
                    import platform
                    if platform.system() == "Linux":
                        python_path = "python"
                        
                    subprocess.run([python_path, os.path.join(self.package_dir, "config.py"), config_path])
                    self.log_message("INFO", f"[Config] Config app exited", 90)
                else:
                    CustomDialog(self, prompt_title="Config application open error!", prompt_msg=f"May be app_settings.yaml file not found in device or device unreachable", waiting_prompt=False).show()
                    self.log_message("INFO", f"[Config] May be app_settings.yaml file not found in device or device unreachable", 90)

            except Exception  as e:
                print(e)

            # remove local folder created
            if os.path.exists(local_folder):
               self.log_message("INFO", f"[Config] Removing temporary local directory", 100)
               shutil.rmtree(local_folder)

    # Save YAML
    def save_settings(self):
        with open(self.app_settings_path, "w") as f:
            yaml.dump(self.app_settings, f)

    # Call back for setcam1 button
    def setcam1_btn_callback(self):
        newip = self.setcam1_edit.text()
        self.setcam_ip(0, newip)
        
    # Call back for setcam2 button
    def setcam2_btn_callback(self):
        newip = self.setcam2_edit.text()
        self.setcam_ip(1, newip)

    # Func for settings camera in yaml
    # camid defines which camera is it, PED or Mobi
    # camid: Mobi = 1, Ped = 2 (anpr)
    def setcam_ip(self, camid, newip):
        self.app_settings["VIDEO_SOURCE"][self.list_cam[camid]]["IPCAM"]["IP"] = newip
        self.save_settings()

    # send config folder to Xavier PC using Paramiko Lib
    # def sendfiles_btn_callback(self):
    #     send_files_to_xavier(self)
    
    # Get config folder from Xavier PC using Paramiko Lib
    # def getfiles_btn_callback(self):
    #     get_files_from_xavier(self)
    #     # Load app_settings.yaml copied from xavier
    #     self.app_settings = load_yaml(self.app_settings_path)
    #     #Enable buttons for app_settings.yaml
    #     enable_settings_buttons(self)
    #     update_UI(self)

    def restart_xavier_callback(self):
        device_ip = self.device_lst_ui.selectedItems()[0].text().split("-")[0].strip()
        self.log_message("INFO", f"[RESTART DEVICE] Restarting device {device_ip}.......", 20)
        retVal = remote_works.restart_device(device_ip)
        if retVal == "SUCCESS":
            CustomDialog(self, prompt_title="DEVICE RESTART", prompt_msg=f"Device restarted remotely", waiting_prompt=False).show()
            self.log_message("INFO", f"[RESTART DEVICE] Device restarted remotely {device_ip}", 100)
        else:
            CustomDialog(self, prompt_title="DEVICE RESTART FAILED", prompt_msg=f"Device restart failed", waiting_prompt=False).show()
            self.log_message("INFO", f"[RESTART DEVICE] Failed device restart {device_ip}", 0)

# Get app object
app = QApplication(sys.argv)

# Get UI object which we inherit from Qmainwindow
UIWindow = UI()

# Start the application
sys.exit(app.exec_())