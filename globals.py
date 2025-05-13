import numpy as np

# --- ped tab
greenArea = np.empty(shape=(0, 2), dtype=np.int16)
violetArea = np.empty(shape=(0, 2), dtype=np.int16)
redLine = np.empty(shape=(0, 2), dtype=np.int16)
lprLine = np.empty(shape=(0,2), dtype= np.int16)
middleLine = np.empty(shape=(0, 2), dtype=np.int16)
entryLine = np.empty(shape=(0,2), dtype= np.int16)
exitLine = np.empty(shape=(0,2), dtype= np.int16)
leftLine = np.empty(shape=(0, 2), dtype=np.int16)
rightLine = np.empty(shape=(0, 2), dtype=np.int16)

# --- mobile/seatbelt tab
vehicleArea = np.empty(shape=(0,2), dtype= np.int16)
detectionLine = np.empty(shape=(0, 2), dtype=np.int16)
tintDetectZone = np.empty(shape=(0, 2), dtype=np.int16)
lprpoly = np.empty(shape=(0, 2), dtype=np.int16)

# --- noentry tab
vehicleArea_noentry = np.empty(shape=(0, 2), dtype=np.int16)  
lprLine_noentry = np.empty(shape=(0, 2), dtype=np.int16)  
entryLine_noentry = np.empty(shape=(0, 2), dtype=np.int16)
exitLine_noentry = np.empty(shape=(0, 2), dtype=np.int16)

# --- noentry dms05 tab
vehicleArea_noentry = np.empty(shape=(0, 2), dtype=np.int16)  
noentry_zone_noentry = np.empty(shape=(0, 2), dtype=np.int16)  
entryLine_noentry = np.empty(shape=(0, 2), dtype=np.int16)

# --- Lane Discipline tab 
vehicleArea_ldms = np.empty(shape=(0, 2), dtype=np.int16)
#rightArea_ldms = np.empty(shape=(0, 2), dtype=np.int16)
rightHArea_ldms = np.empty(shape=(0, 2), dtype=np.int16)  
rightLine_ldms = np.empty(shape=(0, 2), dtype=np.int16)  
leftLine_ldms = np.empty(shape=(0, 2), dtype=np.int16)  
lprLine_ldms = np.empty(shape=(0, 2), dtype=np.int16) 
middleLine_ldms = np.empty(shape=(0, 2), dtype=np.int16)
trajectoryLine_ldms = np.empty(shape=(0, 2), dtype=np.int16)
lprpoly_ldms = np.empty(shape=(0, 2), dtype=np.int16)

