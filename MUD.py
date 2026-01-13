import requests
import pandas as pd
import io
import time
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CONFIGURATION ---
# PASTE YOUR REAL KEY HERE (The one you generated earlier)
API_KEY = "579b464db66ec23bdd000001da53d4ac855940de49990e71b0c4c82f" 

# NEW RESOURCE ID for "Aadhaar Biometric Monthly Update Data"
RESOURCE_ID = "65454dab-1517-40a3-ac1d-47d4dfe6891c"
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

OUTPUT_FILE = "aadhaar_biometric_5M_rows.csv"
CHUNK_SIZE = 1000
MAX_WORKERS = 5   # Keep at 5 to avoid IP ban on 5.5M rows
START_OFFSET = 5000000  # Start fresh

file_lock = threading.Lock()

def fetch_chunk(offset):
    params = {
        'api-key': API_KEY,
        'format': 'csv',
        'limit': CHUNK_SIZE,
        'offset': offset
    }
    for attempt in range(3): # Retry logic
        try:
            response = requests.get(BASE_URL, params=params, timeout=20)
            if response.status_code == 200:
                # Handle empty CSV response
                if not response.content.strip(): 
                    return offset, None, "Empty Content"
                
                csv_content = io.StringIO(response.content.decode('utf-8'))
                df = pd.read_csv(csv_content)
                return offset, df, None
            elif response.status_code in [404, 400]:
                return offset, None, "End of Data"
            else:
                time.sleep(2)
        except Exception:
            time.sleep(2)
    return offset, None, "Failed"

def main():
    offset = START_OFFSET
    # Check if file exists to handle headers
    if offset == 0 and os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE) # Safety: Delete old file if starting from 0
    
    write_header = True
    BATCH_SIZE = 50 # Process 50k rows at a time
    
    print(f"Starting download of ~5.5 Million rows...")
    
    while True:
        offsets = [offset + (i * CHUNK_SIZE) for i in range(BATCH_SIZE)]
        results = []
        stop = False

        print(f"Fetching offsets: {offsets[0]} to {offsets[-1]}...")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_offset = {executor.submit(fetch_chunk, o): o for o in offsets}

            for future in as_completed(future_to_offset):
                o = future_to_offset[future]
                res_o, df, err = future.result()

                if err == "End of Data" or (df is not None and len(df) == 0):
                    stop = True
                elif df is not None:
                    results.append((res_o, df))
                    if len(df) < CHUNK_SIZE:
                        stop = True

        # Write to disk
        results.sort(key=lambda x: x[0])
        if results:
            with file_lock:
                mode = 'a'
                for _, df in results:
                    df.to_csv(OUTPUT_FILE, mode=mode, index=False, header=write_header)
                    write_header = False 
            print(f"  Saved batch. Current Offset: {offset + (BATCH_SIZE*CHUNK_SIZE)}")

        if stop:
            print("Download Complete.")
            break

        offset += (BATCH_SIZE * CHUNK_SIZE)
        time.sleep(0.5)

if __name__ == "__main__":
    main()