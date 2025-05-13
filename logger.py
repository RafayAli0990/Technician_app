
class LoggerUtils():
    def __init__(self):
        if not hasattr(self, 'init'): # init will be called after __new__ singleton class
            self.init = True
            self.statusBar = None
            self.progressBar = None
            self.textBrowser = None

    def __new__(self, *args, **kwargs):
        if not hasattr(self, 'instance'):
            self.instance = super(LoggerUtils, self).__new__(self, *args, **kwargs)

        return self.instance

    def add_ui_elements_to_logger(self, statusBar, progressBar, textBrowser):
        self.statusBar = statusBar
        self.progressBar = progressBar
        self.textBrowser = textBrowser

    # TODO: Set max lines limit and rotate the logs
    # TODO: Also write logs to some file
    # log_level : DEBUG, WARN, INFO
    def log_message(self, log_level:str="INFO", message:str="", progress_bar_level:int=None):
        if self.statusBar is None and self.progressBar is None and self.textBrowser is None:
            print("[" + log_level + "] " + message + " | Progress: " + str(progress_bar_level) + "%") # plus do service file logging always
        else:
            # status bar update
            self.statusBar.showMessage(message)
            if progress_bar_level is not None:
                self.progressBar.setValue(progress_bar_level)
            
            # textBrowser update
            self.textBrowser.append("[" + log_level + "] " + message + " | Progress: " + str(progress_bar_level) + "%")
            