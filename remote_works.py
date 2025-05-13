import os
# import paramiko
# from scp import SCPClient
# import random
import shutil
from remote_device import RemoteDevice
from time import sleep
import subprocess
import time
import logging
from datetime import datetime

from PyQt5.QtTest import QTest

# TODO: flash KTC related SW as well or we can give a KFL file for that. This process heavily depends on SSH. Find an alternative to use low level ways like UDP/TCP
def flash_sw(device_ip:str, flash_file_path:str):
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia") # TODO: get password dynamically?
    if remoteDevice.connect():
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Device connected successfully : {device_ip}", 20)

        remoteDevice.createTmpFolder()
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Temp folder creation done")

        remote_file_path = os.path.join(remoteDevice.tmp_folder_path, os.path.basename(flash_file_path)).replace("\\","/")
        remoteDevice.send_file(flash_file_path, remote_file_path)
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Flash file copied successfully at {remote_file_path}", 30)
        
        remoteDevice.exec_cmd(f"mv {os.path.splitext(remote_file_path)[0]}.kfl {os.path.splitext(remote_file_path)[0]}.tar.gz")

        remoteDevice.exec_cmd(f"tar -xzvf {os.path.splitext(remote_file_path)[0]}.tar.gz -C {remoteDevice.tmp_folder_path}")
        
        sw_dir = os.path.join(os.path.splitext(remote_file_path)[0], "sw").replace("\\","/")
        _, str_stdout, str_stderr = remoteDevice.exec_cmd(f"bash {os.path.splitext(remote_file_path)[0]}/install.sh -d {sw_dir}")

        remoteDevice.disconnect()

        if "installation successful" in str_stdout:
            remoteDevice.log_message("INFO", f"[REMOTE DEVICE] SW flash successfully completed", 90)
            return "SUCCESS"
        
    return "FAILED"

def just_connect(device_ip:str):
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia")
    retVal = remoteDevice.connect(enable_scp=False)
    return retVal, remoteDevice

def reset_last_backup_config(device_ip:str):
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia") # TODO: get password dynamically?
    retVal = remoteDevice.connect()
    if retVal:
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Device connected successfully : {device_ip}", 20)

        remoteDevice.exec_cmd(f"if [ -d /srv/pms/detect/config.$(date +%Y%m%d) ]; then echo \"backup found\"; fi ")
        remoteDevice.exec_cmd(f"if [ -d /srv/pms/detect/config_ldms.$(date +%Y%m%d) ]; then echo \"backup found\"; fi ")

        remoteDevice.exec_cmd(f"if [ -d /srv/pms/detect/config.$(date +%Y%m%d) ]; then rm -r /srv/pms/detect/config && cp -r /srv/pms/detect/config.$(date +%Y%m%d) /srv/pms/detect/config; fi ")
        remoteDevice.exec_cmd(f"if [ -d /srv/pms/detect/config_ldms.$(date +%Y%m%d) ]; then rm -r /srv/pms/detect/config_ldms && cp -r /srv/pms/detect/config_ldms.$(date +%Y%m%d) /srv/pms/detect/config_ldms; fi ")
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] RESET COMMANDS EXECUTED", 90)

def check_active_services(device_ip: str):
    active_services = []
    retVal_Status = "FAILED"
    services = ["detect_mobile", "detect", "detect_ldms", "detect_noentry", "detect_rlms"]
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia")
    retVal = remoteDevice.connect()
    #print(retVal)
    if retVal:
        try:
            for service in services:
                _, _stdout, _stderr = remoteDevice.exec_cmd(f"systemctl status {service}")
                print(_stdout, _stderr)
                status = _stdout.strip()
                if 'active (running)' in status.lower() and 'enabled' in status.lower():
                    active_services.append(service)
            
            if active_services:
                retVal_Status = "SUCCESS"
        
        except Exception as e:
            print(f"Something happened while checking services: {e}")
    
    print("Active Services:", active_services)

    # if success, set retVal_Status to "SUCCESS" before returning, or else values will be ignored
    return retVal_Status, active_services
def check_active_services_part2(device_ip: str):
    active_services = []
    services = ["detect_mobile", "detect", "detect_ldms", "detect_noentry", "detect_rlms"]
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia")
    retVal = remoteDevice.connect()
    #print(retVal)
    if retVal:
        try:
            for service in services:
                _, _stdout, _stderr = remoteDevice.exec_cmd(f"systemctl status {service}")
                status = _stdout.strip()
                if 'active (running)' in status.lower() and 'enabled' in status.lower():
                    active_services.append(service)
                            
        except Exception as e:
            print(f"Something happened while checking services: {e}")
    
    # print("Active Services:", active_services)
    return {"retrievedActiveServices": active_services}

