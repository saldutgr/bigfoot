import argparse

from homeharvest import scrape_property
from pandas import Timestamp
from utils.database_utils import (
    add_postgres_arguments,
    postgres_engine,
    query_last_updated,
)


def scrape_sold(port=None, database=None):

    engine, con = postgres_engine(port=port, database=database)

    df = scrape_property(
        location="Ann Arbor, MI",
        listing_type="for_sale",  # for_sale, for_rent, pending
        past_days=500)

    drop_cols = ['office_phones', 'agent_phones', 'primary_photo', 'alt_photos', 'text']
    df = df.drop(drop_cols, axis =1 )

    df.loc[:, 'data_loaded_at'] = Timestamp('now')

    #query updated for filter
    query_time = query_last_updated(
        'raw.realtor__sold', 
        'last_update_date',
        con = con)

    df = df[df.last_update_date.dt.date > query_time]
    df['new_construction'] =  df['new_construction'].astype(int)
    con.close()
    return df


def load_to_db(df, table, schema, port=None, database=None):
    engine, con = postgres_engine(port=port, database=database)
    df.to_sql(table, con, schema=schema, if_exists='append', index=False)
    con.close()

if __name__ == "__main__":
    parser = add_postgres_arguments(argparse.ArgumentParser())
    args = parser.parse_args()

    df = scrape_sold(port=args.port, database=args.database)
    load_to_db(
        df,
        'realtor__sold',
        'raw',
        port=args.port,
        database=args.database,
    )