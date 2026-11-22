import argparse
import csv
import json
from io import StringIO
from uuid import uuid5, NAMESPACE_URL

from dotenv import load_dotenv
from sqlalchemy import text

from utils.database_utils import postgres_engine

load_dotenv()

TABLE = "raw.here__traffic_flows"
SOURCE_TABLE = "raw.here__traffic_flows"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-port", type=int, required=True)
    parser.add_argument("--destination-port", type=int, required=True)
    parser.add_argument("--source-database", default="bigfoot")
    parser.add_argument("--destination-database", default="bigfoot")
    parser.add_argument("--batch-size", type=int, default=50000)
    return parser.parse_args()


def copy_json(value):
    if value is None:
        return None
    if isinstance(value, str):
        try:
            json.loads(value)
            return value
        except json.JSONDecodeError:
            return json.dumps(value)
    return json.dumps(value)


def main():
    args = parse_args()
    if args.batch_size < 1:
        raise ValueError("--batch-size must be greater than zero")

    _, source = postgres_engine(
        port=args.source_port,
        database=args.source_database,
    )
    _, destination = postgres_engine(
        port=args.destination_port,
        database=args.destination_database,
    )

    copied = 0

    try:
        has_row_id = source.execute(text("""
            select exists (
                select 1
                from information_schema.columns
                where table_schema = 'raw'
                  and table_name = 'here__traffic_flows'
                  and column_name = 'row_id'
            )
        """)).scalar_one()

        with destination.begin():
            destination.execute(text(f"""
                DROP TABLE IF EXISTS {TABLE} CASCADE;

                CREATE TABLE {TABLE} (
                    row_id text PRIMARY KEY,
                    data_queried_at timestamptz,
                    "location.description" text,
                    "location.length" double precision,
                    "location.shape.links" jsonb,
                    "currentFlow.speed" double precision,
                    "currentFlow.speedUncapped" double precision,
                    "currentFlow.freeFlow" double precision,
                    "currentFlow.jamFactor" double precision,
                    "currentFlow.confidence" double precision,
                    "currentFlow.traversability" text,
                    "currentFlow.junctionTraversability" text,
                    "currentFlow.jamTendency" double precision,
                    "currentFlow.subSegments" jsonb
                );
            """))

        row_id_select = '"row_id"' if has_row_id else "null::text"
        source_result = source.execution_options(
            stream_results=True
        ).execute(text(f"""
            SELECT
                ctid::text AS source_ctid,
                {row_id_select} AS source_row_id,
                "location.description",
                "location.length",
                "location.shape.links",
                "currentFlow.speed",
                "currentFlow.speedUncapped",
                "currentFlow.freeFlow",
                "currentFlow.jamFactor",
                "currentFlow.confidence",
                "currentFlow.traversability",
                "currentFlow.junctionTraversability",
                "currentFlow.jamTendency",
                "currentFlow.subSegments",
                data_queried_at
            FROM {SOURCE_TABLE}
        """))

        while True:
            source_rows = source_result.fetchmany(args.batch_size)
            if not source_rows:
                break

            buffer = StringIO()
            writer = csv.writer(buffer)

            for result_row in source_rows:
                row = dict(result_row._mapping)
                source_row_id = row.pop("source_row_id")
                source_ctid = row.pop("source_ctid")

                row_id = source_row_id or str(uuid5(
                    NAMESPACE_URL,
                    f"here-traffic:{source_ctid}",
                ))

                writer.writerow([
                    row_id,
                    row.get("data_queried_at"),
                    row.get("location.description"),
                    row.get("location.length"),
                    copy_json(row.get("location.shape.links")),
                    row.get("currentFlow.speed"),
                    row.get("currentFlow.speedUncapped"),
                    row.get("currentFlow.freeFlow"),
                    row.get("currentFlow.jamFactor"),
                    row.get("currentFlow.confidence"),
                    row.get("currentFlow.traversability"),
                    row.get("currentFlow.junctionTraversability"),
                    row.get("currentFlow.jamTendency"),
                    copy_json(row.get("currentFlow.subSegments")),
                ])

            buffer.seek(0)
            with destination.begin():
                cursor = destination.connection.connection.cursor()
                cursor.copy_expert(
                    f"""
                    COPY {TABLE} (
                        row_id,
                        data_queried_at,
                        "location.description",
                        "location.length",
                        "location.shape.links",
                        "currentFlow.speed",
                        "currentFlow.speedUncapped",
                        "currentFlow.freeFlow",
                        "currentFlow.jamFactor",
                        "currentFlow.confidence",
                        "currentFlow.traversability",
                        "currentFlow.junctionTraversability",
                        "currentFlow.jamTendency",
                        "currentFlow.subSegments"
                    )
                    FROM STDIN WITH (FORMAT CSV)
                    """,
                    buffer,
                )

            copied += len(source_rows)
            print(f"Copied {copied} rows", flush=True)

        source_count = source.execute(text(
            f"SELECT COUNT(*) FROM {SOURCE_TABLE}"
        )).scalar_one()
        destination_count = destination.execute(text(
            f"SELECT COUNT(*) FROM {TABLE}"
        )).scalar_one()

        if source_count != destination_count:
            raise RuntimeError(
                f"Row count mismatch: source={source_count}, "
                f"destination={destination_count}"
            )

        print(
            f"Migration complete: copied {destination_count} rows "
            f"from {args.source_database}:{args.source_port} "
            f"to {args.destination_database}:{args.destination_port}"
        )
    finally:
        source.close()
        destination.close()


if __name__ == "__main__":
    main()