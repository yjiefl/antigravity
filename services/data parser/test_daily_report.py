
import os
import sys
import pandas as pd
from daily_report_web import analyze_daily_report

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "input", "运营日报 - 2026-02-11_2026-02-12.xls")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

print(f"Testing analysis on: {INPUT_FILE}")

if not os.path.exists(INPUT_FILE):
    print("Error: Input file found.")
    sys.exit(1)

try:
    result, error = analyze_daily_report(INPUT_FILE, OUTPUT_DIR)
    
    if error:
        print(f"Analysis Failed: {error}")
    else:
        print("Analysis Success!")
        print(f"Overview: {result['overview']}")
        print(f"Stations Found: {len(result['stations_data'])}")
        print(f"Anomalies: {len(result['anomalies'])}")
        print(f"Passes: {len(result['passes'])}")

except Exception as e:
    print(f"Exception Occurred: {e}")
    import traceback
    traceback.print_exc()
