{{ config(
    materialized='table',
    indexes=[
        {"columns": ['row_id'], "type": 'btree'},
        
    ]
) }}

with raw_routes as (
    select
        row_id,
        data_queried_at,
        "location.description" as route_name,
        "location.length"::double precision as route_length,
        "currentFlow.speed"::double precision as route_speed,
        "currentFlow.speedUncapped"::double precision as route_speed_uncapped,
        "currentFlow.freeFlow"::double precision as route_free_flow,
        "currentFlow.jamFactor"::double precision as route_jam_factor,
        "currentFlow.confidence"::double precision as route_confidence,
        "currentFlow.traversability" as route_traversability,
        "currentFlow.junctionTraversability" as route_junction_traversability,
        "currentFlow.jamTendency"::double precision as route_jam_tendency,
        "currentFlow.subSegments"::jsonb as subsegments
    from {{ source('raw', 'here__traffic_flows') }}
),

expanded as (
    select
        r.*,
        s.segment,
        s.segment_ord
    from raw_routes r
    left join lateral jsonb_array_elements(
        case
            when jsonb_typeof(r.subsegments) = 'array' then r.subsegments
            else '[]'::jsonb
        end
    ) with ordinality as s(segment, segment_ord)
        on true
)

select
    e.row_id,
    e.data_queried_at,
    e.route_name,
    e.segment_ord,
    coalesce(
        (e.segment ->> 'length')::double precision,
        e.route_length
    ) as length,
    coalesce(
        (e.segment ->> 'speed')::double precision,
        e.route_speed
    ) as speed,
    coalesce(
        (e.segment ->> 'speedUncapped')::double precision,
        e.route_speed_uncapped
    ) as speed_uncapped,
    coalesce(
        (e.segment ->> 'freeFlow')::double precision,
        e.route_free_flow
    ) as free_flow,
    coalesce(
        (e.segment ->> 'jamFactor')::double precision,
        e.route_jam_factor
    ) as jam_factor,
    coalesce(
        (e.segment ->> 'confidence')::double precision,
        e.route_confidence
    ) as confidence,
    coalesce(
        e.segment ->> 'traversability',
        e.route_traversability
    ) as traversability,
    coalesce(
        e.segment ->> 'junctionTraversability',
        e.route_junction_traversability
    ) as junction_traversability,
    coalesce(
        (e.segment ->> 'jamTendency')::double precision,
        e.route_jam_tendency
    ) as jam_tendency
from expanded e
left join {{ ref('int_traffic_flow_geometry') }} g
    on g.row_id = e.row_id
   and g.segment_ord is not distinct from e.segment_ord
