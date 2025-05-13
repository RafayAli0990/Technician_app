import cv2
import numpy as np

from kivymd.app import MDApp
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.gridlayout import GridLayout
from pathlib import Path

import globals as gb

class MobileTab(GridLayout, MDTabsBase):
    '''Class implementing content for the areas / lines tab.'''
    message_dialog = None
    exit_dialog = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # get instance of application object
        app = MDApp.get_running_app()

        # init themes
        self.theme_cls = app.theme_cls

    # ---------------------------------------------------------------------------------
    # is called by the parent container whenever the video frame has been clicked
    def on_image_clicked(self, area, x, y):   
        #print(area)               
        if area == 'vehicle_tracking' and gb.vehicleArea.size < 14:
            gb.vehicleArea = np.append(gb.vehicleArea, np.array([[x, y]]), axis=0)
        elif area == 'detect' and gb.detectionLine.size < 4:
            gb.detectionLine = np.append(gb.detectionLine, np.array([[x, y]]), axis=0)
        elif area == 'tint' and gb.tintDetectZone.size < 14:
            gb.tintDetectZone = np.append(gb.tintDetectZone, np.array([[x, y]]), axis=0)
        elif area == 'lprpoly' and gb.lprpoly.size < 14:
            gb.lprpoly = np.append(gb.lprpoly, np.array([[x, y]]), axis=0)

    # ---------------------------------------------------------------------------------
    # Draw user selection on current frame for vehicle tracking zone, detection line
    def draw_areas(self, frame):

        for col in ['vehicle', 'detect','tint','lprpoly']:
            if col == 'vehicle':
                area = gb.vehicleArea
                color = (0, 255, 0)
            elif col == 'detect':
                area = gb.detectionLine
                color = (255, 165, 0)
            elif col == 'tint':
                area = gb.tintDetectZone
                color = (0, 255, 255)
            elif col == 'lprpoly':
                area = gb.lprpoly
                color = (0, 0, 255)
            
            if area.size == 2:
                cv2.circle(frame, (area[0, 0], area[0, 1]), 2, color, 2)
            else:
                if area.size >= 8:                                        
                    area = area[0:area.size, 0:2]					
                    isClosed = True
                else:
                    isClosed = False

                vertices = area.reshape(-1,1,2)
                frame = cv2.polylines(frame, [vertices], isClosed, color, 2)                
        # cv2.imshow("as",frame)
        return frame #cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # ---------------------------------------------------------------------------------
    # clear the selection made on the specified area
    def clear_area(self, col):               
        if col == 'vehicle_tracking':            
            gb.vehicleArea = np.empty(shape=(0,2), dtype= np.int16)            
        elif col == 'detect':
            gb.detectionLine = np.empty(shape=(0,2), dtype= np.int16)
        elif col == 'tint':
            gb.tintDetectZone = np.empty(shape=(0,2), dtype= np.int16)
        elif col == 'lprpoly':
            gb.lprpoly = np.empty(shape=(0,2), dtype= np.int16)

    # ---------------------------------------------------------------------------------
    # returns the name currently selected area (in the radioboxes)
    def selected_area(self):
        if self.ids.chk_vehicle_tracking.active:
            return 'vehicle_tracking'
        elif self.ids.chk_detect.active:
            return 'detect'        
        elif self.ids.chk_tint.active:
            return 'tint'
        elif self.ids.chk_lprpoly.active:
            return 'lprpoly'
        else:
            return None


