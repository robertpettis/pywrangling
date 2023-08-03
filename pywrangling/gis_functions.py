import geopandas as gpd  # For performing spatial operations
import pandas as pd
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import googlemaps
import math
from tqdm import tqdm
from geopy.geocoders import Nominatim
import cartopy.io.img_tiles as cimgt
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import cartopy.crs as ccrs


# GEOCODING ###################################################################
# Initialize Nominatim geolocator
geolocator = Nominatim(user_agent='my_custom_user_agent')


def geocode_with_progress(addresses, api_key, try_nominatim_first=True, batch_size=100):
    # initialize Google Maps client
    gmaps = googlemaps.Client(key=api_key)

    # define geocoding functions
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

    # select initial geocoding function
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





# %% BLACK AND WHITE STATIC MAPS #################################################


# %%% Helper Functions 

def format_description(text):
    if not isinstance(text, str):
        return text

    formatted_text = ""
    capitalize_next = True
    for char in text:
        if capitalize_next:
            char = char.upper()
            capitalize_next = False
        else:
            char = char.lower()
        formatted_text += char
        if char == ';':
            capitalize_next = True
    return formatted_text


#This one uses a log scale and is better if there are big differences in scale
def count_to_color(count, max_count, scale_factor=0.5):
    max_log = math.log(max_count + 1)
    log_count = math.log(count + 1)
    intensity = log_count / max_log
    gray_value = 255 - int(scale_factor * intensity * 255)
    return f'#{gray_value:02x}{gray_value:02x}{gray_value:02x}'

# Define the percentile-based color function
def count_to_color_percentile(count, percentiles):
    for i, p in enumerate(percentiles):
        if count <= p:
            gray_value = 255 - 25 * i
            return f'#{gray_value:02x}{gray_value:02x}{gray_value:02x}'
    return '#000000'


class CustomTiles(cimgt.GoogleWTS):
    def __init__(self, url, subdomains='abc'):
        self.url = url
        self.subdomains = subdomains
        super().__init__()

    def _image_url(self, tile):
        x, y, z = tile
        s = self.subdomains[(x + y) % len(self.subdomains)]
        url = self.url.format(x=x, y=y, z=z, s=s)
        return url


def create_colormap(percentiles):
    n = len(percentiles) + 1
    colors = [count_to_color_percentile(p, percentiles) for p in percentiles] + ['#000000']
    return mcolors.ListedColormap(colors)



# %%% A function to create the map

def create_map(data: gpd.GeoDataFrame, colormap: mcolors.Colormap, extent: Tuple[float, float, float, float]):
    """
    Create a map based on the provided GeoDataFrame and plot the data.

    Parameters:
    data (gpd.GeoDataFrame): The GeoDataFrame containing the data.
    colormap (mcolors.Colormap): The colormap to use for the map.
    extent (tuple): The extent of the map in the form of (xmin, ymin, xmax, ymax).

    Returns:
    Matplotlib figure and axes.
    """

    # Create the map figure
    fig = plt.figure(figsize=(8, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    
    # Define the basemap
    basemap = CustomTiles('https://stamen-tiles-{s}.a.ssl.fastly.net/toner-background/{z}/{x}/{y}.png', subdomains='abcd')
    ax.add_image(basemap, 14, interpolation='spline36', zorder=0)
    
    # Plot the data
    data.plot(column='count', cmap=colormap, linewidth=0.8, ax=ax, edgecolor='0.8')

    return fig, ax































