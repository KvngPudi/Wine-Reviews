import requests
import googlemaps
from pprint import pprint


def get_coordinates(location_name):
    API_KEY = 'AIzaSyDf4CfiHbsySOfdwB0vS4j5bAar_GVm7g8'
    client = googlemaps.Client(API_KEY)

    geocode_result = client.geocode(location_name)

    if geocode_result and len(geocode_result) > 0:
        latitude = geocode_result[0]['geometry']['location']['lat']
        longitude = geocode_result[0]['geometry']['location']['lng']
        return latitude, longitude
    else:
        return None, None


