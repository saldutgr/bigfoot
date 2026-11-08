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

 # Establish connection
def connect_to_dropbox():
    
    import dropbox
    #Token Generated from dropbox
    load_dotenv()

    try:
        dbx = dropbox.Dropbox(
            app_key=os.environ["DROPBOX_KEY"],
            app_secret=os.environ["DROPBOX_SECRET"],
            oauth2_refresh_token=os.environ["DROPBOX_REFRESH"],
        )
        print('Connected to Dropbox successfully')
            
    except Exception as e:
        print(str(e))
            
    return dbx

def backup_table(table_name, 
                 schema_name,
                 dropbox_file,
                 dropbox_folder,
                 where=None):
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
    
    engine, con = postgres_engine()

    if where is None:
        QUERY = f"SELECT * FROM {schema_name}.{table_name}"
    else:
        QUERY = f"""
        select * FROM {schema_name}.{table_name}
        where {where}
        """

    df = pd.read_sql(QUERY, con)
    df = df.astype(str)
    today = date.today().strftime("%Y%m%d")
    df_par = df.to_parquet()

    
    dbx = connect_to_dropbox()

    dbx.files_upload(df_par, 
                     f"/{dropbox_folder}/{today}_{dropbox_file}.parquet", 
                     mode=dropbox.files.WriteMode.overwrite)


def batch_backup(
    table_name, 
    schema_name,
    dropbox_file,
    dropbox_folder,
    where=None,
    zip="False"):
    """
    Queries table from postgres and writes to parquet format local.
    Returned object can be used as input for dropbox upload
    """
    from sqlalchemy import create_engine, text
    import pyarrow as pa
    import pyarrow.parquet as pq
    import dropbox
    from dropbox.files import UploadSessionCursor, CommitInfo, WriteMode

    from utils.database_utils import postgres_engine, connect_to_dropbox

    #setvars
    today = date.today().strftime("%Y%m%d")
    dropbox_path = f"/{dropbox_folder}/{today}_{dropbox_file}.parquet"
    tmp_file = f"tmp/{today}_{dropbox_file}.parquet"

    engine, con = postgres_engine()

    if where is None:
        query = text(f"SELECT * FROM {schema_name}.{table_name}")
    else:
        query = text(f"SELECT * FROM {schema_name}.{table_name} WHERE {where}")

    batch_size = 10_000

    with engine.connect().execution_options(
        stream_results=True,
        yield_per=batch_size,
    ) as conn:
        result = conn.execute(query).mappings()

        sample = [dict(row) for row in result.fetchmany(5000)]
        if sample is None:
            raise ValueError("Query returned no rows; provide a schema for an empty result.")

        inferred_schema = pa.Table.from_pylist(sample).schema
        print(inferred_schema)
        schema = pa.schema([
            pa.field(field.name, field.type, nullable=True)
            for field in inferred_schema
        ])

        with pq.ParquetWriter(tmp_file, schema) as writer:
            writer.write_table(pa.Table.from_pylist(sample, schema=schema))

            while rows := result.fetchmany(batch_size):
                records = [dict(row) for row in rows]
                writer.write_table(pa.Table.from_pylist(records, schema=schema))

    dbx = connect_to_dropbox()

    if zip == "False":
        file_size = os.path.getsize(tmp_file)
        chunk_size = 8 * 1024 * 1024

        with open(tmp_file, "rb") as f:
            first_chunk = f.read(chunk_size)

            if file_size <= chunk_size:
                metadata = dbx.files_upload(
                    first_chunk,
                    dropbox_path,
                    mode=WriteMode.overwrite,
                )
            else:
                session = dbx.files_upload_session_start(first_chunk)
                cursor = UploadSessionCursor(session.session_id, len(first_chunk))
                commit = CommitInfo(dropbox_path, mode=WriteMode.overwrite)

                while file_size - f.tell() > chunk_size:
                    chunk = f.read(chunk_size)
                    dbx.files_upload_session_append_v2(chunk, cursor)
                    cursor.offset = f.tell()

                metadata = dbx.files_upload_session_finish(
                    f.read(),
                    cursor,
                    commit,
                )
    else:
        import zipfile

        zip_file = f"tmp/{today}_{dropbox_file}.zip"
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(tmp_file, arcname=f"{today}_{dropbox_file}.parquet")

        with open(zip_file, "rb") as f:
            dbx.files_upload(f.read(), f"/{dropbox_folder}/{today}_{dropbox_file}.zip", mode=WriteMode.overwrite)