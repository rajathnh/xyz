import requests
import pandas as pd
import io
import time
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse

# ==========================================
# CONFIGURATION
# ==========================================
API_KEY = "579b464db66ec23bdd000001da53d4ac855940de49990e71b0c4c82f"  # <--- PASTE YOUR KEY HERE
RESOURCE_ID = "65454dab-1517-40a3-ac1d-47d4dfe6891c"
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

OUTPUT_FILENAME = "aadhaar_biometric_complete.csv"
CHUNK_SIZE = 1000
MAX_WORKERS = 5  # Safe limit to avoid IP bans

# The "Total Chaos" List
# Includes Official Names, Old Names, Typos, Cities, and Data Entry Errors found in your screenshots.
STATES = [
    # --- The Big Ones (Standard) ---
     "Jammu & Kashmir", "Uttarakhand",
    "Himachal Pradesh", "Tripura", "Meghalaya", "Manipur", "Nagaland",
    "Goa", "Arunachal Pradesh", "Mizoram", "Sikkim", "Chandigarh",
    "Puducherry", "Ladakh", "Dadra and Nagar Haveli and Daman and Diu",
    "Andaman & Nicobar Islands", "Lakshadweep",

    # --- Variations, Typos & Old Names ---
    "Orissa", "Pondicherry", "Uttaranchal", "Telengana", 
    "Chattisgarh", "Jammu and Kashmir", "Andaman and Nicobar Islands",
    "Dadra & Nagar Haveli", "Daman & Diu", "Daman and Diu",
    "Delhi", "New Delhi", "Laccadive", "Mysore",
    "West Bangal", "WEST BENGAL", "Westbengal", "West Bengli", 
    "west Bengal", "WESTBENGAL", "ODISHA", "andhra pradesh", "Tamilnadu",

    # --- Cities & Garbage Data (From Screenshots) ---
    "Pune City", "Nagpur", "GURGAON", "Jaipur", "Madanapalle",
    "BALANAGAR", "Greater Kailash 2", "Puttenahalli", "Darbhanga",
    "PUTHUR", "Raja Annamalai Puram", "100000"
]

# Thread-safe lock for writing to file
file_lock = threading.Lock()
# Global flag to track if we have initialized the file (written headers)
file_initialized = True

def fetch_state_chunk(state, offset):
    """
    Fetches a single chunk for a specific state/filter.
    """
    # URL Encode the state (Critical for 'Jammu & Kashmir' or spaces)
    state_encoded = urllib.parse.quote(state)
    
    # Construct URL with filter
    url = f"{BASE_URL}?api-key={API_KEY}&format=csv&limit={CHUNK_SIZE}&offset={offset}&filters[state]={state_encoded}"
    
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=20)
            
            if response.status_code == 200:
                # API returns empty string sometimes if no data
                if not response.content.strip():
                    return offset, None, "Empty"
                
                # Parse CSV
                csv_content = io.StringIO(response.content.decode('utf-8'))
                try:
                    df = pd.read_csv(csv_content)
                    return offset, df, None
                except pd.errors.EmptyDataError:
                    return offset, None, "Empty"
                    
            elif response.status_code in [404, 400]:
                return offset, None, "End" # Official end of data
            else:
                time.sleep(1) # Server error, wait briefly
        except Exception:
            time.sleep(1)
            
    return offset, None, "Failed"

def process_state(state):
    global file_initialized
    print(f"\n>>> Querying: {state}")
    
    offset = 0
    total_state_rows = 0
    
    while True:
        # We spawn 5 workers to get offsets: 0, 1000, 2000, 3000, 4000
        # Then next loop: 5000, 6000...
        offsets_batch = [offset + (i * CHUNK_SIZE) for i in range(MAX_WORKERS)]
        
        batch_dfs = []
        stop_state_signal = False
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_offset = {executor.submit(fetch_state_chunk, state, o): o for o in offsets_batch}
            
            for future in as_completed(future_to_offset):
                o = future_to_offset[future]
                res_o, df, err = future.result()
                
                if df is not None and not df.empty:
                    batch_dfs.append(df)
                    if len(df) < CHUNK_SIZE:
                        stop_state_signal = True
                elif err == "End" or (df is not None and df.empty):
                    # We hit the end of data for this state
                    stop_state_signal = True

        # Write Batch to Disk
        if batch_dfs:
            with file_lock:
                # Concatenate all chunks in this batch
                combined_df = pd.concat(batch_dfs, ignore_index=True)
                
                # Determine mode: 'w' if new file, 'a' if appending
                mode = 'a' if file_initialized else 'w'
                header = not file_initialized
                
                combined_df.to_csv(OUTPUT_FILENAME, mode=mode, index=False, header=header)
                
                # Mark file as initialized so we don't overwrite or write headers again
                file_initialized = True
                
                count = len(combined_df)
                total_state_rows += count
                print(f"   Saved {count} rows for {state} (Total: {total_state_rows})")

        if stop_state_signal:
            print(f"   Finished {state}. Total rows: {total_state_rows}")
            break
            
        offset += (MAX_WORKERS * CHUNK_SIZE)
        time.sleep(0.5) # Be polite

def main():
    global file_initialized
    
    # 1. Cleanup old file to ensure we start fresh
    if os.path.exists(OUTPUT_FILENAME):
        print(f"Deleting old file: {OUTPUT_FILENAME}")
        os.remove(OUTPUT_FILENAME)
        file_initialized = False

    print(f"Starting Accelerated Download to: {OUTPUT_FILENAME}")
    print("-" * 50)
    
    # 2. Iterate through the "Chaos List"
    for state in STATES:
        process_state(state)
        time.sleep(1) # Pause between states
        
    print("-" * 50)
    print("ALL STATES COMPLETED.")
    print(f"Data saved to {OUTPUT_FILENAME}")

if __name__ == "__main__":
    main()