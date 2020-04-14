import os
import sqlite3
import sys
from datetime import datetime

import terminaltables
from sqlite3 import Error
import argparse


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("booking_id", help="Which booking to compare?")
    return parser.parse_args()


def _format_time(time_in):
    try:
        time_in_converted = datetime.utcfromtimestamp(float(time_in))

    except ValueError:
        # 2020-03-13T15:18:56.19Z
        try:
            time_in_converted = datetime.strptime(time_in, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            time_in_converted = datetime.strptime(time_in, "%Y-%m-%dT%H:%M:%SZ")

    return time_in_converted.strftime("%b %d - %H:%M:%S")


def get_table(table_rows, title):
    table_data = [["Alert Type", "Reported Time"]]
    for row in table_rows:
        alert_type, reported_time = row[2:-2]
        reported_time = _format_time(reported_time)
        table_data.append([alert_type, reported_time])
    return terminaltables.other_tables.SingleTable(table_data, title=title)


def main():
    args = _get_args()
    try:
        conn = sqlite3.connect(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "logsdb.sqlite")
        )
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * from lumo where refid = ? order by ourTime", (args.booking_id,),
        )
        lumo_rows = cursor.fetchall()
        cursor.execute(
            "SELECT * from flightstats where refid = ? order by ourTime",
            (args.booking_id,),
        )
        flightstats_rows = cursor.fetchall()
    except Error as e:
        print(f"Sqlite Error: {e}")
        return 1
    finally:
        conn.close()
    print(get_table(lumo_rows, "Lumo").table)
    print(get_table(flightstats_rows, "Flighstats").table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
