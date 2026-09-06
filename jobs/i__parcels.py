import geopandas as gpd
import pandas as pd
import os
import json
from pandas import Timestamp
from dotenv import load_dotenv
import sqlalchemy

from utils.database_utils import postgres_engine

load_dotenv()

def load_to_db(df, table, schema, dtype=None):
    con = postgres_engine()
    df.to_sql(table, con, schema=schema, if_exists='append', index=False, dtype=dtype)
    con.close()

p = gpd.read_file('2026-03-25 A2 Tax Parcels.gpkg')
df = p.drop('geometry', axis=1)

if __name__ == "__main__":
    load_to_db(df, 'parcel_attributes_2025', 'raw')
