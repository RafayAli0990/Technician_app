import sys
import cv2
import numpy as np

from kivymd.app import MDApp
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.gridlayout import GridLayout
from pathlib import Path

import globals as gb

class PedTab(GridLayout, MDTabsBase):
    '''Class implementing content for the areas / lines tab.'''
    message_dialog = None
    exit_dialog = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # get instance of application object
        app = MDApp.get_running_app()
        self.theme_cls = app.theme_cls
    
    # ---------------------------------------------------------------------------------
    # is called by the parent container whenever the video frame has been clicked
    def on_image_clicked(self, area, x, y):        
        if area == 'green' and gb.greenArea.size < 8:
            gb.greenArea = np.append(gb.greenArea, np.array([[x, y]]), axis=0)
        elif area == 'violet' and gb.violetArea.size < 8:
            gb.violetArea = np.append(gb.violetArea, np.array([[x, y]]), axis=0)
        elif area == 'red' and gb.redLine.size < 4:
            gb.redLine = np.append(gb.redLine, np.array([[x, y]]), axis=0)
        elif area == 'lpr' and gb.lprLine.size < 4:
            gb.lprLine = np.append(gb.lprLine, np.array([[x, y]]), axis=0)
        elif area == 'middle' and gb.middleLine.size < 4:
            gb.middleLine = np.append(gb.middleLine, np.array([[x, y]]), axis=0)
        elif area == 'entry_line' and gb.entryLine.size < 4:
            gb.entryLine = np.append(gb.entryLine, np.array([[x, y]]), axis=0)
        elif area == 'exit_line' and gb.exitLine.size < 4:
            gb.exitLine = np.append(gb.exitLine, np.array([[x, y]]), axis=0)
        elif area == 'left_line' and gb.leftLine.size < 4:
            gb.leftLine = np.append(gb.leftLine, np.array([[x, y]]), axis=0)
        elif area == 'right_line' and gb.rightLine.size < 4:
            gb.rightLine = np.append(gb.rightLine, np.array([[x, y]]), axis=0)

    # ---------------------------------------------------------------------------------
    # returns the color code of the area currently selected in the checkboxes
    def selected_area(self):
        if self.ids.chk_green.active:
            return 'green'
        elif self.ids.chk_violet.active:
            return 'violet'
        elif self.ids.chk_red.active:
            return 'red'
        elif self.ids.chk_lpr.active:
            return 'lpr'
        elif self.ids.chk_middle.active:
            return 'middle'
        elif self.ids.chk_entry_line.active:
            return 'entry_line'
        elif self.ids.chk_exit_line.active:
            return 'exit_line'
        elif self.ids.chk_ped_left_line.active:
            return 'left_line'
        elif self.ids.chk_ped_right_line.active:
            return 'right_line'
        else:
            return None
    

    # ---------------------------------------------------------------------------------            
    # Draw user selection on current frame for green, red, violet
    def draw_areas(self, frame):
			
        for col in ['green', 'red', 'violet', 'lpr', 'middle', 'entry_line', 'exit_line', 'left_line', 'right_line']:
            if col == 'green':
                area = gb.greenArea
                color = (0, 255, 0)
            elif col == 'red':
                area = gb.redLine
                color = (255, 0, 0)
            elif col == 'violet':
                area = gb.violetArea
                color = (138, 43, 226)
            elif col == 'lpr':
                area = gb.lprLine
                color = (240, 240, 10)
            elif col == 'middle':
                area = gb.middleLine
                color = (240, 240, 10)
            elif col == 'entry_line':
                area = gb.entryLine
                color = (255, 165, 0)
            elif col == 'exit_line':
                area = gb.exitLine
                color = (255, 165, 0)
            elif col == 'left_line':
                area = gb.leftLine
                color = (255, 255, 0)
            elif col == 'right_line':
                area = gb.rightLine
                color = (255, 255, 0)

            if area.size == 2:
                cv2.circle(frame, (area[0, 0], area[0, 1]), 2, color, 2)
            else:
                if area.size >= 8:
                    # ignore points after the first 4
                    area = area[0:4, 0:2]					
                    isClosed = True
                else:
                    isClosed = False

                vertices = area.reshape(-1,1,2)
                frame = cv2.polylines(frame, [vertices], isClosed, color, 2)
            
        return frame #cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # ---------------------------------------------------------------------------------
    # clear the selection made on the specified area
    def clear_area(self, col):          
        
        if col == 'green':
            gb.greenArea = np.empty(shape=(0,2), dtype= np.int16)
        elif col == 'violet':
            gb.violetArea = np.empty(shape=(0,2), dtype= np.int16)
        elif col == 'red':
            gb.redLine = np.empty(shape=(0,2), dtype= np.int16)
        elif col == 'lpr':
            gb.lprLine = np.empty(shape=(0,2), dtype= np.int16)
        elif col == 'middle':
            gb.middleLine = np.empty(shape=(0,2), dtype= np.int16)
        elif col =='entry_line':
            gb.entryLine = np.empty(shape=(0,2), dtype= np.int16)
        elif col =='exit_line':
            gb.exitLine = np.empty(shape=(0,2), dtype= np.int16)
        elif col =='left_line':
            gb.leftLine = np.empty(shape=(0,2), dtype= np.int16)
        elif col =='right_line':
            gb.rightLine = np.empty(shape=(0,2), dtype= np.int16)
            
    # ---------------------------------------------------------------------------------
    def show_message_dialog(self, msg):        
        if not self.message_dialog:
            self.message_dialog = MDDialog(
                title="Error",
                text=msg,
                buttons=[
                    MDFlatButton(
                        # https://stackoverflow.com/questions/41817607/python-kivy-assertionerror-none-is-not-callable-error-on-function-call-by-b
                        text="OK", text_color=self.theme_cls.primary_color, on_release = lambda x: self.close_dialog('message')
                    ),
                ],
            )
        else:
            self.message_dialog.text = msg

        self.message_dialog.open()
    

   