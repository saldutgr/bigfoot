with 
    parcels as (select * from {{ source('raw', 'parcel_attributes_2025') }}),

    renamed as (
        select 
            "PIN" as parcel_id, 
            "PACKEDPIN" as p_parcel_id,
            "PRPANUMB" as street_number,
            "PRPASTRT" as street_name,
            "PRPACOM" as full_address,

            "OWNNAME1" as taxpayer_name,
            "OWNNAME2" as taxpayer_name_2,
            "OWNSTADDR" as taxpayer_address,
            "OWNSTATE" as taxpayer_state,
            "OWNZIP" as taxpayer_zip,

            "Condo" as is_condo,
            "APARTMENT" as is_apartment,

            lastsaledate as last_sale_date,
            lastsaleprice as last_sale_price,
            landvalue as land_value,
            "taxableValue" as taxable_value
        from parcels

    )

select * from renamed
