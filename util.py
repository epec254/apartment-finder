import settings
import math
from google_maps import *

def coord_distance(lat1, lon1, lat2, lon2):
    """
    Finds the distance between two pairs of latitude and longitude.
    :param lat1: Point 1 latitude.
    :param lon1: Point 1 longitude.
    :param lat2: Point two latitude.
    :param lon2: Point two longitude.
    :return: Kilometer distance.
    """
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    km = 6367 * c
    return km

def in_box(coords, box):
    """
    Find if a coordinate tuple is inside a bounding box.
    :param coords: Tuple containing latitude and longitude.
    :param box: Two tuples, where first is the bottom left, and the second is the top right of the box.
    :return: Boolean indicating if the coordinates are in the box.
    """
    if box[0][0] < coords[0] < box[1][0] and box[1][1] < coords[1] < box[0][1]:
        return True
    return False

def post_listing_to_slack(sc, listing):
    """
    Posts the listing to slack.
    :param sc: A slack client.
    :param listing: A record of the listing.
    """
    desc = "{0} | {1} | {2} | {3} | <{4}>".format(listing["area"], listing["price"], listing["bart_dist"], listing["name"], listing["url"])
    sc.api_call(
        "chat.postMessage", channel=settings.SLACK_CHANNEL, text=desc,
        username='pybot', icon_emoji=':robot_face:'
    )

def find_points_of_interest(geotag, location):
    """
    Find points of interest, like transit, near a result.
    :param geotag: The geotag field of a Craigslist result.
    :param location: The where field of a Craigslist result.  Is a string containing a description of where
    the listing was posted.
    :return: A dictionary containing annotations.
    """
    area_found = False
    area = ""
    min_dist = None
    near_bart = False
    fb_stop = None
    google_stop = None
    google_dist = None
    fb_dist = None
    bart_dist = "N/A"
    bart = ""
    # Look to see if the listing is in any of the neighborhood boxes we defined.
    for a, coords in settings.BOXES.items():
        if in_box(geotag, coords):
            area = a
            area_found = True

    # Check which google shuttle stop is closest
    google_shortest_distance = 99999999
    for station, coords in settings.GOOGLE_STOPS.items():
        dist = coord_distance(coords[0], coords[1], geotag[0], geotag[1])
        if (dist < google_shortest_distance):
            google_stop = station
            google_dist = dist
            google_shortest_distance = dist

    #get walking time to the shuttle using google maps api
    try:
        google_walktime = walkingTimeFromTo(geotag[0], geotag[1], settings.GOOGLE_STOPS[google_stop][0], settings.GOOGLE_STOPS[google_stop][1])
    except:
        google_walktime = 'Unknown'

    # Check which google shuttle stop is closest
    fb_shortest_distance = 99999999
    for station, coords in settings.FB_STOPS.items():
        dist = coord_distance(coords[0], coords[1], geotag[0], geotag[1])
        if (dist < fb_shortest_distance):
            fb_stop = station
            fb_dist = dist
            fb_shortest_distance = dist

    #get walking time to the shuttle using google maps api
    try:
        fb_walktime = walkingTimeFromTo(geotag[0], geotag[1], settings.FB_STOPS[fb_stop][0], settings.GOOGLE_STOPS[google_stop][1])
    except:
        fb_walktime = 'Unknown'

    #get distance to adi office
    try:
        adi_drivetime = drivingTimeToOffice(geotag[0], geotag[1], settings.OFFICE_ADDRESS)
    except:
        adi_drivetime = "Unknown"

    #get the real address
    try:
        address = geoCodeAddress(geotag[0], geotag[1])
    except:
        address = "%f,%f"%(geotag[0], geotag[1])


    # If the listing isn't in any of the boxes we defined, check to see if the string description of the neighborhood
    # matches anything in our list of neighborhoods.
    if len(area) == 0 and location is not None:
        for hood in settings.NEIGHBORHOODS:
            if hood in location.lower():
                area = hood

    return {
        "area_found": area_found,
        "area": area,
        # "near_bart": near_bart,
        "google_stop": google_stop,
        "google_dist": google_dist,
        "google_walktime": google_walktime,
        "fb_stop": fb_stop,
        "fb_dist": fb_dist,
        "fb_walktime": fb_walktime,
        "adi_drivetime": adi_drivetime,
        "address": address
    }
