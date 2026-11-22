import argparse
from datetime import date
from pathlib import Path

import pandas as pd
from google.cloud import storage
from google.oauth2 import service_account

from utils.database_utils import add_postgres_arguments, postgres_engine


def main():
    parser = add_postgres_arguments(argparse.ArgumentParser())
    args = parser.parse_args()

    scope = [
        'https://www.googleapis.com/auth/drive.metadata.readonly',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file',
    ]
    rel_path = Path(__file__).parent
    credentials = service_account.Credentials.from_service_account_file(
        filename=rel_path / "service_key.json",
        scopes=scope,
    )

    engine, con = postgres_engine(port=args.port, database=args.database)
    try:
        sold = pd.read_sql("SELECT * from raw.realtor__sold", con=con)
    finally:
        con.close()
        engine.dispose()

    sold = sold.astype(str)

    today = date.today().strftime("%Y%m%d")
    fp = f'{rel_path}/tmp/{today}_realtor_sold.parquet'
    sold.to_parquet(fp, index=False, engine='fastparquet')

    client = storage.Client(credentials=credentials, project='myproject')
    bucket = client.get_bucket('mybucket')
    blob = bucket.blob(f'{today}_realtor_sold.parquet')
    blob.upload_from_filename(fp)


if __name__ == "__main__":
    main()
