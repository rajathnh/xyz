import pandas as pd
import os

# --- CONFIGURATION ---
# Using r"" (raw string) to handle Windows backslashes automatically
file_paths = [
    r"C:\Users\Raj\Downloads\api_data_aadhar_enrolment\api_data_aadhar_enrolment_0_500000.csv",
    r"C:\Users\Raj\Downloads\api_data_aadhar_enrolment\api_data_aadhar_enrolment_500000_1000000.csv",
    r"C:\Users\Raj\Downloads\api_data_aadhar_enrolment\api_data_aadhar_enrolment_1000000_1006029.csv"
]

OUTPUT_FILE = "Final_Monthly_Data_Combined.csv"

# --- EXECUTION ---
dfs = []
total_rows = 0

print("Reading files...")

for file in file_paths:
    try:
        # Check if file exists first
        if os.path.exists(file):
            # low_memory=False prevents warnings about mixed types (e.g. if column 5 has text and numbers)
            df = pd.read_csv(file, low_memory=False)
            dfs.append(df)
            
            count = len(df)
            total_rows += count
            print(f"  [+] Loaded: {os.path.basename(file)} ({count:,} rows)")
        else:
            print(f"  [!] File not found: {file}")
            
    except Exception as e:
        print(f"  [!] Error reading {file}: {e}")

if dfs:
    print("-" * 40)
    print("Merging dataframes...")
    combined_df = pd.concat(dfs, ignore_index=True)
    
    print(f"Combined Total Rows: {len(combined_df):,}")
    
    # Optional: Deduplicate just in case
    # combined_df.drop_duplicates(inplace=True)
    # print(f"After Deduplication: {len(combined_df):,}")

    print(f"Saving to {OUTPUT_FILE}...")
    combined_df.to_csv(OUTPUT_FILE, index=False)
    print("SUCCESS! File is ready.")
else:
    print("No data was loaded. Check your file paths.")