def Inactive_services(device_ip: str, active_services):
    # remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia")
    # retVal = remoteDevice.connect()
    # if retVal:
    services = ["detect_mobile", "detect", "detect_ldms", "detect_noentry", "detect_rlms"]
    print("Active Services:", active_services)
    inactive_services = {key: value for key, value in active_services.items() if not value}
    print("Inactive Services:", inactive_services)
    return {"retrievedInactiveServices": inactive_services}

def pull_camera_images_and_configs(device_ip:str, local_folder_path:str, rtsp_uri:dict, active_services:list):
    retVal = "FAILED"
    pull_camera_images(device_ip, local_folder_path, rtsp_uri)

    # if service is active, call respective download
    for active_ser in active_services:
        if (("detect_ldms" in active_ser) or ("detect_ldms" in active_ser and "detect_mobile" in active_ser)): 
            retVal = pull_ldms_configs(device_ip, local_folder_path)
        
        # and / or
        elif "detect_mobile" in active_ser or "detect" in active_ser or "detect_noentry" in active_ser:
            retVal = pull_dms_configs(device_ip, local_folder_path)

    return retVal,active_services

def pull_ldms_configs(device_ip:str, local_folder_path:str):
    # same like dms download code, but just download dms zones and configs
    # print("I'm here in pull camera images and ldms configs")
    # print("printing from pull camera images and ldms config ",pull_camera_images_and_configs)
    finalReturnValue = "SUCCESS"
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia") # TODO: get password dynamically?
    retVal = remoteDevice.connect()
    if retVal:
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Device connected successfully : {device_ip}", 20)
        #print("I'm here in pull camera images and ldms configs -->1")
        remoteDevice.createTmpFolder()
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Temp folder creation done")
        try:
            # for active_se in active_services:
                # print("****** *********", active_se ,"********* **********")
                # if 'detect_ldms' in active_se and 'detect_mobile' in active_se:
                # remoteDevice.recv_file(local_folder_path, "/srv/pms/detect/config/app_settings.yaml")
                # remoteDevice.recv_file(local_folder_path, "/srv/pms/detect/config/zones_mobile.txt")
                # remoteDevice.recv_file(local_folder_path, "/srv/pms/detect/config/zones_ped.txt")
            _, str_stdout, _ = remoteDevice.exec_cmd(f"ls /srv/")
            # print("I'm here in pull camera images and ldms configs -->1")
            os.makedirs(os.path.join(local_folder_path, "ldms"), exist_ok=True)

            if "configs" in str_stdout:
                remoteDevice.recv_file(os.path.join(local_folder_path, "ldms", "configs"), "/srv/configs")
            else:
                # Check for the "config" directory in /srv/ldms/detect/
                _, str_stdout, _ = remoteDevice.exec_cmd("ls /srv/ldms/detect/")
                
                if "config" in str_stdout:
                    remoteDevice.recv_file(os.path.join(local_folder_path, "ldms", "config"), "/srv/ldms/detect/config")
                    print("Config file found in /srv/ldms/detect/config")
                else:
                    print("Config file not found in either location.")

        except Exception as e:
            print("Exited receiving file with exception: ", e)

        remoteDevice.disconnect()
        
    return finalReturnValue
                   
