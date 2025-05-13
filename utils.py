import yaml, sys, paramiko, os
from pathlib import Path
from SFTPClient import MySFTPClient

# Return a multidimensional array called settings
# for access use this syntax, e.g. settings['Tag1']['Tag2']
def load_yaml(filepath):   
    settings = None
    if Path(filepath).is_file():
        with open(filepath) as f:
            settings = yaml.safe_load(f)
            
    else:
        print(f'Settings file not found in {filepath}')
        
    return settings

# if __name__ == "__main__": #
#     yaml_file_path = '../config/settings.yaml' # Load the YAML file 
#     config_data = load_yaml(yaml_file_path) # Print the loaded configuration 
#     if config_data: 
#         print(config_data) 
#     else: 
#         print("No settings loaded.")
# def send_files_to_xavier(UIobject):
#     xavier_ip = UIobject.setxavierip_edit.text()
#     UIobject.dialog_box.show()
#     try:
#         # Provide (IP, Port) to paramiko.Transport e.g. (127.0.0.1, 22)
#         transport = paramiko.Transport((xavier_ip, 22))
#         transport.connect(username='nvidia', password='nvidia')
#         sftp = MySFTPClient.from_transport(transport)
#         src = os.path.join(UIobject.package_dir,"config")
#         # dst = UIobject.xavier_settings['PATHS']['XAVIERPATH']
#         dst = UIobject.setxavierpath_edit.text()
#         sftp.mkdir(dst, ignore_existing=True)
#         sftp.put_dir(src, dst)
#         sftp.close()
#         UIobject.dialog_box.message.setText("Files were successfully copied!")
#         UIobject.dialog_box.buttonBox.setEnabled(True)
#         UIobject.dialog_box.exec()
#         UIobject.restart_btn.setEnabled(True)
#         UIobject.restart_btn.setStyleSheet("background-color : Green")
        
#     except:
#         UIobject.dialog_box.message.setText("Could not make connection with Xavier, Please check path and IP")
#         UIobject.dialog_box.buttonBox.setEnabled(True)
#         UIobject.dialog_box.exec()

# def get_files_from_xavier(UIobject):
#     xavier_ip = UIobject.setxavierip_edit.text()
#     try:
#         # Provide (IP, Port) to paramiko.Transport e.g. (127.0.0.1, 22)
#         transport = paramiko.Transport((xavier_ip, 22))
#         transport.connect(username='nvidia', password='nvidia')
#         sftp = MySFTPClient.from_transport(transport)
#         # src = UIobject.xavier_settings['PATHS']['XAVIERPATH']
#         src = UIobject.setxavierpath_edit.text()
#         dst = os.path.join(UIobject.package_dir, "config")
        
#         if not os.path.exists(dst):
#             os.mkdir(dst)
            
#         sftp.get_dir(src, dst)
#         sftp.close()
#         UIobject.dialog_box.message.setText("Files were successfully copied!")
#         UIobject.dialog_box.buttonBox.setEnabled(True)
#         UIobject.dialog_box.exec()
        
#     except:
#         UIobject.dialog_box.message.setText("Could not make connection with Xavier, Please check path and IP")
#         UIobject.dialog_box.buttonBox.setEnabled(True)
#         UIobject.dialog_box.exec()

# def disable_settings_buttons(UIobject):
#     UIobject.setcam1_btn.setEnabled(False)
#     UIobject.setcam2_btn.setEnabled(False)
#     UIobject.runConfigAppBtn.setEnabled(False)

# def enable_settings_buttons(UIobject):
#     UIobject.setcam1_btn.setEnabled(True)
#     UIobject.setcam2_btn.setEnabled(True)
#     UIobject.runConfigAppBtn.setEnabled(True)

# def update_UI(UIobject):
#     UIobject.setcam1_edit.setText(UIobject.app_settings["VIDEO_SOURCE"]["MOBI"]["IPCAM"]["IP"])
#     UIobject.setcam2_edit.setText(UIobject.app_settings["VIDEO_SOURCE"]["PED"]["IPCAM"]["IP"])

# def restart_xavier(UIobject):
#     # Create object of SSHClient and
#     # connecting to SSH
#     ssh = paramiko.SSHClient()
    
#     # Adding new host key to the local
#     # HostKeys object(in case of missing)
#     # AutoAddPolicy for missing host key to be set before connection setup.
#     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
#     ssh.connect(UIobject.setxavierip_edit.text(), port=22, username='nvidia',
#                 password='nvidia', timeout=3)
    
#     # Execute command on SSH terminal
#     # using exec_command
#     stdin, stdout, stderr = ssh.exec_command("sudo -S reboot")
#     stdin.write("nvidia\n")
#     stdin.flush()
#     UIobject.dialog_box.message.setText("Xavier Restarted")
#     UIobject.dialog_box.buttonBox.setEnabled(True)
#     UIobject.dialog_box.exec()
#     # print("---------------------------------------------")
#     # # print(stdin.readlines())
#     # print("---------------------------------------------")
#     # print(stdout.readlines())
#     # print("---------------------------------------------")
#     # print(stderr.readlines())
#     # print("---------------------------------------------")