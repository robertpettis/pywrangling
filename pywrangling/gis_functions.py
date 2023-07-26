# -*- coding: utf-8 -*-
"""
These functions will provide GIS support.
"""

import pandas as pd
from geopy.geocoders import Nominatim
import googlemaps
import math
from tqdm import tqdm

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
        try:
            batch_coordinates = [geocode_func(address) for address in batch_addresses]
            coordinates += batch_coordinates
        except Exception as e:
            print(f"Error: {e}")
            # Try the other geocoding function if we get a 502 error and try_nominatim_first is true
            if "502" in str(e) and try_nominatim_first:
                if geocode_func == geocode:
                    geocode_func = googlecode
                else:
                    geocode_func = geocode
                # try the other geocode function for this iteration
                try:
                    batch_coordinates = [geocode_func(address) for address in batch_addresses]
                    coordinates += batch_coordinates
                except Exception as e:
                    print(f"Error: {e}")
                    # Switch back to original geocode function
                    if geocode_func == geocode:
                        geocode_func = googlecode
                    else:
                        geocode_func = geocode
                    continue
    return coordinates
