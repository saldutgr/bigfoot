{{ config(
    materialized='incremental',
    indexes=[
        {"columns": ['geom'], "type": "gist"},
        {"columns": ["hash_id"], "type": "hash"}
        ],
    
        )}}


with source as (
     select * from {{ source('raw', 'here__traffic_flows') }}
      {% if is_incremental() %}
        where data_queried_at >= (select coalesce(max(data_queried_at),'1900-01-01') from {{ this }} )
    {% endif %}
)

select  
    concat(hashtext("location.description"), 'x', "location.length") as hash_id,
    "location.description" as street_name,
    "location.length" as length_hash,
    "currentFlow.speed" as speed_cappped,
    "currentFlow.speedUncapped" as speed_uncapped,
    "currentFlow.freeFlow" as flow_index,
    "currentFlow.jamFactor" as jam_index,
    "currentFlow.confidence" as confidence,
    "currentFlow.traversability" as traversability,
    "currentFlow.junctionTraversability" as junction_traversability,
    "currentFlow.jamTendency" as jam_tendency,
    
    data_queried_at,

    st_setsrid(geometry, 4326) as geom

from source

