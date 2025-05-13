import os
import paramiko
from scp import SCPClient
import random

#from logger import LoggerUtils

class RemoteDevice:
    def __init__(self, device_ip:str, device_login_user:str, device_login_pass:str) -> None:
        self.device_ip = device_ip
        self.device_login_user = device_login_user
        self.device_login_pass = device_login_pass

        self.client = None
        self.scp = None
        self.tmp_folder_path = None
        #self.logger = LoggerUtils()

    def log_message(self, log_level:str="INFO", message:str="", progress_bar_level:int=None):
        print(message)
        pass
        #self.logger.log_message(log_level, message, progress_bar_level)
        # if self.logger is not None:
        #     self.logger.log_message(log_level, message, progress_bar_level)

    def removeTmpFolder(self):
        if self.tmp_folder_path is not None:
            self.exec_cmd(f"rm -r {self.tmp_folder_path}")

    def createTmpFolder(self, foldername:str="ktc_app"):
        if self.tmp_folder_path is None:
            self.tmp_folder_path = "/tmp/"+foldername+str(random.randint(11111,99999))
            self.exec_cmd(f"mkdir -p {self.tmp_folder_path}") # TODO: make sure if dir is created

    def connect(self, enable_scp:bool=True):
        
        # subprocess.run(["ssh", f"-o GlobalKnownHostsFile=/dev/null -o UserKnownHostsFile=./known_hosts {self.device_login_user}@{self.device_ip}"])
        self.client = paramiko.client.SSHClient() # TODO: login via ssh key
        #self.client.load_host_keys(os.path.join(os.path.expanduser('~'),'.ssh','known_hosts')) # this is not working if USERNAME in windows7 configured with spaces
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # RejectPolicy
        try:
            self.client.connect(self.device_ip, username=self.device_login_user, password=self.device_login_pass, timeout=3)
            # self.client.connect(self.device_ip, username=self.device_login_user, password=self.device_login_pass, key_filename='', timeout=3)
            #self.log_message("INFO", f"[REMOTE DEVICE] SSH connect done")
            
            if enable_scp:
                self.scp = SCPClient(self.client.get_transport())
                #self.log_message("INFO", f"[REMOTE DEVICE] SCP connect done")
    
            return True
        except Exception as e:
            pass
            #self.log_message("ERROR", f"[REMOTE DEVICE] Failed to connect device: {self.device_ip}")
            #self.log_message("ERROR", f"[REMOTE DEVICE] Err message: {e}")
            # subprocess.run(["ssh-keyscan", f"{self.device_ip}", " >> ", "~/.ssh/known_hosts"])
        
        return False

    def disconnect(self):
        self.removeTmpFolder()
        self.client.close()

    def exec_cmd(self, cmd:str, timeout:int=None): # TODO: return success/failure
        #self.log_message("INFO", f"[REMOTE DEVICE] Executing command {cmd}")
        str_stdin, str_stdout, str_stderr = "", "", ""
        try:
            _stdin, _stdout, _stderr = self.client.exec_command(cmd, timeout=timeout) # if there is no _stderr, then its success?
            try:
                #print(_stdout.channel.recv_exit_status())
                str_stdout, str_stderr = _stdout.read().decode(), _stderr.read().decode()
                #self.log_message("DEBUG", f"[REMOTE DEVICE] STDOUT {str_stdout}")
                print(str_stdout, str_stderr)
                #self.log_message("DEBUG", f"[REMOTE DEVICE] STDERR {str_stdout}")
            except Exception as e:
                #self.log_message("DEBUG", f"[REMOTE DEVICE] Decoding std_out/std_err issue:\n {e}") 
                pass                
            
        except Exception as e:
            #self.log_message("DEBUG", f"[REMOTE DEVICE] Error while executing command {cmd} :\n {e}")
            pass

        return (_stdin, str_stdout, str_stderr)
    
    def exec_cmd_interactive(self, cmd:str, timeout:int=None): # TODO: return success/failure
        #self.log_message("INFO", f"[REMOTE DEVICE] Executing command {cmd}")
        str_stdin, str_stdout, str_stderr = "", "", ""
        try:
            _stdin, _stdout, _stderr = self.client.exec_command(cmd, timeout=timeout) # if there is no _stderr, then its success?
            # try:
            #     #print(_stdout.channel.recv_exit_status())
            #     #str_stdout, str_stderr = _stdout.read().decode(), _stderr.read().decode()
            #     #self.log_message("DEBUG", f"[REMOTE DEVICE] STDOUT {str_stdout}")
            #     #self.log_message("DEBUG", f"[REMOTE DEVICE] STDERR {str_stderr}")
            # except Exception as e:
            #     #self.log_message("DEBUG", f"[REMOTE DEVICE] Decoding std_out/std_err issue:\n {e}") 
            #     pass                
            
        except Exception as e:
            #self.log_message("DEBUG", f"[REMOTE DEVICE] Error while executing command {cmd} :\n {e}")
            pass
        
        return (_stdin, _stdout, _stderr)

    def send_file(self, local_file_path:str, remote_file_path:str): # not sure if sending folder working in this way, may be just recursive is needed
        self.scp.put(local_file_path, remote_file_path, recursive=True) # create hashing and make sure both are same, but maybe scp does it already
    
    def recv_file(self, local_file_path:str, remote_file_path:str=None):
        self.scp.get(remote_file_path, local_file_path, recursive=True) # create hashing and make sure poth are same, but maybe scp does it already

# TODO: flash KTC related SW as well or we can give a KFL file for that. This process heavily depends on SSH. Find an alternative to use low level ways like UDP/TCP
# def main(device_ip:str, flash_file_path:str, logger_callback):
#     remoteDevice = RemoteDevice(device_ip, "nvidia", "nvidia", logger=logger_callback) # TODO: get password dynamically?
#     if remoteDevice.connect():
#         remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Device connected successfully : {device_ip}", 20)

#         remoteDevice.createTmpFolder()
#         remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Temp folder creation done")

#         remote_file_path = remoteDevice.send_file(flash_file_path)
#         remoteDevice.log_message("INFO", f"[REMOTE DEVICE] Flash file copied successfully at {remote_file_path}", 30)
        
#         remoteDevice.exec_cmd(f"mv {os.path.splitext(remote_file_path)[0]}.kfl {os.path.splitext(remote_file_path)[0]}.tar.gz")

#         remoteDevice.exec_cmd(f"tar -xzvf {os.path.splitext(remote_file_path)[0]}.tar.gz -C {remoteDevice.tmp_folder_path}")
        
#         sw_dir = os.path.join(os.path.splitext(remote_file_path)[0], "sw").replace("\\","/")
#         str_stdout, str_stderr = remoteDevice.exec_cmd(f"bash {os.path.splitext(remote_file_path)[0]}/install.sh -d {sw_dir}")

#         remoteDevice.disconnect()

#         if "installation successful" in str_stdout:
#             remoteDevice.log_message("INFO", f"[REMOTE DEVICE] SW flash successfully completed", 90)
#             return "SUCCESS"
        
#     return "FAILED"
    
# if __name__ == "__main__":
#     main("192.168.64.129")