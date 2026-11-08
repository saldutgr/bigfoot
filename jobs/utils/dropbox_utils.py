from dotenv import load_dotenv
import os
load_dotenv()

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
    This is used for smaller tables that can be loaded into memory. For larger tables, use batch_backup.
    """
    import os
    from dotenv import load_dotenv
    from datetime import date
    import pandas as pd
    
    import dropbox

    from utils.database_utils import postgres_engine
    
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
    import os
    from dropbox.files import UploadSessionCursor, CommitInfo, WriteMode

    from utils.database_utils import postgres_engine

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

def clear_dropbox_folder(dropbox_folder):
    """
    Clears all files in the specified Dropbox folder.
    """
    import dropbox
    import os
    from dotenv import load_dotenv

    dbx = connect_to_dropbox()
    
    try:
        result = dbx.files_list_folder(f"/{dropbox_folder}")
        for entry in result.entries:
            dbx.files_delete_v2(entry.path_lower)
        print(f"Cleared all files in Dropbox folder: {dropbox_folder}")
    except Exception as e:
        print(f"Error clearing Dropbox folder: {e}")