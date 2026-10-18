from dotenv import load_dotenv
import os
import sqlalchemy
import pandas as pd
import sshtunnel
import paramiko
load_dotenv()

def postgres_engine():
    engine = sqlalchemy.create_engine(f"postgresql://{os.getenv('USER')}:{os.getenv('PASS')}@{os.getenv('HOST')}:{os.getenv('port')}/{os.getenv('database')}")
    con = engine.connect()
    return con

def mysql_engine(schema):
    
    sshtunnel.SSH_TIMEOUT = 90
    sshtunnel.TUNNEL_TIMEOUT = 90

    from sshtunnel import SSHTunnelForwarder
    import pandas

    # SSH configuration
    server = SSHTunnelForwarder(
        ('ssh.pythonanywhere.com'),
        ssh_username=os.getenv('pyMysql_USER'),
        ssh_password=os.getenv('pymysql_PASS'),
        remote_bind_address=(f'{os.getenv("pyMysql_USER")}.mysql.pythonanywhere-services.com', 3306)
    )
    server.start()
    engine = sqlalchemy.create_engine(f"mysql+pymysql://{os.getenv('pyMysql_USER')}:{os.getenv('pyMysql_DBPASS')}@127.0.0.1:{server.local_bind_port}/saldutgr${schema}")
    con = engine.connect()
 
    return con

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

 # Establish connection
def connect_to_dropbox():
    
    import dropbox
    #Token Generated from dropbox
    load_dotenv()
    TOKEN = os.getenv('DROPBOX_TOKEN')
    try:
        dbx = dropbox.Dropbox(TOKEN)
        print('Connected to Dropbox successfully')
            
    except Exception as e:
        print(str(e))
            
    return dbx

def backup_table(table_name, 
                 schema_name,
                 dropbox_file,
                 dropbox_folder):
    """
    Queries table from postgres and writes to parquet format local.
    Returned object can be used as input for dropbox upload
    """
    import os
    from dotenv import load_dotenv
    from datetime import date
    import pandas as pd
    
    import dropbox

    from utils.database_utils import postgres_engine, connect_to_dropbox
    
    con = postgres_engine()
    query = f"SELECT * FROM {schema_name}.{table_name}"

    df = pd.read_sql(query, con)
    df = df.astype(str)
    today = date.today().strftime("%Y%m%d")
    df_par = df.to_parquet()

    
    dbx = connect_to_dropbox()

    dbx.files_upload(df_par, 
                     f"/{dropbox_folder}/{today}_{dropbox_file}.parquet", 
                     mode=dropbox.files.WriteMode.overwrite)
