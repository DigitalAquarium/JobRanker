from math import sqrt

from dotenv import load_dotenv
import googlemaps
from JobRanker.settings import SECRETS

load_dotenv()

origin_point = SECRETS["zero_location"]
origin_point = origin_point.split("|")
origin_point = [float(origin_point[0]), float(origin_point[1])]
gmaps = googlemaps.Client(SECRETS["maps"])


def get_latlng(location_name):
    geocode = gmaps.geocode(location_name)
    try:
        lat = geocode[0]["geometry"]["location"]["lat"]
        lng = geocode[0]["geometry"]["location"]["lng"]
    except:
        print("failed to get latlng for location",location_name)
        lat = lng = 0
    return lat, lng



def get_distance_km(lat,lng):
    lat_km_ratio = 111
    lng_km_ratio = 69 # at lat ~50
    return sqrt(((origin_point[0] - lat) * lat_km_ratio) ** 2 + ((origin_point[1] - lng) * lng_km_ratio) ** 2)
