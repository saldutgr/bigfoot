with 
    sold as (select * from {{ ref("stg_realtor__for_rent") }}),
    parcels as (select * from {{ ref('stg_city__parcel_shapes_2025') }})

select sold.*, parcels.parcel_id from sold
left join parcels on st_within(sold.geom, parcels.geom)
