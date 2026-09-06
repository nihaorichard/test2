#!/usr/bin/env python3
"""
GTFS Filter Tool
-----------------
Filters a full GTFS feed down to only the rows relevant to a set of
"target" stops (e.g. Klinikum and BBZ Weimar), so you can build a
transfer-itinerary dashboard without uploading huge files.

USAGE:
1. Put this script in the same folder as your GTFS_TXT files
   (agency.txt, stops.txt, stop_times.txt, trips.txt, routes.txt,
   calendar.txt, calendar_dates.txt, transfers.txt, frequencies.txt).
2. Edit TARGET_STOP_PREFIXES below if needed.
3. Run:  python3 filter_gtfs.py
4. It creates a "filtered_output" folder with small CSVs you can
   upload here (should be a few KB to a few MB, not 90+ MB).

Requires only the Python standard library (no installs needed).
"""

import csv
import os

# ---- CONFIGURE YOUR TARGET STOPS HERE ----
# Any stop_id that STARTS WITH one of these prefixes is considered a
# target stop. Using prefixes lets one entry catch all platform/child
# stop_ids belonging to the same station (e.g. ...15518100 and ...15518101).
TARGET_STOP_PREFIXES = [
    "de:16055:155033",   # Weimar, Klinikum
    "de:16055:155181",   # Weimar, BBZ Weimar
]

INPUT_DIR = "."
OUTPUT_DIR = "filtered_output"


def is_target_stop(stop_id):
    return any(stop_id.startswith(p) for p in TARGET_STOP_PREFIXES)


def read_csv(path):
    if not os.path.exists(path):
        print(f"  (skipped, not found: {path})")
        return None, []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return reader.fieldnames, rows


def write_csv(path, fieldnames, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {len(rows)} rows -> {path}")


def main():
    print("Reading stops.txt ...")
    stops_fields, stops = read_csv(os.path.join(INPUT_DIR, "stops.txt"))
    target_stops = [r for r in stops if is_target_stop(r["stop_id"])]
    target_stop_ids = {r["stop_id"] for r in target_stops}
    print(f"  found {len(target_stops)} matching stop rows")
    for r in target_stops:
        print(f"    {r['stop_id']}  -  {r.get('stop_name','')}")

    print("\nReading stop_times.txt (this is the big one, please wait) ...")
    st_fields, stop_times = read_csv(os.path.join(INPUT_DIR, "stop_times.txt"))
    matching_st = [r for r in stop_times if r["stop_id"] in target_stop_ids]
    trip_ids = {r["trip_id"] for r in matching_st}
    print(f"  found {len(matching_st)} stop_times rows across {len(trip_ids)} trips")

    print("\nReading trips.txt ...")
    trips_fields, trips = read_csv(os.path.join(INPUT_DIR, "trips.txt"))
    matching_trips = [r for r in trips if r["trip_id"] in trip_ids]
    route_ids = {r["route_id"] for r in matching_trips}
    service_ids = {r["service_id"] for r in matching_trips}
    print(f"  found {len(matching_trips)} matching trips, {len(route_ids)} routes, {len(service_ids)} services")

    print("\nReading routes.txt ...")
    routes_fields, routes = read_csv(os.path.join(INPUT_DIR, "routes.txt"))
    matching_routes = [r for r in routes if r["route_id"] in route_ids]

    print("\nReading calendar.txt ...")
    cal_fields, calendar = read_csv(os.path.join(INPUT_DIR, "calendar.txt"))
    matching_calendar = [r for r in calendar if r["service_id"] in service_ids] if calendar else []

    print("\nReading calendar_dates.txt ...")
    cd_fields, cal_dates = read_csv(os.path.join(INPUT_DIR, "calendar_dates.txt"))
    matching_cal_dates = [r for r in cal_dates if r["service_id"] in service_ids] if cal_dates else []

    print("\nReading transfers.txt ...")
    tr_fields, transfers = read_csv(os.path.join(INPUT_DIR, "transfers.txt"))
    matching_transfers = []
    if transfers:
        matching_transfers = [
            r for r in transfers
            if r.get("from_stop_id") in target_stop_ids
            or r.get("to_stop_id") in target_stop_ids
        ]

    print("\nReading frequencies.txt ...")
    fr_fields, frequencies = read_csv(os.path.join(INPUT_DIR, "frequencies.txt"))
    matching_frequencies = [r for r in frequencies if r["trip_id"] in trip_ids] if frequencies else []

    print("\n--- Writing filtered files ---")
    if stops_fields:
        write_csv(os.path.join(OUTPUT_DIR, "stops.txt"), stops_fields, target_stops)
    if st_fields:
        write_csv(os.path.join(OUTPUT_DIR, "stop_times.txt"), st_fields, matching_st)
    if trips_fields:
        write_csv(os.path.join(OUTPUT_DIR, "trips.txt"), trips_fields, matching_trips)
    if routes_fields:
        write_csv(os.path.join(OUTPUT_DIR, "routes.txt"), routes_fields, matching_routes)
    if cal_fields and matching_calendar:
        write_csv(os.path.join(OUTPUT_DIR, "calendar.txt"), cal_fields, matching_calendar)
    if cd_fields and matching_cal_dates:
        write_csv(os.path.join(OUTPUT_DIR, "calendar_dates.txt"), cd_fields, matching_cal_dates)
    if tr_fields and matching_transfers:
        write_csv(os.path.join(OUTPUT_DIR, "transfers.txt"), tr_fields, matching_transfers)
    if fr_fields and matching_frequencies:
        write_csv(os.path.join(OUTPUT_DIR, "frequencies.txt"), fr_fields, matching_frequencies)

    print(f"\nDone! Upload the files inside the '{OUTPUT_DIR}' folder.")


if __name__ == "__main__":
    main()
