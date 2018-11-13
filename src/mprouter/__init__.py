import mapbox
from mapbox import Directions
import json

service = Directions()



# TODO: support extra modes:
# "taxi" -> Uber
# "public-transport" -> 9292
# "plane+taxi" ??
# "plane+pulic" ??

# TODO: mapping from transport mode -> function
#mapbox/driving-traffic
#mapbox/driving
#mapbox/walking
#mapbox/cycling

class RouteSummary():
    def __init__(self, profile, distance, duration):
        self.profile = profile
        self.distance = distance
        self.duration = duration
        #TODO define more properties to the route summary: "leisure", "co2"....
        # => just automatically computed from the 3 inputs?

# Mapbox:
def mapbox_route(origin, destination, profile):
    """
    origin (float, float): coordinates longitude, latitude}, eg: (-122.7282, 45.5801)
    destination (float, float): coordinates
    profile (str): "car", "bike", or "foot"
    return RouteSummary
    """
    # Note: the start/end points can also be encoded in GeoJSON, but that doesn't seem necessary:
#    o = {'type': 'Feature',
#         'properties': {'name': 'Boooo'},
#         'geometry': {
#             'type': 'Point',
#             'coordinates': origin}}

    response = service.directions([origin, destination], 'mapbox/driving')
    # TODO: check it went fine

    r = json.loads(response.content.decode("utf-8"))
    # Get the most recommended route
    route = r["routes"][0]
    # To get the whole geometry:
    # driving_routes = response.geojson()

    return RouteSummary(profile, route["distance"], route["duration"])


