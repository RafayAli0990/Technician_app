from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.boxlayout import BoxLayout
from kivymd.uix.gridlayout import GridLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.label import MDLabel

from libs.yaml_parser import YamlParser
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.lang import Builder
from kivy.metrics import dp

from functools import partial


# from kivy.uix.dropdown import DropDown
# from kivy.uix.button import Button
KV = '''
Screen
    MDTextField:
        id: field
        pos_hint: {'center_x': .5, 'center_y': .5}
        size_hint_x: None
        width: "200dp"
        hint_text: "Material"
        on_focus: if self.focus: app.menu.open()
    '''
class SettingsTab(GridLayout, MDTabsBase):
    '''Class implementing content for the areas / lines tab.'''
    message_dialog = None
    exit_dialog = None
    # dropdown=DropDown()
    def __init__(self, settings_file_path= None, settings_format_file_path=None, **kwargs):
        super().__init__(**kwargs)

        # get instance of application object
        app = MDApp.get_running_app()
        self.theme_cls = app.theme_cls
        self.cfg = app.cfg
        
        self.settings_file_path = settings_file_path
        self.settings_format_file_path = settings_format_file_path

        self.settings_cfg = YamlParser(config_file=self.settings_file_path)
        self.cfg_format = YamlParser(config_file=self.settings_format_file_path)

        # # the ids are not yet populated, so we need to do the following
        # # see https://stackoverflow.com/questions/26916262/why-cant-i-access-the-screen-ids
        Clock.schedule_once(self._finish_init)

    def _finish_init(self, dt):
        self.ids.dynamic_ui_update.update_gui(self.cfg_format, self.settings_cfg) 
        
