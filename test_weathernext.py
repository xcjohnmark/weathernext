import json
import sys
import urllib.request
import urllib.error
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Target date (defaults to 2026-09-30, or accepts YYYY-MM-DD as command-line argument)
TARGET_DATE = sys.argv[1] if len(sys.argv) > 1 else "2026-09-30"

# Strict mapping of Kalshi KXRAIN cities to official NWS station codes & coordinates
STATIONS = [
    {
        "city": "Chicago",
        "station_code": "CLIORD",
        "lat": 41.9742,
        "lon": -87.9073,
        "timezone": "America/Chicago",
    },
    {
        "city": "Denver",
        "station_code": "CLIDEN",
        "lat": 39.8561,
        "lon": -104.6737,
        "timezone": "America/Denver",
    },
    {
        "city": "Los Angeles",
        "station_code": "CLILAX",
        "lat": 33.9425,
        "lon": -118.4081,
        "timezone": "America/Los_Angeles",
    },
    {
        "city": "Las Vegas",
        "station_code": "CLILAS",
        "lat": 36.0840,
        "lon": -115.1537,
        "timezone": "America/Los_Angeles",
    },
    {
        "city": "Miami",
        "station_code": "CLIMIA",
        "lat": 25.7959,
        "lon": -80.2870,
        "timezone": "America/New_York",
    },
    {
        "city": "New Orleans",
        "station_code": "CLIMSY",
        "lat": 29.9934,
        "lon": -90.2580,
        "timezone": "America/Chicago",
    },
    {
        "city": "New York City",
        "station_code": "CLINYC",
        "lat": 40.7829,
        "lon": -73.9654,
        "timezone": "America/New_York",
    },
    {
        "city": "Philadelphia",
        "station_code": "CLIPHL",
        "lat": 39.8729,
        "lon": -75.2437,
        "timezone": "America/New_York",
    },
    {
        "city": "San Francisco",
        "station_code": "CLISFO",
        "lat": 37.6213,
        "lon": -122.3790,
        "timezone": "America/Los_Angeles",
    },
    {
        "city": "Trenton",
        "station_code": "CLITTN",
        "lat": 40.2767,
        "lon": -74.8160,
        "timezone": "America/New_York",
    },
    {
        "city": "Atlanta",
        "station_code": "CLIATL",
        "lat": 33.6407,
        "lon": -84.4277,
        "timezone": "America/New_York",
    },
    {
        "city": "Austin",
        "station_code": "CLIAUS",
        "lat": 30.1975,
        "lon": -97.6664,
        "timezone": "America/Chicago",
    },
    {
        "city": "Boston",
        "station_code": "CLIBOS",
        "lat": 42.3656,
        "lon": -71.0096,
        "timezone": "America/New_York",
    },
    {
        "city": "Dallas",
        "station_code": "CLIDFW",
        "lat": 32.8998,
        "lon": -97.0403,
        "timezone": "America/Chicago",
    },
    {
        "city": "Washington DC",
        "station_code": "CLIDCA",
        "lat": 38.8512,
        "lon": -77.0402,
        "timezone": "America/New_York",
    },
    {
        "city": "Newark",
        "station_code": "CLIEWR",
        "lat": 40.6895,
        "lon": -74.1745,
        "timezone": "America/New_York",
    },
    {
        "city": "Houston",
        "station_code": "CLIHOU",
        "lat": 29.6454,
        "lon": -95.2789,
        "timezone": "America/Chicago",
    },
    {
        "city": "Minneapolis",
        "station_code": "CLIMSP",
        "lat": 44.8848,
        "lon": -93.2223,
        "timezone": "America/Chicago",
    },
    {
        "city": "Oklahoma City",
        "station_code": "CLIOKC",
        "lat": 35.3931,
        "lon": -97.6007,
        "timezone": "America/Chicago",
    },
    {
        "city": "Phoenix",
        "station_code": "CLIPHX",
        "lat": 33.4373,
        "lon": -112.0078,
        "timezone": "America/Phoenix",
    },
    {
        "city": "San Antonio",
        "station_code": "CLISAT",
        "lat": 29.5337,
        "lon": -98.4698,
        "timezone": "America/Chicago",
    },
    {
        "city": "Seattle",
        "station_code": "CLISEA",
        "lat": 47.4502,
        "lon": -122.3088,
        "timezone": "America/Los_Angeles",
    },
]

