#!/usr/bin/env python

# Haversine formula example in Python
# Author: Wayne Dyck

import math

def get_distance(origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371 # km

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d

def gridCoordinatesToMap(point, grid):
    x1,y1 = point
    width, height = grid
    return (x1 - width//2, y1 - height//2)

def getPointFromDistance(point1, point2, origin, grid):
    x1, y1 = point1
    x1_lat, y1_lat = origin
    x2, y2 = gridCoordinatesToMap(point2,grid)
    

    R = 6378.1 #Radius of the Earth
    brng = math.atan2(y2 - y1, x2 - x1) #Bearing is 90 degrees converted to radians.
    d = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    #lat2  52.20444 - the lat result I'm hoping for
    #lon2  0.36056 - the long result I'm hoping for.

    lat1 = math.radians(x1_lat) #Current lat point converted to radians
    lon1 = math.radians(y1_lat) #Current long point converted to radians

    lat2 = math.asin( math.sin(lat1)*math.cos(d/R) +
        math.cos(lat1)*math.sin(d/R)*math.cos(brng))

    lon2 = lon1 + math.atan2(math.sin(brng)*math.sin(d/R)*math.cos(lat1),
                math.cos(d/R)-math.sin(lat1)*math.sin(lat2))

    lat2 = math.degrees(lat2)
    lon2 = math.degrees(lon2)

    print(lat2, lon2)
    return lat2, lon2

def getLabels(node_names,sizes,capacities):
    labels = []
    texts = zip(node_names,sizes,capacities)
    for line in texts:
        text = ""
        for i in range(len(line)):
            if i == 0:
                text += line[i]
            if i == 1:
                text += f"<br>Size: {str(line[i])}"
            if i == 2:
                text += f"<br>Capacity: {str(line[i])}"
        labels.append(text)
    return labels