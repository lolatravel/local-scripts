import json
import sqlite3
import os
from glob import iglob
from sqlite3 import Error


def create_schema(conn):
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE lumo (refid TEXT, type TEXT, request_id TEXT, reportedTime TEXT, ourTime REAL, notification TEXT)
        """
    )
    c.execute(
        """
        CREATE TABLE flightstats (refid TEXT, request_id TEXT, type TEXT, reportedTime TEXT, ourTime REAL, notification TEXT)
        """
    )
    return c


def _yield_logs_in_dir(dirname):
    for f in iglob(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), dirname, r"*.json")
    ):
        with open(f) as infile:
            yield json.load(infile)


def add_lumo_logs(cursor):
    for log in _yield_logs_in_dir("lumo-logs"):
        alert = log["data"]["alert"]
        cursor.execute(
            """
            INSERT INTO lumo VALUES(?, ?, ?, ?, ?)
            """,
            (
                alert["booking_reference"].replace("production", ""),
                log["request_id"],
                alert["change"],
                alert["timestamp"],
                float(log["_created"]),
                json.dumps(log["data"]),
            ),
        )


def add_flightstats_logs(cursor):
    for log in _yield_logs_in_dir("flightstats-logs"):
        alert = json.loads(log["data"])
        cursor.execute(
            """
            INSERT INTO flightstats VALUES(?, ?, ?, ?, ?)
            """,
            (
                alert["trip"]["referenceNumber"],
                log["request_id"],
                alert["alertDetails"]["type"],
                alert["alertDetails"]["dateTime"],
                float(log["_created"]),
                log["data"],
            ),
        )


def create_database(db_file):
    # Logs are pulled down from s3
    # aws s3 cp --recursive s3://bloblogs.ops.lola.com/blobs/production/flightstats-alert flightstats-logs
    # aws s3 cp --recursive s3://bloblogs.ops.lola.com/blobs/production/lumo-alert/ lumo-logs
    # They are not committed to the repo
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = create_schema(conn)
        add_lumo_logs(cursor)
        add_flightstats_logs(cursor)
        conn.commit()
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    create_database(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "logsdb.sqlite")
    )
