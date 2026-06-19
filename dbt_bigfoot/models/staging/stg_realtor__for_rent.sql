with for_rent as (select * from {{ source('raw', 'realtor__for_rent') }}),

geom as (
select
    property_id,
    listing_id,
    mls,
    mls_id,
    status,
    st_setsrid(st_makepoint(longitude, latitude), 4326) as geom
from for_rent)

select * from geom
