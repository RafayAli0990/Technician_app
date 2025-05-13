import os
# import paramiko
# from scp import SCPClient
# import random
import shutil
from remote_device import RemoteDevice
from time import sleep
import subprocess
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

def reset_last_backup_config(device_ip:str):
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia") # TODO: get password dynamically?
    retVal = remoteDevice.connect()
    if retVal:
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Device connected successfully : {device_ip}", 20)

        remoteDevice.exec_cmd(f"if [ -d /srv/pms/detect/config.$(date +%Y%m%d) ]; then echo \"backup found\"; fi ")
        remoteDevice.exec_cmd(f"if [ -d /srv/pms/detect/user_configs.$(date +%Y%m%d) ]; then echo \"backup found\"; fi ")

        remoteDevice.exec_cmd(f"if [ -d /srv/pms/detect/config.$(date +%Y%m%d) ]; then rm -r /srv/pms/detect/config && cp -r /srv/pms/detect/config.$(date +%Y%m%d) /srv/pms/detect/config; fi ")
        remoteDevice.exec_cmd(f"if [ -d /srv/pms/detect/user_configs.$(date +%Y%m%d) ]; then rm -r /srv/pms/detect/user_configs && cp -r /srv/pms/detect/user_configs.$(date +%Y%m%d) /srv/pms/detect/user_configs; fi ")
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] RESET COMMANDS EXECUTED", 90)

def check_active_services(device_ip: str, local_folder_path: str, rtsp_uri: dict):
    active_services = []
    retVal_Status = "FAILED"
    services = ["detect_mobile", "detect", "detect_ldms", "detect_noentry", "detect_rlms"]
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia")
    retVal = remoteDevice.connect()
    if retVal:
        try:
            for service in services:

                _, _stdout, _stderr = remoteDevice.exec_cmd(f"systemctl status {service}")
                #print(_stdout, _stderr)
                status = _stdout.strip()
                #print("Status:", status)
                
                if 'active (running)' in status.lower() and 'enabled' in status.lower():
                    active_services.append(service)
                #else:
                #    print(service, status)
            
            if active_services:
                retVal_Status = "SUCCESS"
        
        except Exception as e:
            print(f"Something happened while checking services: {e}")
    
    print("Active Services:", active_services)

    # if success, set retVal_Status to "SUCCESS" before returning, or else values will be ignored
    return retVal_Status, active_services

def pull_camera_images_and_configs(device_ip:str, local_folder_path:str, rtsp_uri:dict, active_services:list):
    #retVal_Status = check_active_services(device_ip, local_folder_path, rtsp_uri)
    retVal = "FAILED"
    # if service is active, call respective download
    for active_ser in active_services:
        if "detect_ldms" in active_ser:
            #print("I'm here in Pull camera image and configs")
            retVal = pull_camera_images_and_ldms_configs(device_ip, local_folder_path, rtsp_uri)
        
        # and / or
        elif "detect_mobile" in active_ser or "detect" in active_ser or "detect_noentry" in active_ser:
            retVal = pull_camera_images_and_dms_configs(device_ip, local_folder_path, rtsp_uri)

    return retVal,active_services

