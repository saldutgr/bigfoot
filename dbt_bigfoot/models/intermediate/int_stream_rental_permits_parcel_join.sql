with 
    parcel as (select * from {{ ref('stg_city__parcel_shapes_2025') }}),
    rental_permits as (select * from {{ ref("stg_stream__rental_permits")}}),
    parcel_attributes as (select * from {{ ref("stg_city__parcel_attributes_2025") }}),
    realtor_rentals as (select * from {{ ref('int_rentals_parcels_joined')}})

select 
    --rental_permits.parcel_id, 
    rental_permits.full_address,
    rental_permits.case_type,
    rental_permits.company_name,
    rental_permits.description,

    parcel_attributes.full_address as parcel_address,
    parcel_attributes.taxpayer_name,
    parcel_attributes.taxpayer_address,
    parcel_attributes.is_condo,
    parcel_attributes.is_apartment,
    parcel_attributes.taxable_value,

    realtor_rentals.*


from rental_permits
left join parcel on rental_permits.parcel_id = parcel.parcel_id
left join parcel_attributes on rental_permits.parcel_id = parcel_attributes.parcel_id
left join realtor_rentals on rental_permits.parcel_id = realtor_rentals.parcel_id