def pull_camera_images(device_ip:str, local_folder_path:str, rtsp_uri:dict):
    finalReturnValue = "SUCCESS"
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia") # TODO: get password dynamically?
    retVal = remoteDevice.connect()
    if retVal:
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Device connected successfully : {device_ip}", 20)

        remoteDevice.createTmpFolder()
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Temp folder creation done")

        remote_camera_images_folder = os.path.join(remoteDevice.tmp_folder_path, 'CameraImages').replace('\\','/')
        remoteDevice.exec_cmd(f"mkdir -p {remote_camera_images_folder}")
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] CameraImages folder creation done")

        try:
            # print(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=\"{rtsp_uri["pedestrian_camera_uri"]}\" ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/pedestrian_camera_uri.jpg max-files=1")
            _, str_stdout, str_stderr = remoteDevice.exec_cmd(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=\"{rtsp_uri['pedestrian_camera_uri']}\" ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/pedestrian_camera_uri.jpg max-files=1", timeout=5)
            # str_stdout, str_stderr = remoteDevice.exec_cmd(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=\"{v}\" ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/{k}.jpg max-files=1", timeout=10)
            #str_stdout, str_stderr = remoteDevice.exec_cmd(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=file:///home/nvidia/ped_violation.mp4 ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/out.jpg max-files=1", timeout=10)
            # str_stdout, str_stderr = remoteDevice.exec_cmd(f"cp /home/nvidia/1.png {remote_camera_images_folder}/out.png", timeout=10)
            # print(str_stdout, str_stderr)
            # sleep(2)
        except Exception as e:
            print("Exited gst pipeline with exception: ", e) # Nothing to worry

        try:
            # print(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=\"{rtsp_uri["pedestrian_camera_uri"]}\" ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/pedestrian_camera_uri.jpg max-files=1")
            _, str_stdout, str_stderr = remoteDevice.exec_cmd(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=\"{rtsp_uri['mobile_detection_camera_uri']}\" ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/mobile_detection_camera_uri.jpg max-files=1", timeout=5)
            # str_stdout, str_stderr = remoteDevice.exec_cmd(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=\"{v}\" ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/{k}.jpg max-files=1", timeout=10)
            #str_stdout, str_stderr = remoteDevice.exec_cmd(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=file:///home/nvidia/ped_violation.mp4 ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/out.jpg max-files=1", timeout=10)
            # str_stdout, str_stderr = remoteDevice.exec_cmd(f"cp /home/nvidia/1.png {remote_camera_images_folder}/out.png", timeout=10)
            # print(str_stdout, str_stderr)
            # sleep(2)
        except Exception as e:
            print("Exited gst pipeline with exception: ", e) # Nothing to worry

        try:
            _, str_stdout, str_stderr = remoteDevice.exec_cmd(f"ls {remote_camera_images_folder}/*")
            if len(str_stdout) > 3:
                remoteDevice.recv_file(local_folder_path, remote_camera_images_folder)
                remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Remote file copied successfully at {local_folder_path}", 30)
            else:
                finalReturnValue = "FAILED"
        except Exception as e:
            print("Exited receiving file with exception: ", e)

        remoteDevice.disconnect()
        
    return finalReturnValue


def pull_dms_configs(device_ip:str, local_folder_path:str):
    finalReturnValue = "SUCCESS"
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia") # TODO: get password dynamically?
    retVal = remoteDevice.connect()
    if retVal:
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Device connected successfully : {device_ip}", 20)

        remoteDevice.createTmpFolder()
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Temp folder creation done")

        try:
            _, str_stdout, str_stderr = remoteDevice.exec_cmd(f"ls /srv/pms/detect")
            # os.makedirs(os.path.join(local_folder_path, "pms", "config"), exist_ok=True)
            os.makedirs(os.path.join(local_folder_path, "pms"), exist_ok=True)
            if "config" in str_stdout:
                # print("from here in pull_dms_configs")
                remoteDevice.recv_file(os.path.join(local_folder_path, "pms"), "/srv/pms/detect/config")

        except Exception as e:
            print("Exited receiving file with exception: ", e)

        remoteDevice.disconnect()
        
    return finalReturnValue

def restart_device(device_ip:str):
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia") # TODO: get password dynamically?
    retVal = remoteDevice.connect(enable_scp=False)
    if retVal:
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Device connected successfully : {device_ip}", 20)
        stdin, _, _ = remoteDevice.exec_cmd(f"sudo -S reboot", 5)
        stdin.write("nvidia\n")
        stdin.flush()
        return "SUCCESS"
    return "FAILED"

