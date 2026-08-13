with for_rent as (select * from {{ source('raw', 'realtor__for_rent') }}),

geom as (
select
    property_id,
    street,
    unit,
    listing_id,
    mls,
    mls_id,
    status,
    list_price,
    list_price_min,
    list_price_max,
    coalesce(list_price, (list_price_min + list_price_max) /2) as ask_price,

    last_sold_date,
    last_sold_price,
    last_update_date,
    list_date,
    st_setsrid(st_makepoint(longitude, latitude), 4326) as geom
from for_rent)

select * from geom
