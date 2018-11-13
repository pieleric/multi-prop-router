import mapbox
from mapbox import Directions
import json
import requests
import time
import calendar
import logging


# Note: we express all coordinates in longitude (float), latitude (float), as in GeoJSON

class RouteSummary():
    def __init__(self, profile, distance, duration, price=None):
        # TODO: distance is not important?
        self.profile = profile # "car", "bike", "foot" "taxi", "public-transport"...
        self.distance = distance # m
        self.duration = duration # s
        self.price = price # €
        #TODO define more properties to the route summary: "leisure"/agreability, "co2"....
        # => just automatically computed from the 3 inputs?
        # TODO: add some "legs" information to be able to display some kind of basic info about the trip?


# TODO: support extra modes:
# "taxi" -> Uber
# "plane+taxi" ??
# "plane+pulic" ??

# TODO: add support for the time of departue/arrival?

# Mapbox:
def mapbox_route(origin, destination, profile):
    """
    origin (float, float): coordinates longitude, latitude, eg: (-122.7282, 45.5801)
    destination (float, float): coordinates
    profile (str): "car", "bike", or "foot"
    return RouteSummary
    """
    mbprofile = {"car": "mapbox/driving-traffic", "bike": "mapbox/cycling", "foot": "mapbox/walking"}[profile]

    service = Directions()
    # Note: the start/end points can also be encoded in GeoJSON, but that doesn't seem necessary:
#    o = {'type': 'Feature',
#         'properties': {'name': 'Boooo'},
#         'geometry': {
#             'type': 'Point',
#             'coordinates': origin}}

    response = service.directions([origin, destination], mbprofile)
    # TODO: check it went fine

    r = response.json()
    logging.debug(response.json())
    # TODO: r = response.json()
    # Get the most recommended route
    route = r["routes"][0]
    # To get the whole geometry:
    # driving_routes = response.geojson()

    return RouteSummary(profile, route["distance"], route["duration"])

# cf https://github.com/aitorvs/9292-api-spec/blob/master/docs/resources/journeys.md
NL_9292_URI_BASE = "http://api.9292.nl/0.1/"
def nl9292_route(origin, destination):
    """
    origin (float, float): coordinates longitude, latitude, eg: (-122.7282, 45.5801)
    destination (float, float): coordinates
    return RouteSummary
    """
    #curl -v "http://api.9292.nl/0.1/journeys?before=1&sequence=1&byFerry=true&bySubway=true&byBus=true&byTram=true&byTrain=true&lang=nl-NL&from=station-amsterdam-centraal&dateTime=2018-11-21T1754&searchType=departure&interchangeTime=standard&after=5&to=station-eindhoven"

    # need to convert a longitue/lattitude to a "location id"
    origin_id = nl9292_get_location_id(origin)
    destination_id = nl9292_get_location_id(destination)

    uri = (NL_9292_URI_BASE + "/journeys?before=1&sequence=1&byFerry=true&bySubway=true&byBus=true&byTram=true&byTrain=true&lang=nl-NL" +
           "&from=" + origin_id +
           "&dateTime=" + time.strftime("%Y-%m-%dT%H%M", time.gmtime(time.time())) + # now in yyyy-MM-ddTHHmm
           "&searchType=departure&interchangeTime=standard&after=5" +
           "&to=" + destination_id
           )
    response = requests.get(uri)
    r = response.json()
    logging.debug("Got response %s", r)
    # We pick the first journey we find
    j = r["journeys"][0]

    departure = nl9292_time_to_epoch(j["departure"])
    arrival = nl9292_time_to_epoch(j["arrival"])
    duration = arrival - departure
    price = j["fareInfo"]["fullPriceCents"] * 0.01 # €
    return RouteSummary("public-transport", None, duration, price)

def nl9292_time_to_epoch(t):
    """
    t (str): time in the format yyyy-MM-ddTHH:mm
    returns (float): seconds since epoch
    """
    return calendar.timegm(time.strptime(t, "%Y-%m-%dT%H:%M"))

def nl9292_get_location_id(coordinates):
    """
    origin (float, float): coordinates longitude, latitude
    returns the closest location id for the given coordinates
    """
    # cf https://github.com/aitorvs/9292-api-spec/blob/master/docs/resources/locations.md
    # ex: "http://api.9292.nl/0.1/locations?lang=nl-NL&latlong=52.352812,4.948491"
    uri = (NL_9292_URI_BASE + "locations?lang=nl-NL&latlong=%f,%f" % (coordinates[1], coordinates[0]))
    response = requests.get(uri)
    r = response.json()
    logging.debug("Got response %s", r)
    return r["locations"][0]["id"]

