import geopandas as gpd  # For performing spatial operations
import pandas as pd
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import googlemaps
import math
from tqdm import tqdm
from geopy.geocoders import Nominatim
import cartopy.io.img_tiles as cimgt
import cartopy.feature as cfeature
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from typing import Tuple, List

from shapely.ops import cascaded_union



# %% GEOCODING ################################################################
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










""" The below section will be to help us make some attractive static maps. """


class CustomTiles(cimgt.GoogleWTS):
    """
    A custom tile class to fetch map tiles from a specified URL.
    
    Extends the GoogleWTS class from cartopy.io.img_tiles.
    
    Attributes:
    -----------
    url : str
        The URL template to fetch the tiles. It should have placeholders for `x`, `y`, `z`, and `s`.
        
    subdomains : str, optional
        Subdomains to be used in the URL. The default is 'abc'.
    
    Methods:
    --------
    _image_url(tile) -> str
        Returns the URL for a specific tile based on its x, y, z coordinates.
    """

    def __init__(self, url, subdomains='abc'):
        """
        Initializes the CustomTiles class.
        
        Parameters:
        -----------
        url : str
            The URL template to fetch the tiles.
            
        subdomains : str, optional
            Subdomains to be used in the URL. The default is 'abc'.
        """
        # Store the URL and subdomains provided by the user
        self.url = url
        self.subdomains = subdomains
        
        # Call the constructor of the parent class (GoogleWTS)
        super().__init__()

    def _image_url(self, tile):
        """
        Returns the URL for a specific tile.
        
        Parameters:
        -----------
        tile : tuple
            A tuple containing the x, y, z coordinates of the tile.
            
        Returns:
        --------
        str
            The URL to fetch the image for the specified tile.
        """
        # Extract x, y, z coordinates from the tile tuple
        x, y, z = tile
        
        # Select a subdomain based on the tile coordinates.
        # This helps in distributing requests across different subdomains.
        s = self.subdomains[(x + y) % len(self.subdomains)]
        
        # Format the URL with the tile coordinates and subdomain
        url = self.url.format(x=x, y=y, z=z, s=s)
        
        return url






def concave_hull(gdf):
    """
    Computes the concave hull for the given GeoDataFrame.
    
    Parameters:
    -----------
    gdf : geopandas.GeoDataFrame
        Input GeoDataFrame containing geometry data.
        
    Returns:
    --------
    geopandas.GeoDataFrame
        A new GeoDataFrame with the concave hull of the input.
    """
    
    # Calculate the union of all geometries in the GeoDataFrame
    merged_geometry = cascaded_union(gdf.geometry)
    
    # Create and return a new GeoDataFrame
    return gpd.GeoDataFrame([{'geometry': merged_geometry}], geometry='geometry')





































# %%% A function to create the map


# def prepare_data(points: gpd.GeoDataFrame, polygons: gpd.GeoDataFrame, extent: Tuple[float, float, float, float], quantiles: List[float]) -> gpd.GeoDataFrame:
#     """
#     Prepare the data by performing a spatial join, counting points in polygons, filtering polygons within an extent, and calculating percentiles.

#     Parameters:
#     points (gpd.GeoDataFrame): GeoDataFrame containing points and additional information.
#     polygons (gpd.GeoDataFrame): GeoDataFrame containing polygons.
#     extent (tuple): The extent of the map in the form of (xmin, ymin, xmax, ymax).
#     quantiles (list): The quantiles to calculate.

#     Returns:
#     gpd.GeoDataFrame: The prepared data.
#     """

#     # Assign an id to each polygon
#     polygons['id'] = polygons.index

#     # Perform spatial join
#     spatial_join = gpd.sjoin(polygons, points, op='contains')

#     # Count points in each polygon
#     polygons_with_counts = spatial_join.groupby("id").size().reset_index(name='count')
#     polygons = polygons.merge(polygons_with_counts, on='id')

#     # Filter polygons within the map extent
#     polygons_within_extent = polygons.cx[extent[0]:extent[2], extent[1]:extent[3]]

#     # Calculate percentiles for the counts within the map extent
#     percentiles = [polygons_within_extent['count'].quantile(q) for q in quantiles]

#     # Add percentiles to the data
#     polygons_within_extent['percentile'] = pd.cut(polygons_within_extent['count'], bins=[0] + percentiles, labels=False, include_lowest=True)

#     # Reproject polygons to equal area projection
#     polygons_equal_area = polygons_within_extent.to_crs("EPSG:3310")

#     # Calculate the area of each polygon in square meters
#     polygons_equal_area["area_sqm"] = polygons_equal_area["geometry"].area

#     # Convert the area from square meters to square miles
#     polygons_equal_area["area_sqmi"] = polygons_equal_area["area_sqm"] / 2589988.47

#     # Merge the area column back to the original polygons_within_extent GeoDataFrame
#     polygons_within_extent["area_sqmi"] = polygons_equal_area["area_sqmi"]

#     # Print the average area in square miles
#     avg_area_sqmi = polygons_within_extent["area_sqmi"].mean()
#     print(f"Average area of each polygon is {avg_area_sqmi:.2f} square miles.")

#     return polygons_within_extent



# def create_map(basemap: cimgt.GoogleWTS, polygons: gpd.GeoDataFrame, shapefiles: List[gpd.GeoDataFrame], aspect_ratio: float = ((1 + math.sqrt(5)) / 2), width: float = 10):
#     """
#     Create a map with the specified base map, polygons, and other shapefiles.

#     Parameters:
#     basemap (cimgt.GoogleWTS): The base map to use.
#     polygons (gpd.GeoDataFrame): GeoDataFrame containing polygons to be plotted.
#     shapefiles (list): List of GeoDataFrames of other shapefiles to be plotted.
#     aspect_ratio (float, optional): The desired aspect ratio. Default is the golden ratio.
#     width (float, optional): The width of the figure. Default is 10.

#     Returns:
#     tuple: A tuple containing the figure and axes.
#     """

#     # Set the height based on the width and aspect ratio
#     height = width / aspect_ratio

#     # Create a figure and axes with the desired aspect ratio
#     fig = plt.figure(figsize=(width, height), dpi=300)
#     ax = fig.add_subplot(1, 1, 1, projection=basemap.crs)

#     # Add the base map
#     ax.add_image(basemap, 10)

#     # Add features
#     ax.add_feature(cfeature.COASTLINE)
#     ax.add_feature(cfeature.BORDERS, linestyle=':')
#     ax.add_feature(cfeature.STATES, linestyle=':')

#     # Plot the polygons
#     polygons.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=2.5, zorder=4)

#     # Plot the other shapefiles
#     for shapefile in shapefiles:
#         shapefile.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=2.5, zorder=4)

#     # Return the figure and axes
#     return fig, ax



