class Dynamic_UI_update(BoxLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.text_fields = {}
        self.dropdown = {}
        self.now_focused_textfield = None

    def add_all_child(self, subcfgformat_dict, subcfg, subcfg_prefix:str):
        #print(subcfg_prefix)
        #for k, v in subcfg.items():
        for k, v in subcfgformat_dict.items():
            if k == "merge_from_file":
                return
            label_txt = str(k)
            if len(subcfg_prefix) > 1:
                label_txt = subcfg_prefix+"-"+str(k)
            if isinstance(v, dict):
                if k in subcfg.keys():
                    self.add_all_child(subcfgformat_dict[k], subcfg[k], label_txt) # recursion
            else:
                label = MDLabel(text=label_txt, adaptive_height=True)
                if k in subcfg.keys():
                    show_text = subcfg[k]
                    # without this snippet, its difficult to post handle while saving this entry as yaml
                    # ['"a"', '"b"', '"c"'..] - cumbersome to handle back it to a proper list
                    if isinstance(subcfg[k], list):
                        show_text = ",".join(subcfg[k])
                else:
                    show_text = subcfgformat_dict[k][-1] # default text from pre-defined format - as we dont have an entry for this in remote config

                # print(k, subcfgformat_dict[k])
                if subcfgformat_dict[k][1] == 'technician':
                    
                    if len(v) > 3:  # Ensure there are enough elements to extract options
                            options = v[3:-1]
                    else:
                        options = []

                    if options: 
                        textfield = MDTextField(text=str(show_text), 
                                                hint_text=str(v[2]), 
                                                required=True, 
                                                helper_text=f"OPTIONS: {v[3:-1]}, DEFAULT: {v[-1]}", 
                                                helper_text_mode= "on_focus") # persistent or on_focus
                        
                        menu_items = [
                            {
                                "viewclass": "OneLineListItem",
                                "text": str(option),
                                "on_release": partial(self.set_dropdown_value, option),
                            }
                            for option in options
                        ]

                        # Create dropdown menu
                        dropdown = MDDropdownMenu(
                            items=menu_items,
                            width_mult=4,
                            caller = textfield
                        )              

                        # Open dropdown when the text field is clicked or gains focus
                        #textfield.bind(focus=lambda instance, focus: dropdown.open() if focus else None)
                        textfield.bind(focus=self.textfieldclicked)
                        
                        # Bind dropdown selection to update the main button text
                        # dropdown.bind(on_select=lambda instance, x: setattr(instance, 'text', x))
                        # dropdown.bind(on_select=print)

                        # Add the dropdown-triggering button to the layout
                        self.add_widget(label)
                        self.add_widget(textfield)
                        self.dropdown[hex(id(textfield))] = dropdown
                        
                    else:

                        textfield = MDTextField(
                            text=str(show_text),
                            hint_text="Enter value",
                            helper_text=f"DEFAULT: {show_text}",
                            helper_text_mode="persistent",  # Valid helper_text_mode
                            required=True
                            # disabled= True
                        )
                        self.add_widget(label)
                        self.add_widget(textfield)
 
                else:  # For technician fields with no options, use a writable text field
                    # textfield = MDTextField(
                    #     text=str(show_text),
                    #     hint_text="Enter value",
                    #     helper_text=f"DEFAULT: {show_text}",
                    #     helper_text_mode="persistent",  # Valid helper_text_mode
                    #     required=True
                    #     # disabled= True
                    # )
                    textfield = MDTextField(text=str(show_text), mode="fill", disabled= True ) # TODO: remove this line, not used
                    # self.add_widget(label)
                    # self.add_widget(textfield)
                    # Store the text field reference
                self.text_fields[label_txt] = textfield
    
    def textfieldclicked(self, l_textfield, l_bool):
        # print("focus called", l_bool)
        if l_bool:
            self.now_focused_textfield = l_textfield
            self.dropdown[hex(id(l_textfield))].open()

    def set_dropdown_value(self, value):
        # print("menu clicked", value)
        if self.now_focused_textfield is not None:
            self.now_focused_textfield.text = str(value)
            self.dropdown[hex(id(self.now_focused_textfield))].dismiss()

    '''
    # self-recursive function
    def add_all_child_old(self, subcfgformat_dict, subcfg, subcfg_prefix:str):
        for k, v in subcfgformat_dict.items():
            if k == "merge_from_file":
                return
            label_txt = str(k)
            if len(subcfg_prefix) > 1:
                label_txt = subcfg_prefix+"-"+str(k)
            if isinstance(v, dict):
                if k in subcfg.keys():
                    self.add_all_child(v, subcfg[k], label_txt) # recursion
            else:
                label = MDLabel(text=label_txt, adaptive_height=True)
                if k in subcfg.keys():
                    show_text = subcfg[k]
                    # without this snippet, its difficult to post handle while saving this entry as yaml
                    # ['"a"', '"b"', '"c"'..] - cumbersome to handle back it to a proper list
                    if isinstance(subcfg[k], list):
                        show_text = ",".join(subcfg[k])
                else:
                    show_text = v[-1] # default text from pre-defined format - as we dont have an entry for this in remote config

                if v[1] == 'technician':
                    textfield = MDTextField(text=str(show_text), hint_text=str(v[2]), required=True, helper_text=f"OPTIONS: {v[3:-1]}, DEFAULT: {v[-1]}", helper_text_mode= "on_focus") # persistent or on_focus
                    # print("V--->>>>", v)
                    self.add_widget(label)
                    self.add_widget(textfield)
                else: # greyed out
                    textfield = MDTextField(text=str(show_text), mode="fill", disabled= True ) # TODO: remove this line, not used

                self.text_fields[label_txt] = textfield
        '''
    def update_gui(self, cfg_format, cfg):
        try:
            #print(cfg.DETECTIONS.MOBI.keys())
            del cfg_format["merge_from_file"]
            del cfg_format["merge_from_dict"]
            del cfg["merge_from_file"]
            del cfg["merge_from_dict"]
        except:
            pass
        self.add_all_child(cfg_format, cfg, "")
    
