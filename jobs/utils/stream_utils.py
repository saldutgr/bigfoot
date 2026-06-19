import json
import requests
import pandas


import config.stream_dicts as streamDicts

def to_snake_case(s):
    return ''.join(['_' + c.lower() if c.isupper() else c for c in s]).lstrip('_')

def scrape_stream_permits(permit_type_id=['bldgPermits','demoPermits']):
    """Query stream endpoint with permit type (stored in config.streamDicts)"""
    url = streamDicts.streamUrl
    permit_type = streamDicts.streamPermits[permit_type_id]
    payload = streamDicts.streamPayload
    payload['PermitCriteria']['PermitTypeId'] = permit_type
    headers = streamDicts.streamHeaders

    req = requests.post(url, json= payload, headers=headers)
    if req.status_code == 200:
        permits = json.loads(req.text)
        
        return permits

def normalize_stream_permits(json_object, fields:list):
    """Transform stream permit json"""
    df = pandas.DataFrame.from_dict(json_object['Result']['EntityResults'], orient='columns')
    df = df[fields]
    addresses = pandas.json_normalize(df['Address'])
    df = df.drop(['Address'], axis=1)
    df = pandas.concat([df,addresses], axis=1)


    df.columns = [to_snake_case(c).casefold() for c in df.columns]

    df['join_address'] = df.loc[:,'address_line1'].fillna('') + ' ' + df.loc[:,'address_line2'].fillna('')

    df['join_address'] = df['join_address'].apply(lambda x: x.upper().strip())


    return df

def get_stream_latlong(df, street_num_col, street_name_col):
    import shapely
    import geopandas
    #load address geodataframe
    df_addr = geopandas.read_file(streamDicts.address_url)
    df_addr.set_geometry('geometry', crs=2253)
    
    #Format dytpe for merge
    df_addr['STREETNUMBER'] = df_addr['STREETNUMBER'].astype(str).str.strip()

    #Ensure street name is uppercase and stripped for merge
    df[street_name_col] = df[street_name_col].str.upper().str.strip()
    
    #Merge on street name and number
    df_merged = df_addr.merge(df, right_on=[street_name_col, street_num_col], left_on=['STREET', 'STREETNUMBER'], how='right')

    #drop address cols
    keep = ['PIN', 'PackedPinLong','ADDRESSPTID', 'SITUS_ADR', 'geometry' ]
    drop = df_addr.columns.difference(keep)
    df_merged.drop(columns=drop, inplace=True)

    renamed = ['parcel_id', 'parcel_id_long', 'address_id', 'situs_address', 'geometry']

    col_dict = dict(zip(keep, renamed))

    df_merged = df_merged.rename(columns=col_dict)

    #Format CRS
    df_merged.set_geometry('geometry', crs=2253)
    df_merged.to_crs(epsg=4326, inplace=True)

    # Create GeoJSON geometry column
    df_merged['geometry_geojson'] = df_merged.geometry.apply(lambda x: json.dumps(shapely.geometry.mapping(x)) if x is not None else None)

    print(df_merged)
    
    return df_merged




                       
