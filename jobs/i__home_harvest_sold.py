from homeharvest import scrape_property
from pandas import Timestamp
from utils.database_utils import query_last_updated, postgres_engine


def scrape_sold():

    con = postgres_engine()

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


def load_to_db(df, table, schema):
    con = postgres_engine()
    df.to_sql(table, con, schema=schema, if_exists='append', index=False)
    con.close()

if __name__ == "__main__":
    df = scrape_sold()
    load_to_db(df, 'realtor__sold', 'raw')