import argparse
import geopandas as gpd
import pandas as pd
import os
import json
from pandas import Timestamp
from dotenv import load_dotenv
import sqlalchemy

from utils.database_utils import add_postgres_arguments, postgres_engine

load_dotenv()

def load_to_db(df, table, schema, dtype=None, port=None, database=None):
    engine, con = postgres_engine(port=port, database=database)
    try:
        df.to_sql(
            table,
            con,
            schema=schema,
            if_exists='append',
            index=False,
            dtype=dtype,
        )
    finally:
        con.close()
        engine.dispose()


if __name__ == "__main__":
    parser = add_postgres_arguments(argparse.ArgumentParser())
    args = parser.parse_args()

    parcels = gpd.read_file('2026-03-25 A2 Tax Parcels.gpkg')
    df = parcels.drop('geometry', axis=1)
    load_to_db(
        df,
        'parcel_attributes_2025',
        'raw',
        port=args.port,
        database=args.database,
    )
