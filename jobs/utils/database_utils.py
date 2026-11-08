from dotenv import load_dotenv
import os
import sqlalchemy
import pandas as pd
from datetime import date

load_dotenv()

def postgres_engine():

    engine = sqlalchemy.create_engine(f"postgresql+psycopg2://{os.getenv('USER')}:{os.getenv('PASS')}@{os.getenv('HOST')}:{os.getenv('port')}/{os.getenv('database')}")
    con = engine.connect()
    return engine, con

def query_last_updated(table_name, 
                       target_date_col,
                       con):

    query = f"SELECT {target_date_col} FROM {table_name} \
        where {target_date_col} is not null \
        order by {target_date_col} desc limit 1"
    result = pd.read_sql(query, con)
    last_updated = result.iloc[0,0]
    return last_updated

def sqlite_keep_alive():
    # pip install sqlitecloud
    import os
    import sqlitecloud
    from dotenv import load_dotenv
    load_dotenv()

    # Open the connection to SQLite Cloud
    conn = sqlitecloud.connect(f"{os.getenv('SQLITE_CLOUD_URI')}{os.getenv('SQLITE_CLOUD_KEY')}")
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    result = cursor.fetchone()
    conn.close()

    print(result)