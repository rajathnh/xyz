import pandas as pd
import os

# --- CONFIGURATION ---
# Using r"" (raw strings) to handle Windows backslashes
file_paths = [
    r"C:\Users\Raj\Downloads\api_data_aadhar_demographic\api_data_aadhar_demographic_0_500000.csv",
    r"C:\Users\Raj\Downloads\api_data_aadhar_demographic\api_data_aadhar_demographic_500000_1000000.csv",
    r"C:\Users\Raj\Downloads\api_data_aadhar_demographic\api_data_aadhar_demographic_1000000_1500000.csv",
    r"C:\Users\Raj\Downloads\api_data_aadhar_demographic\api_data_aadhar_demographic_1500000_2000000.csv",
    r"C:\Users\Raj\Downloads\api_data_aadhar_demographic\api_data_aadhar_demographic_2000000_2071700.csv"
]

OUTPUT_FILE = "Final_Demographic_Data_Combined.csv"

# --- EXECUTION ---
dfs = []

print(f"Starting merge of {len(file_paths)} files...")

for file in file_paths:
    if os.path.exists(file):
        try:
            # low_memory=False helps pandas handle mixed types in large files without crashing
            df = pd.read_csv(file, low_memory=False)
            dfs.append(df)
            print(f"  [+] Loaded: {os.path.basename(file)} ({len(df):,} rows)")
        except Exception as e:
            print(f"  [!] Error reading {file}: {e}")
    else:
        print(f"  [!] File not found: {file}")

if dfs:
    print("-" * 40)
    print("Concatenating dataframes...")
    combined_df = pd.concat(dfs, ignore_index=True)
    
    total_rows = len(combined_df)
    print(f"Total Combined Rows: {total_rows:,}")

    print(f"Saving to {OUTPUT_FILE}...")
    combined_df.to_csv(OUTPUT_FILE, index=False)
    print("SUCCESS! File is ready.")
else:
    print("No data loaded. Check your file paths.")