def save_dms_configs(device_ip: str, local_folder_path: str, dms_types: str,change_details) :
    print("save dms ", local_folder_path)
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia")  # TODO: get password dynamically?
    retVal = remoteDevice.connect()
    if retVal:
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Device connected successfully : {device_ip}", 20)
        remoteDevice.createTmpFolder()
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Temp folder creation done")
        current_date = datetime.now().strftime('%Y-%m-%d')
        for folder in os.listdir(local_folder_path):
            if folder in ['ldms', 'pms']:
                print("Folders--->>>>>>>>>>>>>>>>>>.....", folder)
                remoteDevice.send_file(os.path.join(local_folder_path, folder), f"{remoteDevice.tmp_folder_path}")
        
                srv_path = f"/srv/{folder}/detect"
                print("srv_path", srv_path)
                special_ldms = False
                _, str_stdout, str_stderr = remoteDevice.exec_cmd(f"ls -R {srv_path}")

                if "app_settings.yaml" not in str_stdout and folder == "ldms":
                    srv_path_to = "/srv/"
                    special_ldms = True
                    if special_ldms:
                        _, str_stdout, str_stderr = remoteDevice.exec_cmd(f"ls /home/nvidia/pms")
                        remoteDevice.exec_cmd(f"if [ ! -d {srv_path_to}/configs.$(date +%Y%m%d) ]; then mkdir -p /home/nvidia/pms/archive/{current_date}/configs.$(date +%Y%m%d) && cp -r {srv_path_to}/configs/. /home/nvidia/pms/archive/{current_date}/configs.$(date +%Y%m%d); fi", 10)
                    
                elif "config" in str_stdout:
                # else:
                    if folder=='ldms':
                        print("*********folder = = = = ldMS****************** ", srv_path)
                        remoteDevice.exec_cmd(f"if [ ! -d {srv_path}/config.$(date +%Y%m%d) ]; then cp -r {srv_path}/config {srv_path}/config.$(date +%Y%m%d); fi")
                    elif folder=='pms':
                    # if folder == 'pms':
                        print("*********folder = = = = PMS****************** ", srv_path)
                        print("SRV path", srv_path)
                        remoteDevice.exec_cmd(f"if [ ! -d {srv_path}/config.$(date +%Y%m%d) ]; then cp -r {srv_path}/config {srv_path}/config.$(date +%Y%m%d); fi")


                _, str_stdout, str_stderr = remoteDevice.exec_cmd(f"ls {remoteDevice.tmp_folder_path}")
                if "ldms" in str_stdout or "pms" in str_stdout:
                    if special_ldms:
                        remoteDevice.exec_cmd(f"cp -r {remoteDevice.tmp_folder_path}/{folder}/configs {srv_path_to}/.")
                    else:
                        remoteDevice.exec_cmd(f"cp -r {remoteDevice.tmp_folder_path}/{folder}/config {srv_path}/.")
                
                remoteDevice.log_message("INFO", "[REMOTE DEVICE] Configs folder copy done")

                try:
                    _, config_str_stdout, config_str_stderr = remoteDevice.exec_cmd(f"ls {srv_path}/config")
                    if folder == "pms":
                        if "zones_ped.txt" in config_str_stdout and "zones_mobile.txt" in config_str_stdout:
                            time.sleep(10)
                            send_change_to_remote_pms(device_ip, local_folder_path)
                            remoteDevice.log_message("INFO", "[REMOTE DEVICE] PMS Zone file copied successfully", 30)
                        else:
                            print("not saved pms zones file")
                            return "FAILED"
                    elif folder == "ldms":
                        if "zones_ldms.txt" in config_str_stdout:
                            time.sleep(10)
                            send_change_to_remote_ldms( device_ip, local_folder_path)
                            remoteDevice.log_message("INFO", "[REMOTE DEVICE] LDMS Zone file copied successfully", 30)
                        elif special_ldms:
                            time.sleep(10)
                            _, config_str_stdout, config_str_stderr = remoteDevice.exec_cmd(f"ls {srv_path_to}/configs")
                            if "zones_ldms.txt" in config_str_stdout:
                                send_change_to_remote_ldms(device_ip, local_folder_path)
                                remoteDevice.log_message("INFO", "[REMOTE DEVICE] LDMS Zone file copied successfully", 30)
                            else:
                                print("not saved ldms zones file")
                                return "FAILED"
                        else:
                            remoteDevice.log_message("INFO", "[REMOTE DEVICE] LDMS Zone file copied successfully", 30)
                    if "app_settings.yaml" in config_str_stdout:
                        remoteDevice.log_message("INFO", "[REMOTE DEVICE] app_settings.yaml file copied successfully", 30)
                    else:
                        remoteDevice.log_message("INFO", "[REMOTE DEVICE] app_settings.yaml file copy unsuccessful", 30)
                        return "FAILED"
                        
                except Exception as e:
                    print(f"Exception occurred: {e}")
                    return "FAILED"
        
        remoteDevice.disconnect()

        return "SUCCESS"
    else:
        remoteDevice.log_message("ERROR", f"[REMOTE DEVICE] Failed to connect to device : {device_ip}")
        return "FAILED" 

def ensure_remote_folder(device, path):
    _, stdout, _ = device.exec_cmd(f"ls {path}")
    if path not in stdout:
        device.exec_cmd(f"mkdir -p {path}")
