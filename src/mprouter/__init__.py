import mapbox
from mapbox import Directions
import json
import requests
import time
import calendar
import logging
import os
from geopy import Point
from geopy.distance import distance as geodistance

MONOTCH_KEY = open("monotch.key").readline().strip()
os.environ["MAPBOX_ACCESS_TOKEN"] = open("mapbox.key").readline().strip()

MAX_PARKING_DISTANCE = 10000
PARKING_TO_PT_TIME = 3 * 60 # s

# Note: we express all coordinates in longitude (float), latitude (float), as in GeoJSON

class RouteSummary():
    def __init__(self, profile, distance, duration, price=0, legs=None, depart_time=None, nbChanges=0, origin_id=None, destination_id=None):
        # TODO: distance is not important?
        self.profile = profile # "car", "bike", "foot" "taxi", "public-transport"...
        self.distance = distance # m
        self.depart_time = depart_time
        self.duration = duration # s
        self.price = price # €
        #TODO define more properties to the route summary: "leisure"/agreability, "co2"....
        # => just automatically computed from the 3 inputs?
        # TODO: add some "legs" information to be able to display some kind of basic info about the trip?
        self.legs = legs
        self.nbChanges = nbChanges
        self.origin_id = origin_id
        self.destination_id = destination_id

class PRRouteSummary():
    def __init__(self, duration, price, distance_car, parking, pt_journey, depart_time=None, duration_car=None, duration_pt=None, price_pt=None, url_car=None, url_pt=None):
        self.depart_time = depart_time
        self.duration = duration # s
        self.duration_car = duration_car # s
        self.duration_pt = duration_pt
        self.price = price # €
        # TODO price of the car by converting km -> gas -> €?
        self.price_pt = price_pt
        self.distance_car = distance_car
        self.parking = parking # a Parking
        self.pt_journey = pt_journey # bus line, bus stop start, bus stop end, time, => 9292 legs
        self.url_car = url_car
        self.url_pt = url_pt
    
    def __str__(self):
        return "PR Journey of %d m @ %f €, parking at %s, then doing: %s" % (self.duration / 60, self.price, self.parking.name, self.pt_journey)

# TODO: for now, we assume the price is fixed (because we can always get some arrangment with every parking company ;-) )
# ideally, it could also be per hour
class Parking():
    def __init__(self, coordinates, name, pid, price, address):
        self.coordinates = coordinates
        self.name = name
        self.id = pid
        self.price = price # €
        self.address = address

    def __str__(self):
        return "Parking %s (%s) at %s, price = %f €" % (self.name, self.id, self.coordinates, self.price) 


# TODO: also take the end time? At least to check that the parking is opened when coming back,
# that there is still public transport, and to compute the price
def pr_route(origin, destination, depart_time):
    """
    origin (float, float): coordinates longitude, latitude, eg: (-122.7282, 45.5801)
    destination (float, float): coordinates
    depart_time (float): s from epoch
    return (list of PRRouteSummary): the cheapest/quickest
    """

    # Find all the parking "near" the destinations (aka around the city)
    try:
        pks_dest = monotch_list_parkings(destination, MAX_PARKING_DISTANCE)
    except Exception:
        logging.exception("Failed to get parkings for location %s", destination)
        raise

    # Compute for each parking the route
    full_journeys = []
    for p in pks_dest:
        try:
            a_to_p = mapbox_route(origin, p.coordinates, "car") # TODO: pass the depart_time?
        except Exception:
            logging.exception("Failed to get routing for A %s to %s", origin, p)
            continue
            
        depart_time_p = depart_time + a_to_p.duration + PARKING_TO_PT_TIME
        p_to_b = nl9292_route(p.coordinates, destination, depart_time_p)
        
        total_dur = a_to_p.duration + PARKING_TO_PT_TIME + p_to_b.duration
        total_price = a_to_p.price + p.price + p_to_b.price
        # When to leave at the latest (computed backwards based on the public transport)
        depart_time = p_to_b.depart_time - PARKING_TO_PT_TIME - a_to_p.duration
        gmap_url_a_p = create_gmap_url(origin, p.coordinates, "car")
        logging.debug("Car journey: %s", gmap_url_a_p)
        nl9292_url_p_b = create_nl9292_url(p_to_b.origin_id, p_to_b.destination_id)
        logging.debug("Public transport journey: %s", nl9292_url_p_b)
        j = PRRouteSummary(total_dur, total_price, a_to_p.distance, p, p_to_b.legs, depart_time, url_car=gmap_url_a_p, url_pt=nl9292_url_p_b,
                           duration_car=a_to_p.duration, duration_pt=p_to_b.duration, price_pt=p_to_b.price)
        full_journeys.append(j)

    logging.debug("Got %d journeys", len(full_journeys))
 
    # Pick the 2 cheapest journeys
    cheapest_journeys = sorted(full_journeys, key=lambda j: j.price)
    best_journeys = set(cheapest_journeys[:2])
  
    # Pick the 2 quickest journeys
    quickest_journeys = sorted(full_journeys, key=lambda j: j.duration)
    best_journeys |= set(quickest_journeys[:2])

    logging.debug("Selected %d journeys", len(best_journeys))

    return best_journeys


