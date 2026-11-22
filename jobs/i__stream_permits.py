import argparse
from config import stream_dicts
import os
from dotenv import load_dotenv # type: ignore
import re

from utils.stream_utils import scrape_stream_permits, normalize_stream_permits
from utils.database_utils import add_postgres_arguments, postgres_engine

load_dotenv()

def load_to_db(df, table, schema, port=None, database=None):
    engine, con = postgres_engine(port=port, database=database)
    df.to_sql(table, con, schema=schema, if_exists='replace', index=False)
    con.close()

def run_sfh_bldg_pipeline(port=None, database=None):
    raw_data = scrape_stream_permits('bldgPermits')

    df = normalize_stream_permits(raw_data, stream_dicts.streamFields)
    df['is_main'] = df['is_main'].astype(str)
    
    #df = get_stream_latlong(df, 'address_line1', 'address_line2')

    load_to_db(
        df,
        'stream__building_permits_sfh',
        'raw',
        port=port,
        database=database,
    )

def run_sfh_demo_pipeline(port=None, database=None):
    print('demo')
    raw_data = scrape_stream_permits('demoPermits')

    df = normalize_stream_permits(raw_data, stream_dicts.streamFields)
    df['is_main'] = df['is_main'].astype(str)
    
    #df = get_stream_latlong(df, 'address_line1', 'address_line2')

    load_to_db(
        df,
        'stream__demo_permits_sfh',
        'raw',
        port=port,
        database=database,
    )

if __name__ == '__main__':
    parser = add_postgres_arguments(argparse.ArgumentParser())
    args = parser.parse_args()
    run_sfh_bldg_pipeline(port=args.port, database=args.database)
    run_sfh_demo_pipeline(port=args.port, database=args.database)
