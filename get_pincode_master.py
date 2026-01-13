import requests
import pandas as pd
import io
import time
import os

# --- CONFIGURATION ---
API_KEY = "579b464db66ec23bdd000001cbae3903783d4b4b72aa736063717f69" # <--- PASTE YOUR KEY
RESOURCE_ID = "5c2f62fe-5afa-4119-a499-fec9d604d5bd"
OUTPUT_FILE = "official_pincode_directory.csv"

def download_pincodes_safely():
    print(f"Downloading Official Pincode Directory to {OUTPUT_FILE}...")
    
    # 1. Clear the old file if it exists so we start fresh
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    limit = 10000 
    offset = 0
    write_header = True # We need to write the header for the first batch
    
    while True:
        url = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
        params = {
            'api-key': API_KEY,
            'format': 'csv',
            'limit': limit,
            'offset': offset
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            # Check for server errors
            if response.status_code != 200:
                print(f"Server Error {response.status_code}. Retrying in 2s...")
                time.sleep(2)
                continue

            # Check if response is empty (End of data)
            if not response.content.strip():
                print("End of data reached (Empty content).")
                break

            # Parse CSV
            csv_content = io.StringIO(response.content.decode('utf-8'))
            try:
                df = pd.read_csv(csv_content)
            except pd.errors.EmptyDataError:
                print("End of data reached (No columns).")
                break
            
            if df.empty:
                print("End of data reached (Empty DataFrame).")
                break
                
            # RENAME COLUMNS STANDARDIZED
            # We map whatever the server sends to standard names
            # Common names in this dataset: pincode, district, statename, latitude, longitude
            df.rename(columns={
                'pincode': 'Pincode',
                'statename': 'State', 
                'district': 'District',
                'latitude': 'Latitude',
                'longitude': 'Longitude'
            }, inplace=True)

            # SAVE TO DISK IMMEDIATELY
            mode = 'w' if write_header else 'a' # 'w' for first batch, 'a' (append) for rest
            df.to_csv(OUTPUT_FILE, mode=mode, index=False, header=write_header)
            
            print(f"Saved {len(df)} rows (Offset: {offset})")
            
            # Turn off header for next loops
            write_header = False 

            # Break if we got fewer rows than requested (Standard API behavior)
            if len(df) < limit:
                print("Last batch received. Download Complete.")
                break
            
            offset += len(df)
            
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            print("Retrying...")
            time.sleep(2)

if __name__ == "__main__":
    download_pincodes_safely()