def pull_camera_images_and_ldms_configs(device_ip:str, local_folder_path:str, rtsp_uri:dict):
    # same like dms download code, but just download dms zones and configs
    #print("I'm here in pull camera images and ldms configs")
    finalReturnValue = "SUCCESS"
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia") # TODO: get password dynamically?
    retVal = remoteDevice.connect()
    if retVal:
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Device connected successfully : {device_ip}", 20)
        #print("I'm here in pull camera images and ldms configs -->1")
        remoteDevice.createTmpFolder()
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Temp folder creation done")

        remote_camera_images_folder = os.path.join(remoteDevice.tmp_folder_path, 'CameraImages').replace('\\','/')
        remoteDevice.exec_cmd(f"mkdir -p {remote_camera_images_folder}")
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] CameraImages folder creation done")

        try:
            #print("I'm in ped .10 camera")
            # print(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=\"{rtsp_uri["pedestrian_camera_uri"]}\" ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/pedestrian_camera_uri.jpg max-files=1")
            _, str_stdout, str_stderr = remoteDevice.exec_cmd(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=\"{rtsp_uri['pedestrian_camera_uri']}\" ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/pedestrian_camera_uri.jpg max-files=1", timeout=5)

            #str_stdout, str_stderr = remoteDevice.exec_cmd(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=\"{v}\" ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/{k}.jpg max-files=1", timeout=10)
            #str_stdout, str_stderr = remoteDevice.exec_cmd(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=file:///home/nvidia/ped_violation.mp4 ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/out.jpg max-files=1", timeout=10)
            # str_stdout, str_stderr = remoteDevice.exec_cmd(f"cp /home/nvidia/1.png {remote_camera_images_folder}/out.png", timeout=10)
            #print(str_stdout, str_stderr)
            sleep(2)
        except Exception as e:
            print("Exited gst pipeline with exception: ", e) # Nothing to worry

        try:
            #print("I'm in mobile .20 camera")
            # print(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=\"{rtsp_uri["pedestrian_camera_uri"]}\" ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/pedestrian_camera_uri.jpg max-files=1")
            _, str_stdout, str_stderr = remoteDevice.exec_cmd(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=\"{rtsp_uri['mobile_detection_camera_uri']}\" ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/mobile_detection_camera_uri.jpg max-files=1", timeout=5)
            # str_stdout, str_stderr = remoteDevice.exec_cmd(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=\"{v}\" ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/{k}.jpg max-files=1", timeout=10)
            #str_stdout, str_stderr = remoteDevice.exec_cmd(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=file:///home/nvidia/ped_violation.mp4 ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/out.jpg max-files=1", timeout=10)
            # str_stdout, str_stderr = remoteDevice.exec_cmd(f"cp /home/nvidia/1.png {remote_camera_images_folder}/out.png", timeout=10)
            # print(str_stdout, str_stderr)
            sleep(2)
        except Exception as e:
            print("Exited gst pipeline with exception: ", e) # Nothing to worry

        try:
            # remoteDevice.recv_file(local_folder_path, "/srv/pms/detect/config/app_settings.yaml")
            # remoteDevice.recv_file(local_folder_path, "/srv/pms/detect/config/zones_mobile.txt")
            # remoteDevice.recv_file(local_folder_path, "/srv/pms/detect/config/zones_ped.txt")
            _, str_stdout, _ = remoteDevice.exec_cmd(f"ls /srv/ldms/detect/")
            #print("I'm here in pull camera images and ldms configs -->2")
            if "config" in str_stdout:
                # local_config_ldms_path = os.path.join(local_folder_path, "config_ldms")
                # if not os.path.exists(local_config_ldms_path):
                #     os.makedirs(local_config_ldms_path)
                remoteDevice.recv_file(local_folder_path, "/srv/ldms/detect/config")
                src_path = os.path.join(local_folder_path, "config") 
                dst_path = os.path.join(local_folder_path, "config_ldms") 
                if os.path.exists(src_path): 
                    os.rename(src_path, dst_path)
                
                # print("1")
                # local_config_path = os.path.join(local_folder_path, "config")
                # print("2")
                # local_config_ldms_path = os.path.join(local_folder_path, "config_ldms")
                # print("3")
                # if not os.path.exists(local_config_ldms_path):
                #     os.makedirs(local_config_ldms_path)
                # print("4")
                #shutil.copy(local_config_path, local_config_ldms_path)
                print("file copied successfully!")
                
            _, str_stdout, _ = remoteDevice.exec_cmd(f"ls {remote_camera_images_folder}/*")

            if len(str_stdout) > 3:
                remoteDevice.recv_file(local_folder_path, remote_camera_images_folder)
                remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Remote file copied successfully at {local_folder_path}", 30)
            else:
                finalReturnValue = "FAILED"
        except Exception as e:
            print("Exited receiving file with exception: ", e)

        remoteDevice.disconnect()
        
    return finalReturnValue


def pull_camera_images_and_dms_configs(device_ip:str, local_folder_path:str, rtsp_uri:dict):
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
            sleep(2)
        except Exception as e:
            print("Exited gst pipeline with exception: ", e) # Nothing to worry

        try:
            # print(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=\"{rtsp_uri["pedestrian_camera_uri"]}\" ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/pedestrian_camera_uri.jpg max-files=1")
            _, str_stdout, str_stderr = remoteDevice.exec_cmd(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=\"{rtsp_uri['mobile_detection_camera_uri']}\" ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/mobile_detection_camera_uri.jpg max-files=1", timeout=5)
            # str_stdout, str_stderr = remoteDevice.exec_cmd(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=\"{v}\" ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/{k}.jpg max-files=1", timeout=10)
            #str_stdout, str_stderr = remoteDevice.exec_cmd(f"gst-launch-1.0 uridecodebin buffer-size=1 uri=file:///home/nvidia/ped_violation.mp4 ! nvvidconv ! jpegenc ! multifilesink location={remote_camera_images_folder}/out.jpg max-files=1", timeout=10)
            # str_stdout, str_stderr = remoteDevice.exec_cmd(f"cp /home/nvidia/1.png {remote_camera_images_folder}/out.png", timeout=10)
            # print(str_stdout, str_stderr)
            sleep(2)
        except Exception as e:
            print("Exited gst pipeline with exception: ", e) # Nothing to worry

        try:
            # remoteDevice.recv_file(local_folder_path, "/srv/pms/detect/config/app_settings.yaml")
            # remoteDevice.recv_file(local_folder_path, "/srv/pms/detect/config/zones_mobile.txt")
            # remoteDevice.recv_file(local_folder_path, "/srv/pms/detect/config/zones_ped.txt")

            _, str_stdout, str_stderr = remoteDevice.exec_cmd(f"ls /srv/pms/detect")

            if "config" in str_stdout:
                remoteDevice.recv_file(local_folder_path, "/srv/pms/detect/config")
            if "user_configs" in str_stdout:
                remoteDevice.recv_file(local_folder_path, "/srv/pms/detect/user_configs")

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

