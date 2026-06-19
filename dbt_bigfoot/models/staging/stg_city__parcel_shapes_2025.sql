{{ config(
    materialized='table',
    indexes=[
        {'columns':['geom'],
        'type': "gist"}
        ]
        )}}

with parcels as (select * from {{source('raw', 'parcel_shapes_2025')}})

select 
    parcel_id,
    st_geomfromtext(geometry, 4326) as geom
from parcels