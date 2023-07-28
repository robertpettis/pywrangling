
import pandas as pd
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import googlemaps
import math
from tqdm import tqdm
from geopy.geocoders import Nominatim

#Initialize Nominatim geolocator
geolocator = Nominatim(user_agent='my_custom_user_agent')

def geocode_with_progress(addresses, api_key, try_nominatim_first=True, batch_size=100):
    #initialize Google Maps client
    gmaps = googlemaps.Client(key=api_key)

    #define geocoding functions
    def geocode(address):
        location = geolocator.geocode(address, timeout=10)
        if location is None:
            return None
        else:
            return (location.latitude, location.longitude)

    def googlecode(address):
        geocode_result = gmaps.geocode(address)
        if geocode_result and len(geocode_result) > 0:
            location = geocode_result[0]["geometry"]["location"]
            return (location["lat"], location["lng"])
        else:
            return None

    #select initial geocoding function
    if try_nominatim_first:
        geocode_func = geocode
    else:
        geocode_func = googlecode

    coordinates = []
    num_batches = math.ceil(len(addresses) / batch_size)
    for i in tqdm(range(num_batches)):
        batch_start = i * batch_size
        batch_end = (i + 1) * batch_size
        batch_addresses = addresses[batch_start:batch_end]
        batch_coordinates = []
        for address in batch_addresses:
            try:
                coord = geocode_func(address)
                if coord is None:
                    # Switch geocoding function and try again
                    if geocode_func == geocode:
                        geocode_func = googlecode
                    else:
                        geocode_func = geocode
                    coord = geocode_func(address)
                batch_coordinates.append(coord)
                # Reset to original geocoding function for next address
                if geocode_func == geocode:
                    geocode_func = googlecode
                else:
                    geocode_func = geocode
            except GeocoderServiceError:
                print("GeocoderServiceError occurred, switching geocoding service")
                if geocode_func == geocode:
                    geocode_func = googlecode
                else:
                    geocode_func = geocode
                try:
                    coord = geocode_func(address)
                    batch_coordinates.append(coord)
                except GeocoderServiceError as e:
                    print("Geocoding failed for address: " + address)
                    print(str(e))
                    continue
        coordinates += batch_coordinates

    return coordinates