THRESHOLD_MM = 0.25  # 0.01 inches strictly required by Kalshi


def fetch_forecast(station_info, target_date):
    """Fetches WeatherNext ensemble forecast for a given station and computes rain probability."""
    lat = station_info["lat"]
    lon = station_info["lon"]
    tz = station_info["timezone"]
    station_code = station_info["station_code"]

    url = (
        f"https://ensemble-api.open-meteo.com/v1/ensemble?"
        f"latitude={lat}&longitude={lon}&"
        f"models=google_weathernext2_ensemble&"
        f"hourly=precipitation&"
        f"timezone={tz.replace('/', '%2F')}"
    )

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return {
            "station_code": station_code,
            "error": str(e),
            "expected_mean_mm": 0.0,
            "yes_votes": 0,
            "total_members": 63,
            "probability": 0.0,
        }

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])

    day_indices = [i for i, t in enumerate(times) if t.startswith(target_date)]
    if not day_indices:
        return {
            "station_code": station_code,
            "error": f"Target date {target_date} not found in forecast horizon.",
            "expected_mean_mm": 0.0,
            "yes_votes": 0,
            "total_members": 63,
            "probability": 0.0,
        }

    member_keys = [k for k in hourly.keys() if k.startswith("precipitation_member")]
    yes_votes = 0
    total_members = len(member_keys) if member_keys else 63
    member_daily_totals = []

    for member in member_keys:
        member_hourly = hourly[member]
        daily_total = sum(
            member_hourly[i]
            for i in day_indices
            if i < len(member_hourly) and member_hourly[i] is not None
        )
        member_daily_totals.append(daily_total)
        if daily_total >= THRESHOLD_MM:
            yes_votes += 1

    # True ensemble mean is the arithmetic mean across all ensemble members
    mean_total = (
        sum(member_daily_totals) / len(member_daily_totals)
        if member_daily_totals
        else 0.0
    )
    prob_rain = (yes_votes / total_members) * 100 if total_members > 0 else 0.0

    return {
        "station_code": station_code,
        "city": station_info["city"],
        "error": None,
        "expected_mean_mm": mean_total,
        "yes_votes": yes_votes,
        "total_members": total_members,
        "probability": prob_rain,
    }


def main():
    # Execute network requests concurrently for high scalability
    results = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_station = {
            executor.submit(fetch_forecast, station, TARGET_DATE): station
            for station in STATIONS
        }
        for future in as_completed(future_to_station):
            station = future_to_station[future]
            try:
                res = future.result()
                results[res["station_code"]] = res
            except Exception as e:
                results[station["station_code"]] = {
                    "station_code": station["station_code"],
                    "city": station["city"],
                    "error": str(e),
                    "expected_mean_mm": 0.0,
                    "yes_votes": 0,
                    "total_members": 63,
                    "probability": 0.0,
                }

    # Print output in the exact order requested
    for station in STATIONS:
        code = station["station_code"]
        res = results.get(code)
        if not res or res.get("error"):
            print(f"=== WeatherNext Forecast for {TARGET_DATE} at {code} ===")
            print(f"Error fetching data: {res.get('error') if res else 'Unknown error'}\n")
            continue

        mean_mm = res["expected_mean_mm"]
        mean_in = mean_mm / 25.4
        yes_votes = res["yes_votes"]
        total_members = res["total_members"]
        prob = res["probability"]

        print(f"=== WeatherNext Forecast for {TARGET_DATE} at {code} ===")
        print(f"Expected Mean Daily Rain: {mean_mm:.2f} mm ({mean_in:.3f} inches)")
        print(f"Ensemble Voting Rain (>= 0.01 in): {yes_votes} / {total_members}")
        print(f"WeatherNext Model Probability of YES: {prob:.1f}%\n")


if __name__ == "__main__":
    main()