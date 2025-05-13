import cv2
import logging

# ----------
class VideoCapture:
    # if full_scale is True then 
    # - width parameter is ignored 
    # - the video source open is original resolution
    def __init__(self, cfg, full_scale = True, ipcam = 'ped', width = None):

        # open video source
        if ipcam == 'ped':
            if cfg.VIDEO_SOURCE.PED.TYPE == 'ipcam':
                ip = cfg.VIDEO_SOURCE.PED.IPCAM.IP
                user = cfg.VIDEO_SOURCE.PED.IPCAM.USERNAME
                pwd = cfg.VIDEO_SOURCE.PED.IPCAM.PASSWORD

                # channel 1 is full scale 
                # channel 2 is downscaled
                video_source = f"rtsp://{user}:{pwd}@{ip}/Streaming/channels/1/" 
                self.vid = cv2.VideoCapture(video_source)
                assert self.vid.isOpened(), f'Failed to open {video_source}'
            else:
                video_source = cfg.VIDEO_SOURCE.PED.FILE    
                self.vid = cv2.VideoCapture(video_source)  
        # open video source for mobi app
        elif ipcam == 'mobile':
            if cfg.VIDEO_SOURCE.MOBI.TYPE == 'ipcam':
                ip = cfg.VIDEO_SOURCE.MOBI.IPCAM.IP
                user = cfg.VIDEO_SOURCE.MOBI.IPCAM.USERNAME
                pwd = cfg.VIDEO_SOURCE.MOBI.IPCAM.PASSWORD

                # channel 1 is full scale 
                # channel 2 is downscaled
                video_source = f"rtsp://{user}:{pwd}@{ip}/Streaming/channels/1/" 
                self.vid = cv2.VideoCapture(video_source)
                assert self.vid.isOpened(), f'Failed to open {video_source}'
            else:
                video_source = cfg.VIDEO_SOURCE.MOBI.FILE    
                self.vid = cv2.VideoCapture(video_source)

        elif ipcam == 'noentry':
            if cfg.VIDEO_SOURCE.NOENTRY.TYPE == 'ipcam':
                ip = cfg.VIDEO_SOURCE.NOENTRY.IPCAM.IP
                user = cfg.VIDEO_SOURCE.NOENTRY.IPCAM.USERNAME
                pwd = cfg.VIDEO_SOURCE.NOENTRY.IPCAM.PASSWORD

                # channel 1 is full scale 
                # channel 2 is downscaled
                video_source = f"rtsp://{user}:{pwd}@{ip}/Streaming/channels/1/" 
                self.vid = cv2.VideoCapture(video_source)
                assert self.vid.isOpened(), f'Failed to open {video_source}'
            else:
                video_source = cfg.VIDEO_SOURCE.NOENTRY.FILE    
                self.vid = cv2.VideoCapture(video_source)

        if ipcam == 'LDMS':
            if cfg.VIDEO_SOURCE.PED.TYPE == 'LDMS':
                ip = cfg.VIDEO_SOURCE.LDMS.IPCAM.IP
                user = cfg.VIDEO_SOURCE.LDMS.IPCAM.USERNAME
                pwd = cfg.VIDEO_SOURCE.LDMS.IPCAM.PASSWORD

                # channel 1 is full scale 
                # channel 2 is downscaled
                video_source = f"rtsp://{user}:{pwd}@{ip}/Streaming/channels/1/" 
                self.vid = cv2.VideoCapture(video_source)
                assert self.vid.isOpened(), f'Failed to open {video_source}'
            else:
                video_source = cfg.VIDEO_SOURCE.LDMS.FILE    
                self.vid = cv2.VideoCapture(video_source)

        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        self.fps = self.vid.get(cv2.CAP_PROP_FPS) % 100

        # Get original video source width and height
        w = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

        ## resize frame if it is too big
        if full_scale:
            self.width = int(w)
            self.height = int(h)
        else:
            self.width = width
            self.height = int((width / w) * h)

	# Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

	# Use the read method of the VideoCapture class to get a frame from the video source
    def get_frame(self):
        try:
            if self.vid.isOpened():
                ret, frame = self.vid.read()                            
                if ret:
                    frame = cv2.resize(frame, (int(self.width), int(self.height)))                
                    # Return a boolean success flag and the current frame converted to BGR
                    return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                else:
                    return (ret, None)
            else:
                return (False, None)
        except Exception:
            logging.exception("[VideoCapture] Error while getting next frame from video source") 
            return (False, None)