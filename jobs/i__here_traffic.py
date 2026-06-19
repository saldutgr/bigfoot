import geopandas as gpd
import pandas as pd
import os
import json
from pandas import Timestamp
from dotenv import load_dotenv
import sqlalchemy

from utils.database_utils import postgres_engine
from utils.here_utils import *

load_dotenv()

def load_to_db(df, table, schema, dtype=None):
    con = postgres_engine()
    df.to_sql(table, con, schema=schema, if_exists='append', index=False, dtype=dtype)
    con.close()

def get_here_data():
    bbox = "-83.806746,42.224879,-83.670074,42.327828"
    api_key = os.getenv('HERE_API')

    data = get_traffic_data(bbox, api_key)

    data  = pd.json_normalize(data['results'])

    data['geometry'] = data.apply(lambda x: explode_street_links(x), axis=1)

    data = pd.concat([data, 
           pd.json_normalize(data.explode('currentFlow.subSegments')['currentFlow.subSegments'])],
           axis=1)


    data.loc[:, 'data_queried_at'] = Timestamp('now')

    return data

if __name__ == "__main__":
    df = get_here_data()
    
    load_to_db(df, 'here__traffic_flows', 'raw', dtype={'location.shape.links': sqlalchemy.types.JSON,
                                                        'currentFlow.subSegments': sqlalchemy.types.JSON,
                                                        'geometry': sqlalchemy.types.VARCHAR})



