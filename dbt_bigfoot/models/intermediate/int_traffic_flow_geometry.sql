{{ config(
    materialized='table',
    indexes=[
        {"columns": ['row_id'], "type": "btree"},
        {"columns": ['geometry'], "type": 'gist'}
    ]
) }}

with raw_routes as (
    select
        row_id,
        "location.length"::double precision as route_length,
        "location.shape.links"::jsonb as route_shape,
        "currentFlow.subSegments"::jsonb as subsegments
    from {{ source('raw', 'here__traffic_flows') }}
),

route_geometries as (
    select
        r.row_id,
        raw.ST_Transform(
            raw.ST_SetSRID(
                raw.ST_MakeLine(
                    raw.ST_MakePoint(
                        (p.point ->> 'lng')::double precision,
                        (p.point ->> 'lat')::double precision
                    )
                    order by l.link_ord, p.point_ord
                ),
                4326
            ),
            2253
        ) as route_geometry
    from raw_routes r
    cross join lateral jsonb_array_elements(
        case
            when jsonb_typeof(r.route_shape) = 'array' then r.route_shape
            else '[]'::jsonb
        end
    ) with ordinality as l(link, link_ord)
    cross join lateral jsonb_array_elements(
        case
            when jsonb_typeof(l.link -> 'points') = 'array'
                then l.link -> 'points'
            else '[]'::jsonb
        end
    ) with ordinality as p(point, point_ord)
    group by r.row_id
),

expanded as (
    select
        r.row_id,
        r.route_length,
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
),

segment_bounds as (
    select
        e.*,
        coalesce(
            sum(coalesce((e.segment ->> 'length')::double precision, 0)) over (
                partition by e.row_id
                order by e.segment_ord
                rows between unbounded preceding and 1 preceding
            ),
            0
        ) as start_length,
        sum(coalesce((e.segment ->> 'length')::double precision, 0)) over (
            partition by e.row_id
            order by e.segment_ord
            rows between unbounded preceding and current row
        ) as end_length,
        sum(coalesce((e.segment ->> 'length')::double precision, 0)) over (
            partition by e.row_id
        ) as segment_length
    from expanded e
),

with_route_geometry as (
    select
        b.*,
        rg.route_geometry,
        coalesce(
            nullif(b.route_length, 0),
            nullif(b.segment_length, 0)
        ) as split_length
    from segment_bounds b
    left join route_geometries rg
        on rg.row_id = b.row_id
)

select
    row_id,
    segment_ord,
    case
        when segment is null then route_geometry
        when route_geometry is null then null
        when split_length is null then null
        else raw.ST_LineSubstring(
            route_geometry,
            least(
                greatest(
                    start_length / split_length,
                    0
                ),
                1
            ),
            least(
                greatest(
                    end_length / split_length,
                    0
                ),
                1
            )
        )
    end as geometry
from with_route_geometry
