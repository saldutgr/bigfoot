#! /home/trafficbot/Projects/bigfoot/bigfootpy/bin/python3
from config import stream_dicts
import os
from dotenv import load_dotenv # type: ignore
import re

from utils.stream_utils import scrape_stream_permits, normalize_stream_permits
from utils.database_utils import postgres_engine, mysql_engine

load_dotenv()

def load_to_db(df, table, schema):
    con = mysql_engine('raw')
    df.to_sql(table, con, schema=None, if_exists='replace', index=False)
    con.close()

def run_sfh_bldg_pipeline():
    raw_data = scrape_stream_permits('bldgPermits')

    df = normalize_stream_permits(raw_data, stream_dicts.streamFields)
    df['is_main'] = df['is_main'].astype(str)
    
    #df = get_stream_latlong(df, 'address_line1', 'address_line2')

    load_to_db(df, 'stream__building_permits_sfh', 'raw')

def run_sfh_demo_pipeline():
    print('demo')
    raw_data = scrape_stream_permits('demoPermits')

    df = normalize_stream_permits(raw_data, stream_dicts.streamFields)
    df['is_main'] = df['is_main'].astype(str)
    
    #df = get_stream_latlong(df, 'address_line1', 'address_line2')

    load_to_db(df, 'stream__demo_permits_sfh', 'raw')

if __name__ == '__main__':
    run_sfh_bldg_pipeline()
    run_sfh_demo_pipeline()
