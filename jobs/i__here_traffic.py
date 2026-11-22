import argparse
import os
from uuid import uuid4

import pandas as pd
import sqlalchemy
from dotenv import load_dotenv
from pandas import Timestamp

from utils.database_utils import add_postgres_arguments, postgres_engine
from utils.here_utils import get_traffic_data

load_dotenv()

TARGET_COLUMNS = [
    "row_id",
    "data_queried_at",
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
]


def load_to_db(df, table, schema, dtype=None, port=None, database=None):
    engine, con = postgres_engine(port=port, database=database)
    df.to_sql(table, con, schema=schema, if_exists='append', index=False, dtype=dtype)
    con.close()

def get_here_data():
    bbox = "-83.806746,42.224879,-83.670074,42.327828"
    api_key = os.getenv("HERE_API")

    response = get_traffic_data(bbox, api_key)
    data = pd.json_normalize(response["results"])

    queried_at = Timestamp.now(tz="UTC")
    data["data_queried_at"] = queried_at
    data["row_id"] = [str(uuid4()) for _ in range(len(data))]

    return data.reindex(columns=TARGET_COLUMNS)


if __name__ == "__main__":
    parser = add_postgres_arguments(argparse.ArgumentParser())
    args = parser.parse_args()
    df = get_here_data()

    load_to_db(
        df,
        "here__traffic_flows",
        "raw",
        dtype={
            "location.shape.links": sqlalchemy.types.JSON,
            "currentFlow.subSegments": sqlalchemy.types.JSON,
        },
        port=args.port,
        database=args.database,
    )