# def ensure_remote_log(remoteDevice, remote_log_path):
#     _, str_stdout, _ = remoteDevice.exec_cmd(f"ls {remote_log_path}")
#     if not remote_log_path in str_stdout:
#         remoteDevice.exec_cmd(f'touch {remote_log_path}')
        
# def send_change_to_remote(device_ip, local_folder_path):
#     remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia")
#     retVal = remoteDevice.connect()
#     current_date = datetime.now().strftime('%Y-%m-%d')
#     remote_path = f'/home/nvidia/pms/TechApp/{current_date}'
#     if retVal:
#         for folder in os.listdir(local_folder_path):
#             if folder in ['ldms', 'pms']:
#                 try:
#                     srv_path = f"/srv/{folder}/detect"
#                     ensure_remote_folder(remoteDevice, remote_path)
#                     _, config_str_stdout, _ = remoteDevice.exec_cmd(f"ls -R /srv/")
#                     #_, config_str_stdout1, _ = remoteDevice.exec_cmd(f"ls /srv/pms/detect")
#                     if 'configs' in config_str_stdout:
#                         print("In LDMS_V2 file comparison!!!")
#                         remoteDevice.exec_cmd(f"git diff /home/nvidia/pms/acrhive/{current_date}/configs.$(date +%Y%m%d) /srv/configs > {remote_path}/LDMS_Configs_{current_date}.txt")
#                         print("")
#                     # if 'configs' in config_str_stdout and 'config' in config_str_stdout1:
#                     #     print("In LDMS_V2 pms file comparison")
#                         #remoteDevice.exec_cmd(f"git diff {srv_path}/config {srv_path}/config.$(date +%Y%m%d) >> {remote_path}/PMS2_Config_{current_date}.txt")
#                     else:# 'configs' not in config_str_stdout:
#                         cmd = (f"git diff {srv_path}/config {srv_path}/config.$(date +%Y%m%d) > {remote_path}/PMS_Config_{current_date}.txt")
#                         remoteDevice.exec_cmd(cmd)
#                     print("Change successfully recorded on remote device.")
#                 except Exception as e:
#                     print(f"Error sending change to remote device: {e}")
def send_change_to_remote_ldms(device_ip, local_folder_path):
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia")
    retVal = remoteDevice.connect()
    current_date = datetime.now().strftime('%Y-%m-%d')
    remote_path = f'/home/nvidia/pms/TechApp/{current_date}'
    if retVal:
        for folder in os.listdir(local_folder_path):
            if folder == 'ldms':
                try:
                    ensure_remote_folder(remoteDevice, remote_path)
                    _, config_str_stdout, _ = remoteDevice.exec_cmd(f"ls /srv/")
                    if 'configs' in config_str_stdout:
                        # print("In LDMS_V2 file comparison!!!")
                        if folder=='ldms':
                            remoteDevice.exec_cmd(f"git diff /srv/configs /home/nvidia/pms/archive/{current_date}/configs.$(date +%Y%m%d) >> {remote_path}/LDMS2_Configs_{current_date}.txt")
                        # elif folder=='pms':
                        #     remoteDevice.exec_cmd(f"git diff /srv/pms/detect/config /srv/pms/detect/config.$(date +%Y%m%d) >> {remote_path}/PMS2_Configs_{current_date}.txt")
                    if "configs" not in config_str_stdout:
                        if folder=='ldms':
                            remoteDevice.exec_cmd(f"git diff /srv/ldms/detect/config /srv/ldms/detect/config.$(date +%Y%m%d) >> {remote_path}/LDMS1_Config_{current_date}.txt")
                        # elif folder=='pms':
                        #     remoteDevice.exec_cmd(f"git diff /srv/pms/detect/config /srv/pms/detect/config.$(date +%Y%m%d) >> {remote_path}/PMS1_Config_{current_date}.txt")
                except Exception as e:
                    print(f"Error sending change to remote device: {e}")

