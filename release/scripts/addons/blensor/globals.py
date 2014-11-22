sensor_size = 32 #millimeters. Blender internal

def getPixelPerMillimeter(width,height):
    long_edge = max(width,height)
    return long_edge/sensor_size


