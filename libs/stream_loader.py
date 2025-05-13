import cv2
import numpy as np
import logging

import time
from threading import Thread

class StreamLoader:  
    """Load streaming videos from ped / mobile cameras"""

    def __init__(self, cfg, video_width):
        
        self.sources = self.get_sources(cfg)
        n = len(self.sources)        
        self.imgs, self.fps, self.frames, self.threads = [None] * n, [0] * n, [0] * n, [None] * n
        
        self.video_width, self.video_height = [0] * n, [0] * n # this is the size of the video after resizing to fit the app window

        for i, s in enumerate(self.sources):  # index, source

            # Start thread to read frames from video stream
            cap = cv2.VideoCapture(s)
            assert cap.isOpened(), f'Failed to open {s}'

            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            self.video_width[i] = video_width
            self.video_height[i] = int((video_width / w) * h)

            self.fps[i] = max(cap.get(cv2.CAP_PROP_FPS) % 100, 0) or 30.0  # 30 FPS fallback
            self.frames[i] = max(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), 0) or float('inf')  # infinite stream fallback

            _, self.imgs[i] = cap.read()  # guarantee first frame

            # invoke threads for reading videos streams
            self.threads[i] = Thread(target=self.update, args=([i, cap]), daemon=True)
            print(f" success ({self.frames[i]} frames {w}x{h} at {self.fps[i]:.2f} FPS)")
            self.threads[i].start()                   


    # look into config file and calculate source path for both ped and mobile apps
    def get_sources(self, cfg):
    
        sources = []

        # calc ped video source 
        if cfg.VIDEO_SOURCE.PED.TYPE == 'ipcam':
            ip = cfg.VIDEO_SOURCE.PED.IPCAM.IP
            user = cfg.VIDEO_SOURCE.PED.IPCAM.USERNAME
            pwd = cfg.VIDEO_SOURCE.PED.IPCAM.PASSWORD
        
            sources.append(f"rtsp://{user}:{pwd}@{ip}/Streaming/channels/1/") 
        else:
            sources.append(cfg.VIDEO_SOURCE.PED.FILE)

        # calc mobile video source 
        if cfg.VIDEO_SOURCE.MOBI.TYPE == 'ipcam':
            ip = cfg.VIDEO_SOURCE.MOBI.IPCAM.IP
            user = cfg.VIDEO_SOURCE.MOBI.IPCAM.USERNAME
            pwd = cfg.VIDEO_SOURCE.MOBI.IPCAM.PASSWORD
        
            sources.append(f"rtsp://{user}:{pwd}@{ip}/Streaming/channels/1/") 
        else:
            sources.append(cfg.VIDEO_SOURCE.MOBI.FILE)

        if cfg.VIDEO_SOURCE.NOENTRY.TYPE == 'ipcam':
            ip = cfg.VIDEO_SOURCE.NOENTRY.IPCAM.IP
            user = cfg.VIDEO_SOURCE.NOENTRY.IPCAM.USERNAME
            pwd = cfg.VIDEO_SOURCE.NOENTRY.IPCAM.PASSWORD
        
            sources.append(f"rtsp://{user}:{pwd}@{ip}/Streaming/channels/1/") 
        else:
            sources.append(cfg.VIDEO_SOURCE.NOENTRY.FILE)

        if cfg.VIDEO_SOURCE.LDMS.TYPE == 'ipcam':
            ip = cfg.VIDEO_SOURCE.LDMS.IPCAM.IP
            user = cfg.VIDEO_SOURCE.LDMS.IPCAM.USERNAME
            pwd = cfg.VIDEO_SOURCE.LDMS.IPCAM.PASSWORD
        
            sources.append(f"rtsp://{user}:{pwd}@{ip}/Streaming/channels/1/") 
        else:
            sources.append(cfg.VIDEO_SOURCE.LDMS.FILE)

        return sources

    def update(self, i, cap):
        # Read stream `i` frames in daemon thread
        n, f, read = 0, self.frames[i], 1  # frame number, frame array, inference every 'read' frame
        while cap.isOpened() and n < f:
            try:
                n += 1
                # _, self.imgs[index] = cap.read()
                cap.grab()
                if n % read == 0:
                    success, im = cap.retrieve()
                    self.imgs[i] = im if success else self.imgs[i] * 0
                time.sleep(1 / self.fps[i])  # wait time
            except Exception:
                logging.exception("[StreamLoader:update] Error while reading next frame from video stream") 

    def __iter__(self):
        self.count = -1
        return self

    def __next__(self):        
        self.count += 1
        if not all(x.is_alive() for x in self.threads) or cv2.waitKey(1) == ord('q'):  # q to quit
            cv2.destroyAllWindows()
            raise StopIteration
        
        img0 = self.imgs.copy()       
        return img0

    def __len__(self):
        return len(self.sources)  # 1E12 frames = 32 streams at 30 FPS for 30 years

