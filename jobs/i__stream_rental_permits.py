import requests
import json
import pandas as pd
from utils.database_utils import postgres_engine

def scrape_stream_rental_permits():
    with open("config/stream_headers_rental.json", 'r') as f:
        data = json.load(f)

    streamHeaders={
    'tenantid': '1',
    'Content-Type': 'application/json',
    }

    duplex='1492bd3e-e447-45a1-b69a-27aeff7c4fa0_6f6dcb98-1f7f-4f1f-8acb-287f3cce1f18'
    multi_fam='1492bd3e-e447-45a1-b69a-27aeff7c4fa0_c9bfe670-2caa-4fce-a198-82c26f629d51'
    rooming='1492bd3e-e447-45a1-b69a-27aeff7c4fa0_8a0008c2-76a3-414a-98b4-34de8bc80ee3'
    sfh='1492bd3e-e447-45a1-b69a-27aeff7c4fa0_d1726d7d-5487-4ee5-9187-53318dc0ac0b'

    url="https://stream.a2gov.org/EnerGov_Prod/selfservice/api/energov/search/search"

    df_list = []
    for licenseType in [duplex, multi_fam, rooming, sfh]:
        data['LicenseCriteria']['LicenseTypeId'] = licenseType
        req = requests.post(url, json= data, headers=streamHeaders)
        if req.status_code == 200:
            permits = json.loads(req.text)
            df = pd.DataFrame.from_dict(permits['Result']['EntityResults'])
            df_list.append(df)
    
    df_unlist = pd.concat(df_list, ignore_index=True)

    drops = ['Address', 'CountryTypeId', 'CountryTypeName']

    df_unnest = df_unlist.join(pd.json_normalize(df_unlist['Address'])).drop(drops ,axis='columns')

    return df_unnest

def load_to_db(df, table, schema):
    con = postgres_engine()
    df.to_sql(table, con, schema=schema, if_exists='overwrite', index=False)
    con.close()

if __name__ == "__main__":
    df = scrape_stream_rental_permits()
    load_to_db(df, 'stream__rental_permits', 'raw')