from math import sqrt

from dotenv import load_dotenv
import googlemaps
from time import time
import os

load_dotenv()

origin_point = os.getenv("ZERO_LOCATION")
origin_point = origin_point.split(",")
origin_point = [float(origin_point[0]), float(origin_point[1])]
gmaps = googlemaps.Client(key=os.getenv("MAPS_API"))


def get_distance(location_name):
    geocode = gmaps.geocode(location_name)
    try:
        crow_flies = sqrt((geocode[0]["geometry"]["location"]["lat"] - origin_point[0]) ** 2 + (
                    geocode[0]["geometry"]["location"]["lng"] - origin_point[1]) ** 2)
    except:
        return -1
    return crow_flies