def save_dms_configs(device_ip:str, local_folder_path:str):
    remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia") # TODO: get password dynamically?
    retVal = remoteDevice.connect()
    if retVal:
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Device connected successfully : {device_ip}", 20)

        remoteDevice.createTmpFolder()
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Temp folder creation done")

        if os.path.exists(os.path.join(local_folder_path, "config")):
            remoteDevice.send_file(os.path.join(local_folder_path, "config"), f"{remoteDevice.tmp_folder_path}")
            
        #if os.path.exists(os.path.join(local_folder_path, "user_configs")):
        #    remoteDevice.send_file(os.path.join(local_folder_path, "user_configs"), f"{remoteDevice.tmp_folder_path}")

        # Check the directories and list their contents
        _, str_stdout1, _ = remoteDevice.exec_cmd("if [ -d /srv/pms/detect ]; then ls /srv/pms/detect; fi")
        _, str_stdout2, _ = remoteDevice.exec_cmd("if [ -d /srv/ldms/detect ]; then ls /srv/ldms/detect; fi")

        if "config" in str_stdout1:
            remoteDevice.exec_cmd("if [ ! -d /srv/pms/detect/config.$(date +%Y%m%d) ]; then cp -r /srv/pms/detect/config /srv/pms/detect/config.$(date +%Y%m%d); fi ")
        if "config" in str_stdout2:
            remoteDevice.exec_cmd("if [ ! -d /srv/ldms/detect/config.$(date +%Y%m%d) ]; then cp -r /srv/ldms/detect/config /srv/ldms/detect/config.$(date +%Y%m%d); fi ")


        
        _, str_stdout1, str_stderr = remoteDevice.exec_cmd(f"ls {remoteDevice.tmp_folder_path}")
        _, str_stdout2, str_stderr = remoteDevice.exec_cmd(f"ls {remoteDevice.tmp_folder_path}")
        if "config" in str_stdout1:
            remoteDevice.exec_cmd(f"cp -r {remoteDevice.tmp_folder_path}/config /srv/pms/detect/.")
        elif "config" in str_stdout2:
            remoteDevice.exec_cmd(f"cp -r {remoteDevice.tmp_folder_path}/configs /srv/ldms/detect/.")
            
        remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Configs folder copy done")

        try:
            
            _, config_str_stdout, config_str_stderr = remoteDevice.exec_cmd(f"ls /srv/pms/detect/config")
            if "zones_ped.txt" in config_str_stdout and "zones_mobile.txt" in config_str_stdout:
                remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Zone file copied successfully", 30)
            else:
                remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Zone file copy unsuccessful", 30)
                return "FAILED"
            
            _, config_str_stdout1, config_str_stderr1 = remoteDevice.exec_cmd(f"ls /srv/ldms/detect/config")
            if "zones_ldms.txt" in config_str_stdout1:
                remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Zone file copied successfully", 30)
            else:
                remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Zone file copy unsuccessful", 30)
                return "FAILED"

            _, user_configs_str_stdout, user_configs_str_stderr = remoteDevice.exec_cmd(f"ls /srv/pms/detect/user_configs")
            if (("app_settings.yaml" in user_configs_str_stdout) or 
                ("app_settings.yaml" in config_str_stdout)or ("app_settings.yaml" in config_str_stdout1)):
                remoteDevice.log_message("INFO", f"[REMOTE DEVICE] app_settings.yaml file copied successfully", 30)
            else:
                remoteDevice.log_message("INFO", f"[REMOTE DEVICE] app_settings.yaml file copy unsuccessful", 30)
                return "FAILED"
        except Exception as e:
            print("Exited sending file with exception: ", e)

        remoteDevice.disconnect()
        
    return "SUCCESS"

if __name__ == "__main__":
    pull_camera_images_and_dms_configs("192.168.64.129")