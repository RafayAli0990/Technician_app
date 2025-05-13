import os
import sys
import logging
from pathlib import Path
import argparse

import traceback
os.environ["KIVY_NO_ARGS"] = "1"
from kivy.lang import Builder
from kivy.core.window import Window

from libs.yaml_parser import YamlParser
# os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2' # - angle bg is available only on windows
os.environ["CONFIG_ROOT"] = os.path.dirname(os.path.abspath(__file__))
# os.environ["CONFIG_ROOT"] = str(Path(__file__).parent)

def main(app_settings_path, dms_types):
    #from kivy import Config
    #Config.set('graphics', 'multisamples', '0')
    from kivymd.app import MDApp

    KV_DIR = os.path.join(os.environ['CONFIG_ROOT'], "kv")
    for kv_file in os.listdir(KV_DIR):
        
        if (("root_screen" in kv_file) or ("settings_tab" in kv_file)) or \
            (("detect_ldms" in dms_types) and ("ldms" in kv_file)) or \
            (("detect_mobile" in dms_types) and ("mobile" in kv_file)) or \
            (("detect_noentry" in dms_types) and ("noentry" in kv_file)) or \
            (("detect" in dms_types) and ("ped" in kv_file)):
            #print(kv_file)
            with open(os.path.join(KV_DIR, kv_file), encoding="utf-8") as kv:
                Builder.load_string(kv.read())

    KV = """
#:import ConfigRootScreen baseclass.root_screen.ConfigRootScreen

ScreenManager:

    ConfigRootScreen:
        name: "config root screen"    
"""

    class Config(MDApp):

        def __init__(self, app_settings_path, **kwargs):
            super().__init__(**kwargs)
            self.title = "Configure Violation Detector"
            self.app_settings_path = app_settings_path

        # remove this and test clean exits
        def _on_request_close(self, *args):
            return True
    
        def build(self):  
            Window.bind(on_request_close=self._on_request_close) # remove this and test clean exits
            app = MDApp.get_running_app()  
            try:          
                self.read_settings(app)
            except Exception as e:
                print(e)

            # --- configure logging
            # for handler in logging.root.handlers[:]:
            #     logging.root.removeHandler(handler)
            # fname = f"{os.environ['CONFIG_ROOT']}/logs/config.log"
            # logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%d-%m-%Y %I:%M:%S %p', level=logging.DEBUG, filename=fname)   

            FONT_PATH = f"{os.environ['CONFIG_ROOT']}/fonts/"
            self.theme_cls.font_styles.update(
                {
                    "Title": [
                        FONT_PATH + "Montserrat-BoldItalic",
                        13,
                        False,
                        0.15,
                    ],
                    "Subtitle": [
                        FONT_PATH + "Montserrat-Black",
                        13,
                        False,
                        0.1,
                    ],
                    "Body": [FONT_PATH + "Montserrat-Regular", 13, False, 0.5],                
                    "Button": [FONT_PATH + "Montserrat-SemiBold", 13, True, 1.25]
                }
            )
            return Builder.load_string(KV)   

        # def read_settings(self, app):        
            
        #     # Read YAML configuration file
        #     settings_file_path = self.app_settings_path #os.path.join(os.environ['CONFIG_ROOT'],"config","app_settings.yaml")
        #     print("determining form this path --->>>",settings_file_path)
        #     if Path(settings_file_path).is_file():                              
        #          # Read YAML config file using YamlParser class
        #         # app.cfg = YamlParser(config_file=settings_file_path)
        #         # app.settings_file_path = settings_file_path
        #         if 'detect_ldms' in dms_types:
        #             #print('pms file path', os.path.join(Path(settings_file_path).parent.absolute().parent.absolute(), 'config','app_settings.yaml'))
        #             #print('ldms file path', settings_file_path)
        #             # app.settings_file_path = {'ldms': settings_file_path, 'pms': os.path.join(Path(settings_file_path).parent.absolute(), 'config','app_settings.yaml')}
        #             app.cfg = {'ldms': YamlParser(config_file=settings_file_path), 
        #                        'pms': YamlParser(config_file=os.path.join(Path(settings_file_path).parent.absolute().parent.absolute(), 'config','app_settings.yaml'))
        #                     }
        #         elif (('detect_mobile' in dms_types) and ('detect' in dms_types)):
        #             # app.settings_file_path = {'ldms': None, 'pms': settings_file_path}
        #             app.cfg = {'ldms': None, 'pms': YamlParser(config_file=settings_file_path)}
        #             #print(app.cfg)
        #         app.device_file_dir = Path(settings_file_path).parent.absolute().parent.absolute() # 2 steps back
        #         print("config.py-------->>>>dms_types",dms_types)
        #         app.dms_types = dms_types
        #         #Path(settings_file_path).parent
        #     else:
        #         print(f'Settings file not found in {settings_file_path}')
        #         sys.exit()
        def read_settings(self, app):
            # Read YAML configuration file
            settings_file_path = self.app_settings_path
            #print("Determining from this path --->>>", settings_file_path)
            
            if Path(settings_file_path).is_file():
                if 'detect_ldms' in dms_types and 'detect_mobile' in dms_types:
                    print(os.path.join(Path(settings_file_path).parent.absolute().parent.absolute().parent.absolute(), 'pms','config', 'app_settings.yaml'))
                    app.cfg = {
                        'ldms': YamlParser(config_file=settings_file_path),
                        'pms': YamlParser(config_file=os.path.join(Path(settings_file_path).parent.absolute().parent.absolute().parent.absolute(), 'pms','config', 'app_settings.yaml'))
                        
                    }
                elif 'detect_ldms' in dms_types:
                    app.cfg = {
                        'ldms': YamlParser(config_file=settings_file_path),
                        'pms': None #YamlParser(config_file=os.path.join(Path(settings_file_path).parent.absolute().parent.absolute(), 'config', 'app_settings.yaml'))
                    }
                elif 'detect_mobile' in dms_types or  'detect' in dms_types or 'detect_noentry' in dms_types:
                    app.cfg = {'ldms': None, 
                               'pms': YamlParser(config_file=os.path.join(Path(settings_file_path).parent.absolute().parent.absolute().parent.absolute(), 'pms','config', 'app_settings.yaml'))}

                app.device_file_dir = Path(settings_file_path).parent.absolute().parent.absolute().parent.absolute()  # 2 steps back
                app.dms_types = dms_types
                
                #print("config.py-------->>>>dms_types", dms_types)
            else:
                print(f'Settings file not found in {settings_file_path}')
                sys.exit()

    con = Config(app_settings_path=app_settings_path)
    try:
        con.run()
    except Exception as e:
        print("[Error] Exit from config.py : ", e)
        traceback.print_exc(file=sys.stdout)
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Optional app description')
    parser.add_argument('app_settings_path', type=str, help='app_settings.yaml path')
    parser.add_argument('dms_types', type=str, help='detect_ldms,detect_mobile,detect,detect_noentry') #ldms,pms
    
    args = parser.parse_args()

    dms_types = args.dms_types.split(',')
    #print("Near main---------------->>>>>>>>",dms_types)
    main(args.app_settings_path, dms_types)