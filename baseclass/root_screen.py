import os
import cv2
import logging
import numpy as np
import yaml
import subprocess
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import BooleanProperty

from kivy.graphics.texture import Texture
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton

import weakref
import io

from libs.yaml_parser import YamlParser
from pathlib import Path
import remote_works 


from remote_device import RemoteDevice
import globals as gb

from copy import deepcopy
from baseclass.settings_tab import SettingsTab
from baseclass.ped_tab import PedTab
from baseclass.mobile_tab import MobileTab
from baseclass.noentry_tab import NoentryTab
from baseclass.ldms_tab import LdmsTab

from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

errorMessage = ''

class ConfigRootScreen(MDScreen):

    VIDEO_WIDTH = 960 # Scale video from source to this width
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # get instance of application object
        app = MDApp.get_running_app()

        self.title = "Configure PMS Cube"
        self.theme_cls = app.theme_cls
        self.message_dialog = None
        self.restart_dialog = None
        self.accept_dialog = None
        self.exit_dialog = None
        self.stream = "ped" # TODO: make it to use camera_opts

        #video_stream_loader = StreamLoader(app.cfg, self.VIDEO_WIDTH)
        #self.video_streams = iter(video_stream_loader)

        self.video_width = [1250,1250]
        self.video_height = [750,750]
        self.imgs = [None] * 2
        
        # camera_image_file_path = os.path.join(app.device_file_dir,"CameraImages","out.png")
        # self.frame = np.zeros(self.get_vid_dim(), np.uint8) # default black image - This allows technicians to configure yaml settings even if cameras are not connected in site  or in office
        # if os.path.exists(camera_image_file_path):
        #     self.frame = cv2.imread(camera_image_file_path)
        # elif os.path.exists(os.path.join(app.device_file_dir,"CameraImages","out.jpg")):
        #     camera_image_file_path = os.path.join(app.device_file_dir,"CameraImages","out.jpg")
        #     self.frame = cv2.imread(camera_image_file_path)
        
        # self.frame = cv2.resize(self.frame, self.get_vid_dim(), interpolation = cv2.INTER_AREA)
        # self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)

        camera_opts = ["mobile_detection_camera_uri", "pedestrian_camera_uri"]
        cameraFramesFilePath = {} # this no need to be a dict
        self.cameraFrames = {}
        for k in camera_opts:
            cameraFramesFilePath[k] = os.path.join(app.device_file_dir,"CameraImages", f"{k}.png")
            self.cameraFrames[k] = np.zeros(self.get_vid_dim(), np.uint8) # default black image - This allows technicians to configure yaml settings even if cameras are not connected in site  or in office
            if os.path.exists(cameraFramesFilePath[k]):
                self.cameraFrames[k] = cv2.imread(cameraFramesFilePath[k])
            elif os.path.exists(os.path.join(app.device_file_dir,"CameraImages", f"{k}.jpg")):
                cameraFramesFilePath[k] = os.path.join(app.device_file_dir,"CameraImages", f"{k}.jpg")
                self.cameraFrames[k] = cv2.imread(cameraFramesFilePath[k])

            self.cameraFrames[k] = cv2.resize(self.cameraFrames[k], self.get_vid_dim(), interpolation = cv2.INTER_AREA)
            self.cameraFrames[k] = cv2.cvtColor(self.cameraFrames[k], cv2.COLOR_BGR2RGB)

        # set root window dimensions
        # Window.size = (self.VIDEO_WIDTH + 450, 700 + 100)
        # self.width = Window.width
        # self.height = Window.height
        # Window.size = (self.width + 320, 620)  # Example size: VIDEO_WIDTH + 320, 500 + 120
        # # Center the window on the screen
        # screen_width, screen_height = Window.system_size  # Get system screen dimensions
        # Window.left = (screen_width - Window.width) // 2
        # Window.top = (screen_height - Window.height) // 2

        # Window.size = (self.VIDEO_WIDTH + 320, 500 + 120)
        # Window.auto = True
        # Window.borderless = True

        # Window.size = (self.VIDEO_WIDTH + 400, 700 + 120) # Window.system_size  # Automatically sets fullscreen size
        Window.fullscreen = 'auto'

        # Center the window
        # screen_width, screen_height = Window.system_size
        # Window.left = (screen_width - Window.width) // 2
        # Window.top = (screen_height - Window.height) // 2

        # Print the window size and position in the same function
        # print(f"Window size: {Window.size}")
        # print(f"Window position: Left={Window.left}, Top={Window.top}")

        # refresh image from video source
        # DOESN'T WORK: Cannot update GUI element from another thread
        #Clock.schedule_interval(self.update_img, 4*(1.0/self.vid.fps)) 
        #stream_thread = Thread(target=self.update_img, daemon=True)            
        #stream_thread.start()
        
        Clock.schedule_once(self.populate_tabs)
        # self.update_img()

        self.settings_tabs = []
        Clock.schedule_once(self.populate_yaml_configs)

        # self.first_frame_read_success = False

        Clock.schedule_interval(lambda dt: self.update_img(), 4*(1.0/30.0)) # fps = 10

        # load zone / line coordinates from config files
        # self.load_coords(app)

        
        
        # self.update_img()
    # ---------------------------------------------------------------------------------
    # load zones / line coordinates from pedestrian / mobile config file 
    # - look for the coordinates file specified in the yaml settings file
    # - if the file exists then set the values of zones / line coords
    def load_coords(self, app):
        for dms_type in app.dms_types:
            #print("load coords", dms_type)
            if dms_type == 'detect':
                if Path(os.path.join(app.device_file_dir, "pms", app.cfg['pms'].DETECTIONS.PED.ZONES_FILE)).is_file():
                    zoneCoords = np.loadtxt(os.path.join(app.device_file_dir, "pms", app.cfg['pms'].DETECTIONS.PED.ZONES_FILE), dtype=np.float16)
                    gb.greenArea = self.denormalize_coords(zoneCoords[0:4, 0:2], 'ped')
                    gb.violetArea = self.denormalize_coords(zoneCoords[4:8, 0:2], 'ped')
                    gb.redLine = self.denormalize_coords(zoneCoords[8:10, 0:2], 'ped')
                    gb.lprLine = self.denormalize_coords(zoneCoords[10:12, 0:2], 'ped')
                    gb.middleLine = self.denormalize_coords(zoneCoords[12:14, 0:2], 'ped')
                    gb.entryLine = self.denormalize_coords(zoneCoords[14:16, 0:2], 'ped')
                    gb.exitLine = self.denormalize_coords(zoneCoords[16:18, 0:2], 'ped')
                    gb.leftLine = self.denormalize_coords(zoneCoords[18:20, 0:2], 'ped')
                    gb.rightLine = self.denormalize_coords(zoneCoords[20:22, 0:2], 'ped')

            elif dms_type == 'detect_mobile':
                # print("mobile zones -->>", dms_type, os.path.join(app.device_file_dir, app.cfg['pms'].DETECTIONS.MOBI.ZONES_FILE))
                if Path(os.path.join(app.device_file_dir, 'pms', app.cfg['pms'].DETECTIONS.MOBI.ZONES_FILE)).is_file():
                    '''
                    #print(os.path.join(app.device_file_dir, app.cfg['pms'].DETECTIONS.MOBI.ZONES_FILE))
                    zoneCoords = np.loadtxt(os.path.join(app.device_file_dir, 'pms', app.cfg['pms'].DETECTIONS.MOBI.ZONES_FILE), dtype=np.float16)
                    gb.vehicleArea = self.denormalize_coords(zoneCoords[0:4, 0:2], 'mobi')
                    gb.detectionLine = self.denormalize_coords(zoneCoords[4:6, 0:2], 'mobi')
                    gb.tintDetectZone = self.denormalize_coords(zoneCoords[6:, 0:2], 'mobi')
                    '''
                    vehicle_area_lines = ''
                    entry_line = ''
                    lane_line = ''
                    check_line = ''
                    tint_detect_zone = ''
                    lprpoly_zone = ''

                    with open(os.path.join(app.device_file_dir, 'pms', app.cfg['pms'].DETECTIONS.MOBI.ZONES_FILE)) as f:
                        for line in f:
                            if line.startswith('# Vehicle'):
                                lines_type = 'vehicle_area'
                            elif line.startswith('# Detection'):
                                lines_type = 'entry_line'
                            elif line.startswith('# Lane'):
                                lines_type = 'lane_line'
                            elif line.startswith('# Check lane'):
                                lines_type = 'check_line'
                            elif line.startswith('# Tint detect zone'):
                                lines_type = 'tint_detect_zone'
                            elif line.startswith('# LPR zone'):
                                lines_type = 'lprpoly_zone'

                            elif lines_type == 'vehicle_area':
                                vehicle_area_lines += line
                            elif lines_type == 'entry_line':
                                entry_line += line
                            elif lines_type == 'lane_line':
                                lane_line += line
                            elif lines_type == 'check_line':
                                check_line += line
                            elif lines_type == 'tint_detect_zone':
                                tint_detect_zone += line
                            elif lines_type == 'lprpoly_zone':
                                lprpoly_zone += line

                    coords = np.loadtxt(io.StringIO(vehicle_area_lines), dtype=np.float16)
                    gb.vehicleArea = self.denormalize_coords(coords[:, :], 'mobi')

                    if tint_detect_zone != '':
                        coords = np.loadtxt(io.StringIO(tint_detect_zone), dtype=np.float16)
                        gb.tintDetectZone = self.denormalize_coords(coords[:, :], 'mobi')

                    if lprpoly_zone != '':
                        coords = np.loadtxt(io.StringIO(lprpoly_zone), dtype=np.float16)
                        gb.lprpoly = self.denormalize_coords(coords[:, :], 'mobi')

                    coords = np.loadtxt(io.StringIO(entry_line), dtype=np.float16)
                    gb.detectionLine = self.denormalize_coords(coords[:, :], 'mobi')
            elif dms_type == 'detect_noentry':
                #for val in app.cfg['pms'].DETECTIONS.NOENTRY.ZONES_FILE.split("\n"):
                if Path(os.path.join(app.device_file_dir, "pms", app.cfg['pms'].DETECTIONS.NOENTRY.ZONES_FILE)).is_file():
                    # zoneCoords = np.loadtxt(os.path.join(app.device_file_dir, "pms", app.cfg['pms'].DETECTIONS.NOENTRY.ZONES_FILE), dtype=np.float16)
                    # gb.vehicleArea_noentry = self.denormalize_coords(zoneCoords[0:4, 0:2], 'noentry')
                    # gb.noentry_zone_noentry = self.denormalize_coords(zoneCoords[4:8, 0:2], 'noentry')
                    # gb.entryLine_noentry = self.denormalize_coords(zoneCoords[8:, 0:2], 'noentry')
                    vehicle_area_lines = ''
                    noentry_area_lines = ''
                    entry_line = ''
                    exit_line = ''
                    lpr_line = ''
                    with open(os.path.join(app.device_file_dir, "pms", app.cfg['pms'].DETECTIONS.NOENTRY.ZONES_FILE)) as f:
                        for line in f:
                            if line.startswith('# Vehicle'):
                                lines_type = 'vehicle_area'
                            elif line.startswith('# LPR'):
                                lines_type = 'lpr_line'
                            elif line.startswith('# No-entry'):
                                lines_type = 'noentry_area'
                            elif line.startswith('# Entry'):
                                lines_type = 'entry_line'
                            elif line.startswith('# Exit'):
                                lines_type = 'exit_line'

                            elif lines_type == 'vehicle_area':
                                vehicle_area_lines += line
                            elif lines_type == 'lpr_line':
                                lpr_line += line
                            elif lines_type == 'noentry_area':
                                noentry_area_lines += line
                            elif lines_type == 'entry_line':
                                entry_line += line
                            elif lines_type == 'exit_line':
                                exit_line += line

                    nocoords = np.loadtxt(io.StringIO(vehicle_area_lines), dtype=np.float16)
                    gb.vehicleArea_noentry = self.denormalize_coords(nocoords[:, :], 'noentry')
                    
                    if lpr_line != '':
                        nocoords = np.loadtxt(io.StringIO(lpr_line), dtype=np.float16)
                        gb.lprLine_noentry = self.denormalize_coords(nocoords[:, :], 'noentry')
                    
                    if noentry_area_lines != '':
                        nocoords = np.loadtxt(io.StringIO(noentry_area_lines), dtype=np.float16)
                        gb.noentry_zone_noentry = self.denormalize_coords(nocoords[:, :], 'noentry')
                    
                    if entry_line != '':
                        nocoords = np.loadtxt(io.StringIO(entry_line), dtype=np.float16)
                        gb.entryLine_noentry = self.denormalize_coords(nocoords[:, :], 'noentry')

                    if exit_line != '':
                        nocoords = np.loadtxt(io.StringIO(exit_line), dtype=np.float16)
                        gb.exitLine_noentry = self.denormalize_coords(nocoords[:, :], 'noentry')

                        # return vehicleArea, lprLine, noEntryArea, entryLine, exitLine
                
            elif dms_type == 'detect_ldms':
                #print("LDMS is zones load:", dms_type, Path(os.path.join(app.device_file_dir, 'ldms', 'config', app.cfg['ldms'].ZONES_FILE)))
                ldms_app_settings_path = None
                if hasattr(app.cfg['ldms'], "ZONES_FILE"):
                    ldms_app_settings_path = Path(os.path.join(app.device_file_dir, 'ldms', 'config', app.cfg['ldms'].ZONES_FILE))
                else:
                    ldms_app_settings_path = Path(os.path.join(app.device_file_dir, 'ldms', 'configs', os.path.basename(app.cfg['ldms'].SCHEDULER.LDMS.ZONES)))

                if ldms_app_settings_path.is_file():
                    zones_file = ldms_app_settings_path
                    
                    #print("from root_screen.py", Path(os.path.join(app.device_file_dir,'ldms', 'config',app.cfg['ldms'].ZONES_FILE)))
                    # zone_coords = np.loadtxt(os.path.join(app.device_file_dir, 'ldms', app.cfg['ldms'].ZONES_FILE), dtype=np.float16)
                    # gb.vehicleArea_ldms = self.denormalize_coords(zone_coords[0:5, 0:2], 'ldms')
                    # gb.rightHArea_ldms = self.denormalize_coords(zone_coords[5:8, 0:2], 'ldms')
                    # gb.leftLine_ldms = self.denormalize_coords(zone_coords[8:10, 0:2], 'ldms')
                    # gb.rightLine_ldms = self.denormalize_coords(zone_coords[10:12, 0:2], 'ldms')
                    # gb.middleLine_ldms = self.denormalize_coords(zone_coords[12:14, 0:2], 'ldms')
                    # gb.trajectoryLine_ldms = self.denormalize_coords(zone_coords[14:16, 0:2], 'ldms')
                    # gb.lprLine_ldms = self.denormalize_coords(zone_coords[16:, 0:2], 'ldms')
                    #gb.rightArea_ldms = self.denormalize_coords(rightArea_coords, 'ldms')
                    #rightArea_coords = zone_coords[4:9, 0:2]
                    # rightArea_coords = np.vstack((
                    #     zone_coords[8:10, 0:2],  # Assuming these are coordinates for the right line
                    #     zone_coords[10:12, 0:2]   # Assuming these are coordinates for the left line
                    # ))
                    
                    left_line = ''
                    right_line = ''
                    middle_line = ''
                    lpr_line = ''
                    lprpoly_line = ''
                    middle_area_lines = ''      
                    right_area_lines = ''        
                    vehicle_area_lines = ''
                    noparking_area_lines = ''
                    trajectory_line = ''
                    lines = ''
                    with open(ldms_app_settings_path) as f:
                        for line in f:
                            if line.startswith('# Left line of middle hatched area'):
                                lines = 'left_line'
                            elif line.startswith('# Right line of middle hatched area'):
                                lines = 'right_line'
                            elif line.startswith('# Middle line coords'):
                                lines = 'middle_line'                    
                            elif line.startswith('# LPR line'):
                                lines = 'lpr_line'
                            elif line.startswith('# LPR poly'):
                                lines = 'lprpoly_line'                    
                            elif line.startswith('# Right hatched area'):
                                lines = 'right_area'
                            elif line.startswith('# Middle hatched area'):
                                lines = 'middle_area'
                            elif line.startswith('# Vehicle tracking zone'):
                                lines = 'vehicle'
                            elif line.startswith('# No parking area'):
                                lines = 'noparking'
                            elif line.startswith('# Trajectory axis'):
                                lines = 'trajectory'
                            elif lines == 'left_line': 
                                left_line += line
                            elif lines == 'right_line': 
                                right_line += line
                            elif lines == 'middle_line': 
                                middle_line += line
                            elif lines == 'lpr_line': 
                                lpr_line += line
                            elif lines == 'lprpoly_line': 
                                lprpoly_line += line
                            elif lines == 'middle_area':
                                middle_area_lines += line
                            elif lines == 'right_area':
                                right_area_lines += line
                            elif lines == 'vehicle':
                                vehicle_area_lines += line
                            elif lines == 'noparking':
                                noparking_area_lines += line
                            elif lines == 'trajectory':
                                trajectory_line += line

                    if left_line != '' and right_line != '':
                        lcoords = np.loadtxt(io.StringIO(left_line), dtype=np.float16)
                        gb.leftLine_ldms = self.denormalize_coords(lcoords[:, :], 'ldms')  
                        rcoords = np.loadtxt(io.StringIO(right_line), dtype=np.float16)
                        gb.rightLine_ldms = self.denormalize_coords(rcoords[:, :], 'ldms')  

                        # append second row first
                        lcoords = np.append(lcoords, rcoords[1:2, :], axis=0)
                        # then first row        
                        coords = np.append(lcoords, rcoords[0:1, :], axis=0)        

                        # middleArea = self.denormalize_coords(coords[:, :], 'ldms')

                    if right_area_lines != '':
                        coords = np.loadtxt(io.StringIO(right_area_lines), dtype=np.float16)
                        gb.rightHArea_ldms = self.denormalize_coords(coords[:, :], 'ldms')         
                        
                    # overwrite middle area from left/right lines if one was explicitly defined in the zones file            
                    # if middle_area_lines != '':
                    #     coords = np.loadtxt(io.StringIO(middle_area_lines), dtype=np.float16)
                    #     middleArea = self.denormalize_coords(coords[:, :], 'ldms')                

                    coords = np.loadtxt(io.StringIO(vehicle_area_lines), dtype=np.float16)
                    gb.vehicleArea_ldms = self.denormalize_coords(coords[:, :], 'ldms')
                    
                    # if noparking_area_lines != '':
                    #     coords = np.loadtxt(io.StringIO(noparking_area_lines), dtype=np.float16)
                    #     noparkingArea = self.denormalize_coords(coords[:, :], 'ldms')

                    if middle_line != '':
                        coords = np.loadtxt(io.StringIO(middle_line), dtype=np.float16)
                        gb.middleLine_ldms = self.denormalize_coords(coords[:, :], 'ldms')

                    #print(gb.lprLine_ldms.size==0,np.unique(gb.lprLine_ldms),len(np.unique(gb.lprLine_ldms)), len(np.unique(gb.lprLine_ldms))>1)
                    if lpr_line != '':
                        coords = np.loadtxt(io.StringIO(lpr_line), dtype=np.float16)
                        gb.lprLine_ldms = self.denormalize_coords(coords[:, :], 'ldms')
                        self.ids.ldms_tab.setOpacity("row_8", 1)
                    else:
                        self.ids.ldms_tab.setOpacity("row_8", 0)

                    if lprpoly_line != '':
                        coords = np.loadtxt(io.StringIO(lprpoly_line), dtype=np.float16)
                        gb.lprpoly_ldms = self.denormalize_coords(coords[:, :], 'ldms')
                        self.ids.ldms_tab.setOpacity("row_9", 1)
                    else:
                        self.ids.ldms_tab.setOpacity("row_9", 0)

                    coords = np.loadtxt(io.StringIO(trajectory_line), dtype=np.float16)
                    gb.trajectoryLine_ldms = self.denormalize_coords(coords[:, :], 'ldms')

    # -------------------------------------------------------------------------------
    # is invoked when a user clicks on the app window
    def on_touch_down(self, touch):
         
        # get coordinates of clicked point
        x, y = int(touch.x), int(self.get_vid_dim()[1] - touch.y)       

        # check for collision of mouse click with image
        if self.ids.video_img.collide_point(*touch.pos):
            ix, iy = self.ids.video_img.pos            
            if self.stream == "ped":
                area = self.ids.ped_tab.selected_area()
                self.ids.ped_tab.on_image_clicked(area, x + ix, y + iy)
            elif self.stream == "mobile":
                area = self.ids.mobile_tab.selected_area()
                self.ids.mobile_tab.on_image_clicked(area, x + ix, y + iy)
            elif self.stream == "noentry":
                area = self.ids.noentry_tab.selected_area()
                self.ids.noentry_tab.on_image_clicked(area, x + ix, y + iy)
            elif self.stream == "ldms":
                area = self.ids.ldms_tab.selected_area()
                self.ids.ldms_tab.on_image_clicked(area, x + ix, y + iy)


        # when we overwrite a method, we must return the same method of the super class
        return super(ConfigRootScreen, self).on_touch_down(touch)

    # -------------------------------------------------------------------------------
    # is invoked every time the user clicks on another tab: switch between ped <-> mobile cameras
    def on_tab_switch(
            self, instance_tabs, instance_tab, instance_tab_label, tab_text
        ):
            '''
            Called when switching tabs.

            :type instance_tabs: <kivymd.uix.tab.MDTabs object>;
            :param instance_tab: <__main__.Tab object>;
            :param instance_tab_label: <kivymd.uix.tab.MDTabsLabel object>;
            :param tab_text: text or name icon of tab;

            '''
            # pass
            # change stream variable; this variable is read at every frame by the root screen to determine the video stream source            
            
            if tab_text == "Mob./Seat.":                    
                self.stream = "mobile"
            elif tab_text == "Pedestrian":
                self.stream = "ped"
            elif tab_text == "NoEntry":
                self.stream = "noentry"
            elif tab_text == "ldms":
                self.stream = "ldms"

    # -------------------------------------------------------------------------------
    def update_img(self):

        try:            
            # try to get next frame from currently selected video source
            # if operation fails the we auto fallback to the last good frames obtained
            # if(not self.first_frame_read_success):
            #     try:                
            #         self.imgs = next(self.video_streams)
            #         self.first_frame_read_success = True
            #     except Exception:
            #         logging.exception("[update_img] Could not obtain next image set from streams")

            # if self.stream == 'ped':         
            #     frame = self.imgs[0]
            #     frame = cv2.resize(frame, self.get_vid_dim(), interpolation = cv2.INTER_AREA)
            #     frame = self.ids.ped_tab.draw_areas(frame)
            # else:
             # self.imgs[1]
            frame = None
            #print(self.stream)
            # print(self.ids.tabs.get_current_tab(), isinstance(self.ids.tabs.get_current_tab(), MobileTab))
            if self.stream == 'ped' and hasattr(self.ids, "ped_tab"):
                frame = deepcopy(self.cameraFrames["pedestrian_camera_uri"])
                #print(hasattr(self.ids,"mobile_tab"))
                frame = self.ids.ped_tab.draw_areas(frame)
                # self.ids.tabs.set_active_item(self.ids.ped_tab)
            elif self.stream == "mobile" and hasattr(self.ids, "mobile_tab"):
                frame = deepcopy(self.cameraFrames["mobile_detection_camera_uri"])
                frame = self.ids.mobile_tab.draw_areas(frame)
                # self.ids.tabs.set_active_item(self.ids.mobile_tab)
            elif self.stream == "noentry" and hasattr(self.ids, "noentry_tab"):
                frame = deepcopy(self.cameraFrames["pedestrian_camera_uri"])
                frame = self.ids.noentry_tab.draw_areas(frame)
                # self.ids.tabs.set_active_item(self.ids.noentry_tab)
            elif self.stream == "ldms" and hasattr(self.ids, "ldms_tab"):
                frame = deepcopy(self.cameraFrames["pedestrian_camera_uri"])
                frame = self.ids.ldms_tab.draw_areas(frame)
                # self.ids.tabs.set_active_item(self.ids.ldms_tab)

            # convert it to texture
            if frame is not None:
                buf1 = cv2.flip(frame, 0)
                buf = buf1.tostring()
                texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb') 
                texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')

                self.ids.video_img.texture = texture 

            else:
                print("Frame is NONE ", isinstance(self.ids.tabs.get_current_tab(), MobileTab))          

        except Exception as e:
            logging.exception(f"[update_img] Error while updating frame from video stream : {e}") 

    # helper method: returns the dimensions of the video from selected source
    def get_vid_dim(self):
        if self.stream == 'ped':
            return (self.video_width[0], self.video_height[0])            
        elif self.stream == 'mobile':
            return (self.video_width[1], self.video_height[1])
        elif self.stream == 'noentry':
            return (self.video_width[0], self.video_height[0])
        elif self.stream == 'ldms':
            return (self.video_width[0], self.video_height[0])

    def construct_yaml(self, user_dict:dict, format_dict):

        # self-recursive function
        def update_dict(l_new_dict, key, value):
            if "-" not in key:
                l_new_dict[key] = value.text
                return
            else:
                subkey = key.split('-')
                if subkey[0] not in l_new_dict.keys():
                    l_new_dict[subkey[0]] = {} #create a new entry

                update_dict(l_new_dict[subkey[0]], "-".join(subkey[1:]), value)

        # self-recursive function
        def validate_and_update_values_to_original_format(l_new_dict:dict, formatter_dict:dict):
            global errorMessage
            for k1 in l_new_dict.keys():
                if not isinstance(l_new_dict[k1], dict):
                    try:
                        if formatter_dict[k1][0] == 'str':
                                l_new_dict[k1] = str(l_new_dict[k1]).strip()
                                # make sure user specified value in the options
                                # TODO: this works, but need to implement a new rule (STRICT_CHECK=True/False) in FORMAT yaml doc
                                # if ((len(formatter_dict[k1])>2) and (len(formatter_dict[k1][3:-1])>0) 
                                #     and (str(l_new_dict[k1]).strip() in formatter_dict[k1][3:-1])):
                                #     l_new_dict[k1] = str(l_new_dict[k1]).strip()
                        elif formatter_dict[k1][0] == 'int':
                            l_new_dict[k1] = int(l_new_dict[k1])
                        elif formatter_dict[k1][0] == 'float':
                            l_new_dict[k1] = float(l_new_dict[k1])
                        elif formatter_dict[k1][0] == 'bool':
                            if l_new_dict[k1].strip().lower() == "true":
                                l_new_dict[k1] = True
                            elif l_new_dict[k1].strip().lower() == "false":
                                l_new_dict[k1] = False
                            else:
                                errorMessage += f'Invalid value at {k1} - Only TRUE or FALSE allowed. Double check spelling\n'
                        elif formatter_dict[k1][0] == 'list':
                            l_new_dict[k1] = l_new_dict[k1].strip().split(',')
                    except Exception as e:
                        errorMessage += f'Invalid value at {k1} - Exception: {e}\n'
                else:
                    validate_and_update_values_to_original_format(l_new_dict[k1], formatter_dict[k1])

        new_dicts = {}
        for k1 in user_dict.keys():
            #print(k1)
            update_dict(new_dicts, k1, user_dict[k1])

        validate_and_update_values_to_original_format(new_dicts, format_dict) #self.ids.settings_tab.cfg_format)

        return new_dicts

    def populate_tabs(self, _):

        app = MDApp.get_running_app()
        for active_serv in app.dms_types:
            if active_serv == 'detect':
                newTab = PedTab(title="Pedestrian")
                self.ids.tabs.add_widget(newTab)
                self.ids["ped_tab"] = weakref.ref(newTab)
                # self.stream = "ped"
            elif active_serv == 'detect_mobile':
                newTab = MobileTab(title="Mob./Seat.")
                self.ids.tabs.add_widget(newTab)
                self.ids["mobile_tab"] = weakref.ref(newTab)
                # self.stream = "mobile"
            elif active_serv == 'detect_noentry':
                newTab = NoentryTab(title="NoEntry")
                self.ids.tabs.add_widget(newTab)
                self.ids["noentry_tab"] = weakref.ref(newTab)
                # self.stream = "noentry"
            elif active_serv == 'detect_ldms':
                newTab = LdmsTab(title="ldms")
                self.ids.tabs.add_widget(newTab)
                self.ids["ldms_tab"] = weakref.ref(newTab)
                # self.stream = "ldms"

            if isinstance(self.ids.tabs.get_current_tab(), MobileTab):
                self.stream = "mobile"
            elif isinstance(self.ids.tabs.get_current_tab(), PedTab):
                self.stream = "ped"
            elif isinstance(self.ids.tabs.get_current_tab(), NoentryTab):
                self.stream = "noentry"
            elif isinstance(self.ids.tabs.get_current_tab(), LdmsTab):
                self.stream = "ldms"

        self.load_coords(app)


    def populate_yaml_configs(self, dt):
    #     # Get instance of application object
        app = MDApp.get_running_app()

    #     print("INSIDE---------------->>>>>>>app.dms_types", app.dms_types)
        
    #     result = list(Path(app.device_file_dir).rglob("*.[yY][aA][mM][lL]"))
    #     for settings_file_path in result:
    #         title = os.path.splitext(os.path.basename(settings_file_path))[0]
            
    #         if 'detect_ldms' in app.dms_types and 'detect_mobile' in app.dms_types:
    #             if 'config_ldms' in os.path.basename(settings_file_path):
    #                 settings_format_file_path = os.path.join(Path(__file__).parents[1], "app_settings_format_ldms.yaml")
    #                 app.cfg['ldms'] = YamlParser(config_file=settings_file_path)
    #                 print("ldms config_file opens here --->>>", settings_format_file_path)
    #             elif 'config' in os.path.basename(settings_file_path):
    #                 settings_format_file_path = os.path.join(Path(__file__).parents[1], "app_settings_format.yaml")
    #                 app.cfg['pms'] = YamlParser(config_file=settings_file_path)
    #                 print("pms config_file opens here --->>>", settings_format_file_path)
    #         elif 'detect_ldms' in app.dms_types:
    #             if 'config_ldms' in os.path.basename(settings_file_path):
    #                 settings_format_file_path = os.path.join(Path(__file__).parents[1], "app_settings_format_ldms.yaml")
    #                 app.cfg['ldms'] = YamlParser(config_file=settings_file_path)
    #                 print("ldms config_file opens here --->>>", settings_format_file_path)
    #         elif 'detect_mobile' in app.dms_types:
    #             if 'config' in os.path.basename(settings_file_path):
    #                 settings_format_file_path = os.path.join(Path(__file__).parents[1], "app_settings_format.yaml")
    #                 app.cfg['pms'] = YamlParser(config_file=settings_file_path)
    #                 print("pms config_file opens here --->>>", settings_format_file_path)
            
    #         # Create a new settings tab and add it to the list of settings tabs and to the UI
    #         new_tab = SettingsTab(settings_file_path=settings_file_path, settings_format_file_path=settings_format_file_path, title=title)
    #         self.settings_tabs.append(new_tab)
    #         self.ids.tabs.add_widget(new_tab)
            # if "inference_manager_settings_format" in settings_format_file_path:
            #     break
                # elif "app_settings" in os.path.basename(settings_file_path):
                #     settings_format_file_path = os.path.join(Path(__file__).parents[1], "app_settings_format_ldms.yaml")
        result = list(Path(app.device_file_dir).rglob("app_settings.[yY][aA][mM][lL]"))
        for settings_file_path in result:
            if "config" not in os.path.basename(Path(settings_file_path).parent) :
                continue
            # print("root", os.path.basename(Path(settings_file_path).parent.parent))
            # title = settings_type + filename
            # eg. ldms + app_settings
            dms_type = os.path.basename(Path(settings_file_path).parent.parent)
            title = dms_type.upper() + ":" + os.path.splitext(os.path.basename(settings_file_path))[0]
            if dms_type == 'ldms': #'config_ldms' in settings_file_path and
                #print("Inside detect_ldms--------->>>>>>>setting_file_path")
                if hasattr(app.cfg['ldms'], "ZONES_FILE"):
                    settings_format_file_path = os.path.join(Path(__file__).parents[1], "app_settings_format_ldms1.yaml")
                else:
                    settings_format_file_path = os.path.join(Path(__file__).parents[1], "app_settings_format_ldms.yaml")



                # settings_format_file_path = os.path.join(Path(__file__).parents[1], "app_settings_format_ldms.yaml") # go two steps back and 
            # elif (('detect_mobile' in app.dms_types) and ('detect_ldms' in app.dms_types)):
            #     if "app_settings" in os.path.basename(settings_file_path):
            #         settings_format_file_path = os.path.join(Path(__file__).parents[1], "app_settings_format.yaml") # go two steps back and 
            #     elif "app_settings" in os.path.basename(settings_file_path):
            #         settings_format_file_path = os.path.join(Path(__file__).parents[1], "app_settings_format_ldms.yaml")
            elif ((dms_type == 'pms')):
                settings_format_file_path = os.path.join(Path(__file__).parents[1], "app_settings_format.yaml") # go two steps back and  

            # Create a new settings tab and add it to the list of settings tabs and to the UI
            new_tab = SettingsTab(settings_file_path=settings_file_path, settings_format_file_path=settings_format_file_path, title=title)
            self.settings_tabs.append(new_tab) 
            self.ids.tabs.add_widget(new_tab)
            # if "inference_manager_settings_format" in settings_format_file_path:
            #     break
    
    # -------------------------------------------------------------------------------
    # Save all data entered by the user to 3 files: settings.yaml, ped zones, mobile/seatbelt zones
    def save(self):
        # self.show_message_dialog("INFO", "Saving... please wait")
        # global errorMessage
        # errorMessage = ''
        # app = MDApp.get_running_app()
        # for tabs in self.settings_tabs:
        #     yaml_dict = self.construct_yaml(tabs.ids.dynamic_ui_update.text_fields, tabs.cfg_format)
        #     if errorMessage != '':
        #         self.show_message_dialog("ERROR", errorMessage)
        #         return
        #     else:	
        #         with open(tabs.settings_file_path, "w") as f:
        #             #write the warning code here
        #             yaml.safe_dump(yaml_dict, f)
        # self.show_message_dialog("INFO", "Saving... please wait")
        global errorMessage
        errorMessage = ''

        app = MDApp.get_running_app()

        # Create the accept dialog
        self.accept_dialog = MDDialog(
            text="Are you sure you want to save the settings?",
            buttons=[
                MDFlatButton(
                    text="Accept",
                    text_color=self.theme_cls.primary_color,
                    on_release=lambda x: self.proceed_save()
                ),
                MDFlatButton(
                    text="Decline",
                    text_color=self.theme_cls.primary_color,
                    on_release=lambda x: self.close_dialog_n()
                ),
            ],
        )
        self.accept_dialog.open()

    def close_dialog_n(self):
        self.accept_dialog.dismiss()


    def proceed_save(self):
        """Function to handle the actual saving process after confirmation."""
        self.accept_dialog.dismiss()  # Close the dialog
        app = MDApp.get_running_app()
        global errorMessage
        errorMessage = ''

        for tabs in self.settings_tabs:
            yaml_dict = self.construct_yaml(
                tabs.ids.dynamic_ui_update.text_fields,
                tabs.cfg_format
            )

            # Check for errors
            if errorMessage != '':
                self.show_message_dialog("ERROR", errorMessage)
                return

            # Proceed to save if no errors
        
            with open(tabs.settings_file_path, "w") as f:
                # Write the warning/status to the file before saving
                f.write("# Warning: Modifying this file manually may cause issues.\n")
                yaml.safe_dump(yaml_dict, f)
        if 'detect' in app.dms_types:
            # --- Data validation (all required fields must be there)            
            errorMessage = ''
            
            if gb.greenArea.size < 8:
                errorMessage = 'Green zone is not defined\n' 

            if gb.violetArea.size < 8:
                errorMessage += 'Violet zone is not defined\n' 

            if gb.leftLine.size < 4:
                errorMessage += 'Ped. left line is not defined\n' 

            if gb.rightLine.size < 4:
                errorMessage += 'Ped. right line is not defined\n' 

            if gb.middleLine.size < 4:
                errorMessage += 'Middle line is not defined\n' 

            if gb.entryLine.size < 4:
                errorMessage += 'Entry line is not defined\n' 

            if gb.exitLine.size < 4:
                errorMessage += 'Exit line is not defined\n' 

            if gb.redLine.size < 4:
                errorMessage += 'Red line is not defined\n' 

            if gb.lprLine.size < 4:
                errorMessage += 'LPR line is not defined\n' 

            if gb.vehicleArea.size < 8:
                errorMessage += 'Vehicle tracking zone is not defined\n' 

            if gb.detectionLine.size < 4:
                errorMessage += 'Mobile/Seatbelt detection line is not defined\n'

            if gb.tintDetectZone.size < 4:
                errorMessage += 'Mobile/Seatbelt tint zone is not defined\n' 

            if errorMessage != '':
                self.show_message_dialog("ERROR", errorMessage)
                return
            else:					            
                greenCoords = np.reshape(gb.greenArea, (1, 4, 2))            
                violetCoords = np.reshape(gb.violetArea, (1, 4, 2))        
                areaCoords = np.concatenate([greenCoords, violetCoords], axis = 0)            

                redCoords = np.reshape(gb.redLine, (1, 2, 2))
                lprCoords = np.reshape(gb.lprLine, (1, 2, 2))
                middleCoords = np.reshape(gb.middleLine, (1, 2, 2))
                entryCoords = np.reshape(gb.entryLine, (1, 2, 2))
                exitCoords = np.reshape(gb.exitLine, (1, 2, 2))
                leftCoords = np.reshape(gb.leftLine, (1, 2, 2))
                rightCoords = np.reshape(gb.rightLine, (1, 2, 2))

                lineCoords = np.concatenate([redCoords, lprCoords, middleCoords, entryCoords, exitCoords, leftCoords, rightCoords], axis = 0)                        
                
                # --- Write ped zones/line to disk            
                # https://stackoverflow.com/questions/3685265/how-to-write-a-multidimensional-array-to-a-text-file
                
                zones_file = os.path.join(app.device_file_dir, 'pms', app.cfg['pms'].DETECTIONS.PED.ZONES_FILE) #app.cfg['pms'].DETECTIONS.PED.ZONES_FILE

                with open(zones_file, 'w') as outfile:			

                    # Iterating through a ndimensional array produces slices along
                    # the last axis. This is equivalent to data[i,:,:] in this case
                    i = 0
                    for data_slice in areaCoords:
                        i += 1

                        # Writing out a break to indicate different slices...
                        if i == 1:                         
                            outfile.write('# Green zone coords\n')
                        elif i == 2:
                            outfile.write('# Violet zone coords\n')

                        # The formatting string indicates that I'm writing out
                        # the values in left-justified ('-') columns 8 characters in width
                        # with integer values
                        np.savetxt(outfile, self.normalize_coords(data_slice, "ped"), fmt='%-1.6f')

                    for data_slice in lineCoords:
                        i += 1

                        if i == 3:
                            outfile.write('# Red line coords\n')
                        elif i == 4:
                            outfile.write('# LPR line coords\n')
                        elif i == 5:
                            outfile.write('# Middle line coords\n')                                        
                        elif i == 6:
                            outfile.write('# Entry line coords\n')                                        
                        elif i == 7:
                            outfile.write('# Exit line coords\n')                                        
                        elif i == 8:
                            outfile.write('# Ped. left line coords\n')                                        
                        elif i == 9:
                            outfile.write('# Ped. right line coords\n')            

                        np.savetxt(outfile, self.normalize_coords(data_slice, "ped"), fmt='%-1.6f')
        if 'detect_mobile' in app.dms_types:
            # --- Write mobile/seatbelt zones/line to disk            
            zoneCoords = np.reshape(gb.vehicleArea, (1, int(gb.vehicleArea.size / 2), 2)) 
            lineCoords = np.reshape(gb.detectionLine, (1, 2, 2))  
            zoneCoords_tint = np.reshape(gb.tintDetectZone, (1, int(gb.tintDetectZone.size / 2), 2))
            zoneCoords_lpr = np.reshape(gb.lprpoly, (1, int(gb.lprpoly.size / 2), 2))
            zones_file = os.path.join(app.device_file_dir, "pms", app.cfg['pms'].DETECTIONS.MOBI.ZONES_FILE)

            with open(zones_file, 'w') as outfile:			                
                outfile.write('# Vehicle tracking zone\n')
                np.savetxt(outfile, self.normalize_coords(zoneCoords[0], 'mobi'), fmt='%-1.6f')
                outfile.write('# Detection line; only vehicles having crossed this line are considered for detections\n')
                np.savetxt(outfile, self.normalize_coords(lineCoords[0], 'mobi'), fmt='%-1.6f')
                outfile.write('# Tint detect zone\n')
                np.savetxt(outfile, self.normalize_coords(zoneCoords_tint[0], 'mobi'), fmt='%-1.6f')
                outfile.write('# LPR zone\n')
                np.savetxt(outfile, self.normalize_coords(zoneCoords_lpr[0], 'mobi'), fmt='%-1.6f')

        # zones_file_name = "zones_dms09_noentry.txt"
        if 'detect_noentry' in app.dms_types:
            # --- Data validation (all required fields must be there)
            errorMessage = ''
            
            if gb.vehicleArea_noentry.size < 8:
                errorMessage = 'vehicleArea zone is not defined\n' 
            
            if gb.lprLine_noentry.size < 4:
                errorMessage = 'lpr zone is not defined\n' 
            
            if gb.noentry_zone_noentry.size < 8:
                errorMessage = 'noentry zone is not defined\n'

            if gb.entryLine_noentry.size < 4:
                errorMessage = 'entry zone is not defined\n' 

            if gb.exitLine_noentry.size < 4:
                errorMessage = 'exit zone is not defined\n' 

            if errorMessage != '':
                self.show_message_dialog("ERROR", errorMessage)
                return
            else:
                # Reshape and concatenate safely
                zoneCoords_v = np.reshape(gb.vehicleArea_noentry, (1, int(gb.vehicleArea_noentry.size / 2), 2)) 
                lprCoords_noentry = np.reshape(gb.lprLine_noentry, (1, 2, 2))
                zoneCoords_ne = np.reshape(gb.noentry_zone_noentry, (1, int(gb.noentry_zone_noentry.size / 2), 2))
                entryCoords_noentry = np.reshape(gb.entryLine_noentry, (1, 2, 2))
                exitCoords_noentry = np.reshape(gb.exitLine_noentry, (1, 2, 2)) 
                lineCoords_noentry = np.concatenate([lprCoords_noentry, entryCoords_noentry, exitCoords_noentry], axis=0)

                # Write to a no-entry zones file
                zones_file = os.path.join(app.device_file_dir, "pms", app.cfg['pms'].DETECTIONS.NOENTRY.ZONES_FILE)
                with open(zones_file, 'w') as outfile:
                    outfile.write('# Vehicle tracking zone\n')
                    np.savetxt(outfile, self.normalize_coords(zoneCoords_v[0], 'noentry'), fmt='%-1.6f')
                    outfile.write('# No-entry zone\n')                                  
                    np.savetxt(outfile, self.normalize_coords(zoneCoords_ne[0], 'noentry'), fmt='%-1.6f')
                    i = 0
                    for data_slice in lineCoords_noentry:
                        i += 1
                        if i == 1:
                            outfile.write('# LPR line coords\n')                                  
                        elif i == 2:
                            outfile.write('# Entry line coords\n')                                        
                        elif i == 3:
                            outfile.write('# Exit line coords\n')                                                                          

                        np.savetxt(outfile, self.normalize_coords(data_slice, "noentry"), fmt='%-1.6f')
        if 'detect_ldms' in app.dms_types:
            # --- Data validation (all required fields must be there)
            errorMessage = ''
            
            # if gb.vehicleArea_ldms.size < 8:
            #     errorMessage = 'vehicleArea zone is not defined\n' 

            # if gb.leftLine_ldms.size < 4:
            #     errorMessage = 'Left Line zone is not defined\n' 

            # if gb.rightLine_ldms.size < 4:
            #     errorMessage = 'Right Line zone is not defined\n' 

            # if gb.rightHArea_ldms.size < 6:
            #     errorMessage = 'right area is not defined\n' 

            # if gb.middleLine_ldms.size < 4:
            #     errorMessage = 'Middle line is not defined\n' 

            # if gb.trajectoryLine_ldms.size < 4:
            #     errorMessage = 'trajectory line is not defined\n'
            
            # # if gb.lprLine_ldms.size < 4:
            # #     errorMessage = 'Lpr line is not defined\n'
            # if gb.lprpoly_ldms.size < 8:
            #      errorMessage = 'Lpr poly is not defined\n'

            if errorMessage != '':
                self.show_message_dialog("ERROR", errorMessage)
                return
            else:
                # Reshape and concatenate safely
                # Write to a ldms zones file
                zoneCoords_vl = np.reshape(gb.vehicleArea_ldms, (1, int(gb.vehicleArea_ldms.size / 2), 2))
                #zoneCoords_r = np.reshape(gb.rightArea_ldms, (1, int(gb.rightArea_ldms.size / 2), 2))
                zoneCoords_r =  np.reshape(gb.rightHArea_ldms, (1, int(gb.rightHArea_ldms.size / 2), 2))
                rightLine_ldms = np.reshape(gb.rightLine_ldms, (1, 2, 2))
                leftLine_ldms = np.reshape(gb.leftLine_ldms,(1, 2, 2))
                #zoneCoords_lr = np.reshape(gb.rightArea_ldms, (1, gb.rightLine_ldms.shape[0], gb.leftLine_ldms.shape[1]))
                #areaCoords_ldms = np.concatenate([zoneCoords_vl, zoneCoords_r], axis = 0) #, zoneCoords_lr, zoneCoords_r
                trajectoryLine_ldms = np.reshape(gb.trajectoryLine_ldms, (1, 2, 2)) 
                middleLine_ldms = np.reshape(gb.middleLine_ldms, (1, 2, 2))
                lprLine_ldms = np.zeros(shape=(1, 2, 2))
                if gb.lprLine_ldms.size != 0:
                    lprLine_ldms = np.reshape(gb.lprLine_ldms, (1, 2, 2))
                zoneCoords_lp= np.reshape(gb.lprpoly_ldms, (1, int(gb.lprpoly_ldms.size / 2), 2))
                lineCoords_ldms = np.concatenate([leftLine_ldms, rightLine_ldms, middleLine_ldms, trajectoryLine_ldms, lprLine_ldms], axis=0)
                #gb.rightArea_ldms = self.denormalize_coords(rightArea_coords, 'ldms')

                # Write to a ldms zones file
                ldms_app_settings_path = None
                if hasattr(app.cfg['ldms'], "ZONES_FILE"):
                    ldms_app_settings_path = Path(os.path.join(app.device_file_dir, 'ldms', 'config', app.cfg['ldms'].ZONES_FILE))
                else:
                    ldms_app_settings_path = Path(os.path.join(app.device_file_dir, 'ldms', 'configs', os.path.basename(app.cfg['ldms'].SCHEDULER.LDMS.ZONES)))

                zones_file = ldms_app_settings_path
                
                # existing_coords = {}
                # if os.path.exists(zones_file):
                #     with open(zones_file, 'r') as infile:
                #         contents = infile.readlines()
                #         for line in contents:
                #             if "# Vehicle tracking zone" in line:
                #                 existing_coords["vehicle_tracking"] = zoneCoords_vl
                #             elif "# Right hatched area" in line:
                #                 existing_coords["right_hatched"] = zoneCoords_r
                #             elif "# LPR poly coords" in line:
                #                 existing_coords["lpr_poly"] = zoneCoords_lp
                #             elif "# Left line of middle hatched area" in line:
                #                 existing_coords["left_line"] = lineCoords_ldms[0]
                #             elif "# Right line of middle hatched area" in line:
                #                 existing_coords["right_line"] = lineCoords_ldms[1]
                #             elif "# Middle line coords" in line:
                #                 existing_coords["middle_line"] = lineCoords_ldms[2]
                #             elif "# Trajectory axis" in line:
                #                 existing_coords["trajectory_axis"] = lineCoords_ldms[3]
                #             elif "# LPR line coords" in line:
                #                 existing_coords["lpr_line"] = lineCoords_ldms[4]
                with open(zones_file, 'w') as outfile:
                    outfile.write('# Vehicle tracking zone\n')
                    np.savetxt(outfile, self.normalize_coords(zoneCoords_vl[0], 'ldms'), fmt='%-1.6f')
                    outfile.write('# Right hatched area\n')
                    np.savetxt(outfile, self.normalize_coords(zoneCoords_r[0], 'ldms'), fmt='%-1.6f')

                    if gb.lprpoly_ldms.size != 0:
                        outfile.write('# LPR poly coords\n')
                        np.savetxt(outfile, self.normalize_coords(zoneCoords_lp[0], 'ldms'), fmt='%-1.6f')

                    # for i, key in enumerate(["left_line", "right_line", "middle_line", "trajectory_axis", "lpr_line"]):
                    #     if key in existing_coords and existing_coords[key] is not None:
                    #         if i == 0:
                    #             outfile.write("# Left line of middle hatched area\n")
                    #         elif i == 1:
                    #             outfile.write("# Right line of middle hatched area\n")
                    #         elif i == 2:
                    #             outfile.write("# Middle line coords\n")
                    #         elif i == 3:
                    #             outfile.write("# Trajectory axis\n")
                    #         elif i == 4:
                    #             outfile.write("# LPR line coords\n")
                    #         np.savetxt(outfile, self.normalize_coords(existing_coords[key], "ldms"), fmt='%-1.6f')

                    i = 0
                    for data_slice in lineCoords_ldms:
                        i += 1
                        if len(np.unique(data_slice))<=1:
                            continue

                        if i == 1:
                            outfile.write("# Left line of middle hatched area\n")
                        elif i == 2:
                            outfile.write("# Right line of middle hatched area\n")
                        elif i == 3:
                            outfile.write('# Middle line coords\n')
                        elif i == 4:
                            outfile.write('# Trajectory axis\n')                     
                        elif i == 5:
                            outfile.write('# LPR line coords\n')  
                                                                                                                                                                  
                        np.savetxt(outfile, self.normalize_coords(data_slice, "ldms"), fmt='%-1.6f')

                '''
                with open(zones_file, 'w') as outfile:
                    outfile.write('# Vehicle tracking zone\n')
                    np.savetxt(outfile, self.normalize_coords(zoneCoords_vl[0], 'ldms'), fmt='%-1.6f')
                    outfile.write('# Right hatched area\n')
                    np.savetxt(outfile, self.normalize_coords(zoneCoords_r[0], 'ldms'), fmt='%-1.6f')
                    outfile.write('# LPR poly coords\n')
                    np.savetxt(outfile, self.normalize_coords(zoneCoords_lp[0], 'ldms'), fmt='%-1.6f')
                    i = 0
                    for data_slice in lineCoords_ldms:
                        i += 1
                        if i ==1:
                            outfile.write("# Left line of middle hatched area\n")
                        elif i == 2:
                            outfile.write("# Right line of middle hatched area\n")
                        elif i == 3:
                            outfile.write('# Middle line coords\n')
                        elif i == 4:
                            outfile.write('# Trajectory axis\n')                          
                        elif i == 5:
                            outfile.write('# LPR line coords\n')                                                                                                                                               
                        np.savetxt(outfile, self.normalize_coords(data_slice, "ldms"), fmt='%-1.6f')
                '''
        device_ip = os.path.basename(app.device_file_dir)[13:].replace('_','.')
        retVal = remote_works.save_dms_configs(device_ip, app.device_file_dir, app.dms_types, change_details=None)

        if retVal == "SUCCESS":
            self.restart_dialog = MDDialog(text=f"File save status : {retVal}. Changes will affect only after device restart",
                                            buttons=[
                                                MDFlatButton(
                                                    # https://stackoverflow.com/questions/41817607/python-kivy-assertionerror-none-is-not-callable-error-on-function-call-by-b
                                                    text="Restart now", text_color=self.theme_cls.primary_color, on_release = lambda x: self.device_restart(device_ip)
                                                ),
                                                MDFlatButton(
                                                    # https://stackoverflow.com/questions/41817607/python-kivy-assertionerror-none-is-not-callable-error-on-function-call-by-b
                                                    text="Restart later", on_release = lambda x: self.close_dialog('restart')
                                                ),
                                            ])
            self.restart_dialog.open()
        else:
            self.show_message_dialog("INFO", f"File save status : {retVal}")

    def device_restart(self, device_ip):
        self.close_dialog('restart')
        
        self.show_message_dialog("INFO", f"Restarting {device_ip}. Please wait")
        remote_works.restart_device(device_ip)
        self.show_message_dialog("INFO", f"Device restarted - {device_ip}")

    # -------------------------------------------------------------------------------
    # invoke when the exit button is pressed
    def exit(self):        
        if not self.exit_dialog:
            self.exit_dialog = MDDialog(                
                text="Do you really want to exit? DO YOU?",
                buttons=[
                    MDFlatButton(
                        # https://stackoverflow.com/questions/41817607/python-kivy-assertionerror-none-is-not-callable-error-on-function-call-by-b
                        text="Cancel", text_color=self.theme_cls.primary_color, on_release = lambda x: self.close_dialog('exit')
                    ),
                    MDFlatButton(
                        # https://stackoverflow.com/questions/41817607/python-kivy-assertionerror-none-is-not-callable-error-on-function-call-by-b
                        text="Yes", text_color=self.theme_cls.primary_color, on_release = self.exit_mdapp()
                    ),
                ]
            )
        self.exit_dialog.open()

    def exit_mdapp(self):
        app = MDApp.get_running_app()
        app.stop()
        Window.close()
        return True
    
    # ------------------------------------------------------------------------------
    # show specified message on dialog; dialog instance is created only the first time function is invoked
    def show_message_dialog(self, title, msg):        
        if self.message_dialog:
            self.close_dialog('message')

        self.message_dialog = MDDialog(
            title=title,
            text=msg,
            buttons=[
                MDFlatButton(
                    # https://stackoverflow.com/questions/41817607/python-kivy-assertionerror-none-is-not-callable-error-on-function-call-by-b
                    text="OK", text_color=self.theme_cls.primary_color, on_release = lambda x: self.close_dialog('message')
                ),
            ],
        )

        self.message_dialog.open()

    # -------------------------------------------------------------------------------
    def close_dialog(self, dlg):
        if dlg == 'message' and self.message_dialog:
            self.message_dialog.dismiss()
        elif dlg == 'exit' and self.exit_dialog:                   
            self.exit_dialog.dismiss()
        elif dlg == 'restart' and self.restart_dialog:
            if self.message_dialog:
                self.message_dialog.dismiss()
            self.restart_dialog.dismiss()

    # -------------------------------------------------------------------------------
    # helper method: normalizes all coordinates with respect to the resolution ped / mobile video cameras
    def normalize_coords(self, coords, src):
        if src == "ped":
            # normalization vector for ped camera
            v = np.array([self.video_width[0], self.video_height[0]])
        elif src =="mobi":
            # normalization vector for mobile camera
            v = np.array([self.video_width[1], self.video_height[1]])            
        elif src =="noentry":
            # normalization vector for ped camera
            v = np.array([self.video_width[0], self.video_height[0]])
        elif src =="ldms":
            # normalization vector for ped camera
            v = np.array([self.video_width[0], self.video_height[0]])            
        return coords / v[None,:]

    def denormalize_coords(self, coords, src):
        if src == "ped":
            # normalization vector for ped camera
            v = np.array([self.video_width[0], self.video_height[0]])
        elif src == "mobi":
            # normalization vector for mobile camera
            v = np.array([self.video_width[1], self.video_height[1]])            
        elif src == "noentry":
            # normalization vector for ped camera
            v = np.array([self.video_width[0], self.video_height[0]])
        elif src == "ldms":
            # normalization vector for ped camera
            v = np.array([self.video_width[0], self.video_height[0]])      
        ret = coords * v[None,:]                
        return ret.astype(int)
