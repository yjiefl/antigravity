
import requests
import json
from datetime import datetime, timedelta

# Old Date (20 days ago)
old_date = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')
lat = 22.8172
lon = 108.3661
fields = "temperature_2m,precipitation,wind_speed_10m"

# URL Construction similar to _build_api_url (Archive)
url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": lat,
    "longitude": lon,
    "start_date": old_date,
    "end_date": old_date,
    "hourly": fields,
    "minutely_15": fields,
    "timezone": "Asia/Shanghai"
}

print(f"Testing Archive API: {url} with params: {params}")

try:
    resp = requests.get(url, params=params)
    data = resp.json()
    
    print("\nResponse Keys:", data.keys())
    
    if 'minutely_15' in data:
        print("\nminutely_15 keys:", data['minutely_15'].keys())
        times = data['minutely_15'].get('time', [])
        print(f"minutely_15 time count: {len(times)}")
        if len(times) > 0:
            print("First 3 times:", times[:3])
    else:
        print("\nNO minutely_15 in response!")
        if 'reason' in data: print("Reason:", data['reason'])

    if 'hourly' in data:
        times_h = data['hourly'].get('time', [])
        print(f"\nhourly time count: {len(times_h)}")

except Exception as e:
    print(f"Error: {e}")