def send_change_to_remote_pms(device_ip, local_folder_path):
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia")
    retVal = remoteDevice.connect()
    current_date = datetime.now().strftime('%Y-%m-%d')
    remote_path = f'/home/nvidia/pms/TechApp/{current_date}'
    if retVal:
        for folder in os.listdir(local_folder_path):
            # if folder == 'pms':
            try:
                ensure_remote_folder(remoteDevice, remote_path)
                _, config_str_stdout, _ = remoteDevice.exec_cmd(f"ls /srv/pms/detect")
                print("send_change_to_remote_pms", config_str_stdout)
                # if 'configs' in config_str_stdout:
                #     # print("In LDMS_V2 file comparison!!!")
                #     if folder=='ldms':
                #         remoteDevice.exec_cmd(f"git diff /srv/configs /home/nvidia/pms/archive/{current_date}/configs.$(date +%Y%m%d) >> {remote_path}/LDMS2_Configs_{current_date}.txt")
                #     elif folder=='pms':
                #         remoteDevice.exec_cmd(f"git diff /srv/pms/detect/config /srv/pms/detect/config.$(date +%Y%m%d) >> {remote_path}/PMS2_Configs_{current_date}.txt")
                if "config" in config_str_stdout:
                    if folder=='pms':
                        # remoteDevice.exec_cmd(f"git diff /srv/ldms/detect/config /srv/ldms/detect/config.$(date +%Y%m%d) >> {remote_path}/LDMS1_Config_{current_date}.txt")
                    # elif folder=='pms':
                        remoteDevice.exec_cmd(f"git diff /srv/pms/detect/config /srv/pms/detect/config.$(date +%Y%m%d) >> {remote_path}/PMS1_Config_{current_date}.txt")
            except Exception as e:
                print(f"Error sending change to remote device: {e}")

def ensure_remote_folder(remoteDevice, remote_path):
    remoteDevice.exec_cmd(f"mkdir -p {remote_path}")


def set_services_state(device_ip: str, serviceDict: dict, remoteDevice):
    try:
        for service, state in serviceDict.items():
            if state:
                cmd = f"sudo systemctl enable {service}.service && sudo systemctl start {service}.service"
            else:
                cmd = f"sudo systemctl stop {service}.service && sudo systemctl disable {service}.service"
            _, str_stdout, str_stderr = remoteDevice.exec_cmd(cmd, timeout=5)
            print(str_stdout, str_stderr)
            # if str_stderr:
            #     print(f"Error with {service}: {str_stderr}")
            #     return "FAIL"
        return "SUCCESS"
    except Exception as e:
        print(f"Exception: {e}")
        return "FAIL"
    
def Software(device_ip):
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia")
    retVal = remoteDevice.connect()
    if retVal:
        try:
            # _, config_str_stdout, _ = remoteDevice.exec_cmd("cat /home/nvidia/build_1.0-245-g7b41bb2/build/code/pms_pytorch/ktc_sw_version.txt")
            # if '1.0-245-g7b41bb2' in config_str_stdout:
            #     return {"retrievedSoftwareVersion": "1.0-245"}
            _, config_str_stdout, _ = remoteDevice.exec_cmd("cat /home/nvidia/build_1.0-245-g7b41bb2/build/code/pms_pytorch/ktc_sw_version.txt")
            if config_str_stdout.strip():  
                lines = config_str_stdout.strip().split('\n')
                for line in lines:
                    return {"retrievedSoftwareVersion":line}
            else:
                return {"retrievedSoftwareVersion": "1"}
        except Exception as e:
            print(f"This is exception: {e}")
            return {"retrievedSoftwareVersion": "Device Not Reachable"}
    else:
        return {"retrievedSoftwareVersion": "Device Not Reachable"}

def Deepstream(device_ip):
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia")
    retVal = remoteDevice.connect()
    if retVal:
        try:
            _, config_str_stdout, _ = remoteDevice.exec_cmd("cat /opt/nvidia/deepstream/deepstream/version")
            for line in config_str_stdout.split('\n'):
                if "Version:" in line:
                    modification_time = line.strip().split()[1]
                    return {"retrievedDeepStreamVersion": modification_time}
                else:
                    return {"retrievedDeepStreamVersion": "Not Available"}
        except Exception as e:
            print(f"This is exception: {e}")
            return {"retrievedDeepStreamVersion": "Unknown"}
    else:
        return {"retrievedDeepStreamVersion":"Device Not Reachable"}

def DeviceInstallation(device_ip:str):
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia")
    retVal = remoteDevice.connect()
    filepath = "/srv/"
    if retVal:
        try:
            _, stdout, stderr = remoteDevice.exec_cmd(f"stat {filepath}")
            output = stdout.strip()
            error = stderr.strip()
            
            if error:
                return{"retrievedDeviceInstallationDate": "error"}
            else:
                for line in output.split('\n'):
                    if "Modify:" in line:
                        modification_time = line.strip().split()[1]
                        return {"retrievedDeviceInstallationDate": modification_time}        
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        return{"retrievedDeviceInstallationDate":"device Not Reachable"}

if __name__ == "__main__":
    #pull_camera_images_and_dms_configs("192.168.64.129")
    pass