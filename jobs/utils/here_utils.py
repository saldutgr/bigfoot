import requests as re
from shapely.geometry import Point, LineString
import pandas as pd
import geopandas as gpd

def get_traffic_data(bbox, api_key):
    """
    Fetch traffic data from the HERE API for a given bounding box.

    Parameters:
    bbox (str): Bounding box in the format "min_lon,min_lat,max_lon,max_lat".
    api_key (str): Your HERE API key.

    Returns:
    dict: JSON response from the API containing traffic data.
    """
    url = f"https://data.traffic.hereapi.com/v7/flow?locationReferencing=shape&in=bbox:{bbox}&apiKey={api_key}"
    response = re.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def explode_street_links(traffic_data):
    point_list = []
    for points in traffic_data['location.shape.links']:
        for p in points['points']:
            point = Point(p['lng'], p['lat'])
            point_list.append(point)
        

    geom = LineString(point_list).wkt
    
    return geom