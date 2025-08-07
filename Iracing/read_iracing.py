import irsdk
ir = irsdk.IRSDK()
ir.startup()
while True:
    speed = ir['Speed']*3.6  # Convert m/s to km/h
    gear = ir['Gear']
    print("Speed:",speed,"km/h, Gear:", gear)