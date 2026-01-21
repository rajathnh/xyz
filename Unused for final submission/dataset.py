import requests
import pandas as pd
import io
import time
import os

# --- CONFIGURATION ---
API_KEY = "579b464db66ec23bdd000001cbae3903783d4b4b72aa736063717f69"  # <--- PASTE YOUR KEY AGAIN
RESOURCE_ID = "ecd49b12-3084-4521-8f7e-ca8bf72069ba"
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

# FILE SETTINGS
OUTPUT_FILE = "aadhaar_monthly_data_full.csv" # Using the same filename to append
START_OFFSET = 8000  # <--- CHANGED: Resume from where it crashed
CHUNK_SIZE = 1000    # Keep at 1000
MAX_RETRIES = 5      # Will try 5 times before giving up on a chunk

def fetch_data():
    offset = START_OFFSET
    
    # Check if file exists to determine if we need to write headers
    file_exists = os.path.isfile(OUTPUT_FILE)
    
    # If we are starting from 0, we need headers. 
    # If appending (offset > 0), we assume headers exist.
    need_header = True if offset == 0 else False

    print(f"Resuming download from offset {offset}...")
    print(f"Appending to: {OUTPUT_FILE}")
    print("-" * 50)

    while True:
        params = {
            'api-key': API_KEY,
            'format': 'csv',
            'limit': CHUNK_SIZE,
            'offset': offset
        }

        success = False
        
        # --- RETRY LOOP ---
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(BASE_URL, params=params, timeout=30)
                
                # If 504/502/500 error, this raises an exception immediately
                response.raise_for_status()
                
                success = True
                break # Exit retry loop if successful
            
            except requests.exceptions.RequestException as e:
                wait_time = (attempt + 1) * 5
                print(f"  [Attempt {attempt+1}/{MAX_RETRIES}] Failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    print(f"  Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("  Max retries reached. Moving to critical error.")

        if not success:
            print(f"\nCRITICAL: Could not fetch offset {offset} after {MAX_RETRIES} attempts.")
            print("Stopping script. You can resume later by updating START_OFFSET.")
            break

        # --- PROCESS DATA ---
        try:
            csv_content = io.StringIO(response.content.decode('utf-8'))
            df = pd.read_csv(csv_content)

            if df.empty or len(df) == 0:
                print("No more records found. Download complete.")
                break

            # Write to disk IMMEDIATELY
            # mode='a' appends to the file
            # header=need_header ensures we don't write the column names in the middle of the file
            df.to_csv(OUTPUT_FILE, mode='a', index=False, header=need_header)
            
            # After the first write, we never want headers again
            need_header = False 

            print(f"Saved {len(df)} rows (Offset: {offset})")

            if len(df) < CHUNK_SIZE:
                print("Last partial chunk received. Done.")
                break

            offset += CHUNK_SIZE
            time.sleep(0.5) # Short pause

        except Exception as e:
            print(f"Error processing CSV data: {e}")
            break

if __name__ == "__main__":
    fetch_data()