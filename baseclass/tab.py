from kivy.properties import StringProperty

from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout

class Tab(MDFloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''
    #content_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)