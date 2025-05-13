import cv2
import numpy as np

from kivymd.app import MDApp
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.gridlayout import GridLayout
from pathlib import Path

import globals as gb

class NoentryTab(GridLayout, MDTabsBase):
    '''Class implementing content for the areas / lines tab.'''
    message_dialog = None
    exit_dialog = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Get instance of application object
        app = MDApp.get_running_app()

        # Init themes
        self.theme_cls = app.theme_cls

    # ---------------------------------------------------------------------------------
    # Is called by the parent container whenever the video frame has been clicked
    def on_image_clicked(self, area, x, y):   
        #print(area)  
        if area == 'vehicle_tracking' and gb.vehicleArea_noentry.size < 14:
            gb.vehicleArea_noentry = np.append(gb.vehicleArea_noentry, np.array([[x, y]]), axis=0)
        elif area == 'lpr' and gb.lprLine_noentry.size < 4:
            gb.lprLine_noentry = np.append(gb.lprLine_noentry, np.array([[x, y]]), axis=0)
        elif area == 'No_entry_zone' and gb.noentry_zone_noentry.size < 14:
            gb.noentry_zone_noentry = np.append(gb.noentry_zone_noentry, np.array([[x, y]]), axis=0)
        elif area == 'entry_line' and gb.entryLine_noentry.size < 4:
            gb.entryLine_noentry = np.append(gb.entryLine_noentry, np.array([[x, y]]), axis=0)
        elif area == 'exit_line' and gb.exitLine_noentry.size < 4:
            gb.exitLine_noentry = np.append(gb.exitLine_noentry, np.array([[x, y]]), axis=0)

    # ---------------------------------------------------------------------------------
    # Draw user selection on current frame for vehicle tracking zone, detection line
    def draw_areas(self, frame):
        for col in ['vehicle', 'No_entry_zone', 'lpr', 'entry_line', 'exit_line']:
            if col == 'vehicle':
                area = gb.vehicleArea_noentry
                color = (0, 255, 0)
            elif col == 'lpr':
                area = gb.lprLine_noentry
                color = (0, 255, 255)
            elif col == 'No_entry_zone':
                area = gb.noentry_zone_noentry
                color = (255, 0, 45)
            elif col == 'entry_line':
                area = gb.entryLine_noentry
                color = (40, 40, 240)
            elif col == 'exit_line':
                area = gb.exitLine_noentry
                color = (240, 40, 40)

            if area.size == 2:
                cv2.circle(frame, (area[0, 0], area[0, 1]), 2, color, 2)
            else:
                if area.size >= 8:                                        
                    area = area[0:area.size, 0:2]                    
                    isClosed = True
                else:
                    isClosed = False

                vertices = area.reshape(-1, 1, 2)
                frame = cv2.polylines(frame, [vertices], isClosed, color, 2)                
        
        return frame  # cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # ---------------------------------------------------------------------------------
    # Clear the selection made on the specified area
    def clear_area(self, col):               
        if col == 'vehicle_tracking':            
            gb.vehicleArea_noentry = np.empty(shape=(0, 2), dtype=np.int16)            
        elif col == 'lpr':
            gb.lprLine_noentry = np.empty(shape=(0, 2), dtype=np.int16)
        elif col == 'No_entry_zone':
            gb.noentry_zone_noentry = np.empty(shape=(0, 2), dtype=np.int16)
        elif col == 'entry_line':
            gb.entryLine_noentry = np.empty(shape=(0, 2), dtype=np.int16)
        elif col == 'exit_line':
            gb.exitLine_noentry = np.empty(shape=(0, 2), dtype=np.int16)

    # ---------------------------------------------------------------------------------
    # Returns the name of the currently selected area (in the radio boxes)
    def selected_area(self):
        if self.ids.chk_vehicle_tracking.active:
            return 'vehicle_tracking'
        elif self.ids.chk_lpr_noentry.active:
            return 'lpr'       
        elif self.ids.chk_No_entry_zone.active:
            return 'No_entry_zone'
        elif self.ids.chk_entry_line.active:
            return 'entry_line'
        elif self.ids.chk_exit_line.active:
            return 'exit_line'
        else:
            return None