def create_gmap_url(origin, destination, profile="car"):
    """
    origin (float, float): coordinates longitude, latitude, eg: (-122.7282, 45.5801)
    destination (float, float): coordinates
    return (str): the url to open the routing in google map
    """
    # cf https://developers.google.com/maps/documentation/urls/ios-urlscheme
    gmprofile = {"car": "driving", "pt": "transit", "bike": "bicycling", "foot": "walking"}[profile]
    return ("https://www.google.com/maps/?" + 
            "saddr=@%f,%f" % (origin[1], origin[0]) +
            "&daddr=@%f,%f" % (destination[1], destination[0]) +
            "&directionsmode=%s" % gmprofile)

def create_nl9292_url(origin_id, destination_id):
    """
    origin_id (str): nl9292 POI ID
    destination_id (str): nl9292 POI ID
    return (str): the url to open the routing in 9292
    """
    # cf https://9292.nl/zakelijk/reisadvies-via-je-eigen-website
    return ("https://9292.nl/?" + 
            "van=%s" % origin_id +
            "&naar=%s" % destination_id)


MONOTCH_URI_BASE = "https://api.monotch.com/PrettigParkeren/v6/"
MONOTCH_USABLE_PARKINGS = "parking_unknown;parking_garage;parking_area;parking_pr;parking_valet;parking_book"
def monotch_list_parkings(position, radius):
    """
    origin (float, float): coordinates longitude, latitude, eg: (-122.7282, 45.5801)
    radius (float): max distance from the position
    return (list of Parkings)
    """
    # It doesn't take a "radius", but a bounding box
    bbox = get_bbox(position, radius)
    uri = (MONOTCH_URI_BASE + "list?" + "w=%f&n=%f&e=%f&s=%f" % bbox +
           "&types=" + MONOTCH_USABLE_PARKINGS +
           "&api_key=" + MONOTCH_KEY
          )
    logging.debug("Contacting uri: %s", uri)
    response = requests.get(uri)
    while response.status_code == 403:
        time.sleep(1)
        logging.debug("retrying a bit later")
        response = requests.get(uri)
    logging.debug("Got response: %s", response.content)
    r = response.json()

    pks = []
    for pj in r:
        loc = float(pj["location"]["lng"]), float(pj["location"]["lat"])
        p_details = monotch_get_parking_details(pj["id"])
        if "rate_day" in pj:
            price = (int(pj["rate_day"]) / 100) 
            price /= 2 # asssume we can get discount for 12h
        # TODO: for a specific time slot? cf p_details["rates"]
        
        else:
            price = 0
        
        # Note: the address is not always present. Ideally, we'd just fill-up by reverse geocoding.
        full_address = p_details.get("address", "") + " " + p_details["overview_city"]
        p = Parking(loc, p_details["name"], pj["id"], price, full_address)
        pks.append(p)

    return pks



def monotch_get_parking_details(parking_id):
    """
    return (str): structure json-like from the monotoch API
    """
    # https://api.monotch.com/PrettigParkeren/v6/detail?id=parking_1557&includeRates=1&api_key=hp8cq2h6sy2me5hn4nekgnme
    # https://api.monotch.com/PrettigParkeren/v6/rates?eid=parking_1731&api_key=hp8cq2h6sy2me5hn4nekgnme
    uri = (MONOTCH_URI_BASE + "detail?" + "id=%s" % parking_id +
           "&includeRates=1" + 
           "&api_key=" + MONOTCH_KEY
          )
    logging.debug("Contacting uri: %s", uri)
    response = requests.get(uri)
    while response.status_code == 403:
        time.sleep(1)
        logging.debug("retrying a bit later")
        response = requests.get(uri)
    r = response.json()
    return r
    

def get_bbox(position, radius):
    """
    return (4 float): long west, lat north, long east, lat south
    """
    nw = geodistance(meters=radius/2).destination(Point(position[1], position[0]), 225)
    se = geodistance(meters=radius/2).destination(Point(position[1], position[0]), 45)
    return nw[1], nw[0], se[1], se[0]


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
def nl9292_route(origin, destination, depart_time):
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
           "&dateTime=" + time.strftime("%Y-%m-%dT%H%M", time.gmtime(depart_time)) + # now in yyyy-MM-ddTHHmm
           "&searchType=departure&interchangeTime=standard&after=5" +
           "&to=" + destination_id
           )
    response = requests.get(uri)
    r = response.json()
    logging.debug("Got response %s", r)
    # We pick the first journey we find
    # TODO: be more picky: less changes + earliest one after the departure time
    j = r["journeys"][0]

    departure = nl9292_time_to_epoch(j["departure"])
    arrival = nl9292_time_to_epoch(j["arrival"])
    duration = arrival - departure
    price = j["fareInfo"]["fullPriceCents"] * 0.01 # €
    legs = j["legs"]
    nbChanges = j["numberOfChanges"]
    logging.debug("Found pt journey starting at %f, lasting %d m", departure, duration / 60)
    return RouteSummary("public-transport", None, duration, price, legs, departure, nbChanges, origin_id, destination_id)

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

