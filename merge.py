import pandas as pd
import os

# --- CONFIGURATION ---
INPUT_FILE = "aadhaar_monthly_data_full.csv"     # The file you just cleaned
PINCODE_FILE = "pincode_master_unique.csv"     # The 19k Lat/Long file
OUTPUT_FILE = "Final_Monthly_Data.csv"      # The Analysis-Ready file

print(f"Loading {INPUT_FILE}...")
df = pd.read_csv(INPUT_FILE, low_memory=False)

# 1. Clean Pincode Format
# Ensure it is a string and remove decimals "500001.0" -> "500001"
df['Pincode'] = df['Pincode'].astype(str).str.replace(r'\.0$', '', regex=True)

# 2. Load Pincode Master
if os.path.exists(PINCODE_FILE):
    print("Merging with Pincode Master...")
    pin_master = pd.read_csv(PINCODE_FILE, dtype={'Pincode': str})
    
    # Merge (Left Join)
    df = df.merge(pin_master, on='Pincode', how='left')
    
    # 3. FIX STATE NAMES (The Magic Step)
    # If we found a match in the Master file (State_y), use it.
    # This automatically converts "West Bengli" -> "West Bengal"
    df['State'] = df['State_y'].fillna(df['State_x'])
    df['District'] = df['District_y'].fillna(df['District_x'])
    
    # Drop the dirty columns
    df.drop(columns=['State_x', 'District_x', 'State_y', 'District_y'], inplace=True)
else:
    print("⚠️ Pincode Master not found! skipping map fix.")

# 4. Final Formatting
print("Standardizing text...")
df['State'] = df['State'].str.title().str.strip()
df['District'] = df['District'].str.title().str.strip()

# 5. Save
print(f"Saving {len(df):,} rows to {OUTPUT_FILE}...")
df.to_csv(OUTPUT_FILE, index=False)
print("DONE! You are ready for the hackathon.")