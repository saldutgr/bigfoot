{{ config(
    materialized='table',
    indexes=[
        {"columns": ['geom'],
            "type": "gist"}
    ])}}

with source as (select * from {{ source('raw', 'realtor__sold') }})

select 
    -- ids
    property_id as realtor_property_id,
    listing_id as realtor_listing_id,
    mls_id,

    -- property info
    full_street_line,
    unit,

    -- property attributes
    style,
    beds,
    full_baths,
    half_baths, 
    sqft, 
    year_built::integer as year_built,

    -- sale attributes
    sold_price::integer as sold_price,
    list_price::integer as list_price,
    days_on_mls::integer as days_on_mls,
    estimated_value::integer as estimated_value,

    --date
    last_sold_date as last_sold,
    last_status_change_date as status_updated_at,
    last_update_date as updated_at,
    data_loaded_at,

    -- lot info
    lot_sqft as lot_size_sqft,
    price_per_sqft,
    parking_garage as num_parking_spaces,
    stories as num_stores,

    st_setsrid(st_makepoint(longitude, latitude), 4326) as geom

from source
