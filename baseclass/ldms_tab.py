import sys
import cv2
import numpy as np

from kivymd.app import MDApp
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.gridlayout import GridLayout
from kivy.properties import BooleanProperty
from pathlib import Path

import globals as gb

class LdmsTab(GridLayout, MDTabsBase):
    '''Class implementing content for the areas / lines tab.'''
    message_dialog = None
    exit_dialog = None
    

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # get instance of application object
        app = MDApp.get_running_app()

        # init themes
        self.theme_cls = app.theme_cls

        
        # self.ids["ldms_tab"]

        # self.isShownLDMSLine = True

    def setOpacity(self, idx, val):
        self.ids[idx].opacity=val

    # ---------------------------------------------------------------------------------
    # is called by the parent container whenever the video frame has been clicked
    def on_image_clicked(self, area, x, y):   
        #print(area)               
        if area == 'vehicle' and gb.vehicleArea_ldms.size < 12:
            gb.vehicleArea_ldms = np.append(gb.vehicleArea_ldms, np.array([[x, y]]), axis=0)
            #print(area)
        elif area == 'left' and gb.leftLine_ldms.size < 4:
            gb.leftLine_ldms = np.append(gb.leftLine_ldms, np.array([[x, y]]), axis=0)
        elif area == 'right' and gb.rightLine_ldms.size < 4:
            gb.rightLine_ldms = np.append(gb.rightLine_ldms, np.array([[x, y]]), axis=0)
        elif area == 'righth' and gb.rightHArea_ldms.size < 8:
            gb.rightHArea_ldms = np.append(gb.rightHArea_ldms, np.array([[x, y]]), axis=0)
            #print(area)
        elif area == 'middle' and gb.middleLine_ldms.size < 4:
            gb.middleLine_ldms = np.append(gb.middleLine_ldms, np.array([[x, y]]), axis=0)
            #print(area)
        elif area == 'trajectory' and gb.trajectoryLine_ldms.size < 4:
            gb.trajectoryLine_ldms = np.append(gb.trajectoryLine_ldms, np.array([[x, y]]), axis=0)
            #print(area)
        elif area == 'lpr' and gb.lprLine_ldms.size < 4:
            gb.lprLine_ldms = np.append(gb.lprLine_ldms, np.array([[x, y]]), axis=0)
            #print(area)
        elif area == 'lprpoly' and gb.lprpoly_ldms.size < 12:
            gb.lprpoly_ldms = np.append(gb.lprpoly_ldms, np.array([[x, y]]), axis=0)
    # ---------------------------------------------------------------------------------
    # Draw user selection on current frame for vehicle tracking zone, detection line
    def draw_areas(self, frame):

        for col in ['vehicle', 'left','right', 'righth','middle','trajectory','lpr','lprpoly']:
            # print(col)
            if col == 'vehicle':
                area = gb.vehicleArea_ldms
                color = (0, 255, 50)
            elif col == 'left':
                area = gb.leftLine_ldms
                color = (0, 0, 255)
            elif col == 'right':
                color = (255,0,45) 
                area = gb.rightLine_ldms
            elif col == 'righth':
                area = gb.rightHArea_ldms
                color = (255, 165, 0)
            elif col == 'middle':
                area = gb.middleLine_ldms
                color = (0, 0, 255)
            elif col == 'trajectory':
                area = gb.trajectoryLine_ldms
                color = (40, 40, 255)
            elif col == 'lpr':
                area = gb.lprLine_ldms
                color = (255, 255, 50)
            elif col == 'lprpoly':
                area = gb.lprpoly_ldms
                color = (250, 0, 50)
            
            if area.size == 2:
                # print("pt")
                cv2.circle(frame, (area[0, 0], area[0, 1]), 2, color, 2)
            else:
                if area.size >= 8:                                        
                    area = area[0:area.size, 0:2]					
                    isClosed = True
                else:
                    isClosed = False

                vertices = area.reshape(-1,1,2)
                # print("ply")
                frame = cv2.polylines(frame, [vertices], isClosed, color, 2)                
        # cv2.imshow("as",frame)
        return frame #cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # ---------------------------------------------------------------------------------
    # clear the selection made on the specified area
    def clear_area(self, col):   
        #print("clear --- ", col)            
        if col == 'vehicle':            
            gb.vehicleArea_ldms = np.empty(shape=(0,2), dtype= np.int16)    
        elif col == 'left':
            gb.leftLine_ldms = np.empty(shape=(0,2), dtype= np.int16)
        elif col == 'right':
            gb.rightLine_ldms = np.empty(shape=(0,2), dtype= np.int16)        
        elif col == 'righth':
            gb.rightHArea_ldms = np.empty(shape=(0,2), dtype= np.int16)
        elif col == 'middle':
            gb.middleLine_ldms = np.empty(shape=(0,2), dtype= np.int16)
        elif col == 'trajectory':
            gb.trajectoryLine_ldms = np.empty(shape=(0,2), dtype= np.int16)
        elif col == 'lpr':
            gb.lprLine_ldms = np.empty(shape=(0,2), dtype= np.int16)
        elif col == 'lprpoly':
            gb.lprpoly_ldms = np.empty(shape=(0,2), dtype= np.int16)

    # ---------------------------------------------------------------------------------
    # returns the name currently selected area (in the radioboxes)
    def selected_area(self):
        if self.ids.chk_vehicle_tracking_ldms.active:
            return 'vehicle'
        elif self.ids.chk_Left.active:
            return 'left'
        elif self.ids.chk_Right.active:
            return 'right'
        elif self.ids.chk_Righth.active:
            return 'righth'        
        elif self.ids.chk_Middle.active:
            return 'middle'
        elif self.ids.chk_Trajectory.active:
            return 'trajectory'
        elif self.ids.chk_LPR.active:
            return 'lpr'
        elif self.ids.chk_lprpoly.active:
            return 'lprpoly'
        else:
            return None


