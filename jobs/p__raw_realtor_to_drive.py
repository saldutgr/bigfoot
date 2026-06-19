import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
import io
from googleapiclient.errors import HttpError
from pathlib import Path
from google.cloud import storage

from datetime import date
from utils.database_utils import postgres_engine



scope = ['https://www.googleapis.com/auth/drive.metadata.readonly',
'https://www.googleapis.com/auth/drive', 
'https://www.googleapis.com/auth/drive.file']
rel_path = Path(__file__).parent

service_account_json_key = rel_path / "service_key.json"
credentials = service_account.Credentials.from_service_account_file(
                              filename=service_account_json_key, 
                              scopes=scope)


service = build('drive', 'v3', credentials=credentials)

folder_metadata = {
        "name": "RealEstateData",
        "mimeType": "application/vnd.google-apps.folder"
    }
    # create the folder
#file = service.files().create(body=folder_metadata, fields="id").execute()
    # get the folder id


sold = pd.read_sql("SELECT * from raw.realtor__sold", con = postgres_engine())

sold = sold.astype(str)

today = date.today().strftime("%Y%m%d")
fp=f'{rel_path}/tmp/{today}_realtor_sold.parquet'

sold.to_parquet(fp, index=False, engine='fastparquet')

client = storage.Client(credentials=credentials, project='myproject')
bucket = client.get_bucket('mybucket')
blob = bucket.blob(f'{today}_realtor_sold.parquet')
blob.upload_from_filename(fp)
"""
file_metadata = {'name': f'{today}_realtor_sold.parquet', 
                 'parents':["1S-1vYU8p6Hsha81MfcDPbkf1DuO-FhNs"]}
media = MediaFileUpload(f'{rel_path}/tmp/{today}_realtor_sold.parquet',
                        mimetype=None, 
                        resumable=False)

file = service.files().create(body=file_metadata, 
                              media_body=media,
                              fields='id', 
                              supportsAllDrives=True).execute()
"""