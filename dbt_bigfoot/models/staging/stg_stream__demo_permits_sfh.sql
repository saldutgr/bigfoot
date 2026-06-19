with source as (select * from {{ source('raw', 'stream__demo_permits_sfh') }} )

select 
    main_parcel as parcel_id,
    concat(address_line1, ' ',
           pre_direction, ' ',
            address_line2, ' ',
            street_type_name, ' ', 
            address_line3) as full_address,
    case_number,
    case_id,
    project_name,
    case_type,
    case_status,
    description,

    is_main,

    apply_date as date_applied,
    issue_date as date_issued,
    final_date as date_final,
    expire_date as date_expired
from source
