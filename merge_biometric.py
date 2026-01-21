import pandas as pd
import os

# --- CONFIGURATION ---
# Using r"" to handle Windows paths safely
file_paths = [
    r"C:\Users\Raj\Downloads\api_data_aadhar_biometric\api_data_aadhar_biometric_0_500000.csv",
    r"C:\Users\Raj\Downloads\api_data_aadhar_biometric\api_data_aadhar_biometric_500000_1000000.csv",
    r"C:\Users\Raj\Downloads\api_data_aadhar_biometric\api_data_aadhar_biometric_1000000_1500000.csv",
    r"C:\Users\Raj\Downloads\api_data_aadhar_biometric\api_data_aadhar_biometric_1500000_1861108.csv"
]

OUTPUT_FILE = "Final_Biometric_Data_Combined.csv"

# --- EXECUTION ---
dfs = []

print("Reading files...")

for file in file_paths:
    if os.path.exists(file):
        try:
            # low_memory=False is crucial for large files to guess column types correctly
            df = pd.read_csv(file, low_memory=False)
            dfs.append(df)
            print(f"  [+] Loaded: {os.path.basename(file)} ({len(df):,} rows)")
        except Exception as e:
            print(f"  [!] Error reading {file}: {e}")
    else:
        print(f"  [!] File not found: {file}")

if dfs:
    print("-" * 40)
    print("Merging dataframes...")
    combined_df = pd.concat(dfs, ignore_index=True)
    
    total_rows = len(combined_df)
    print(f"Combined Total Rows: {total_rows:,}")

    # Optional: Remove exact duplicates if any exist across files
    # combined_df.drop_duplicates(inplace=True)
    # print(f"Rows after dedup: {len(combined_df):,}")

    print(f"Saving to {OUTPUT_FILE}...")
    combined_df.to_csv(OUTPUT_FILE, index=False)
    print("SUCCESS! File is ready.")
else:
    print("No data loaded. Please check the file paths.")