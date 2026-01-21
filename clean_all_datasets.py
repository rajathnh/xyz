import pandas as pd
import os
import requests
import io

# ==========================================
# CONFIGURATION
# ==========================================
FILES_TO_CLEAN = [
    "Final_Biometric_Data_Combined.csv",
    "Final_Demographic_Data_Combined.csv",
    "Final_Monthly_Data_Combined.csv"
]

PINCODE_MASTER_FILE = "pincode_master_unique.csv"

# ==========================================
# 1. GET THE PINCODE MASTER
# ==========================================
def get_pincode_master():
    """
    Loads local master file or downloads one if missing.
    Returns a dataframe with: [Pincode, Official_State, Official_District]
    """
    if os.path.exists(PINCODE_MASTER_FILE):
        print(f"Loading local Pincode Master: {PINCODE_MASTER_FILE}...")
        df = pd.read_csv(PINCODE_MASTER_FILE, dtype=str)
    else:
        print("Pincode Master not found locally. Downloading from GitHub...")
        url = "https://raw.githubusercontent.com/sanand0/pincode/master/data/IN.csv"
        s = requests.get(url).content
        df = pd.read_csv(io.StringIO(s.decode('utf-8')), dtype=str)
        # Rename standard columns
        df.rename(columns={'key': 'Pincode', 'admin_name1': 'State', 'admin_name2': 'District'}, inplace=True)

    # Standardize columns
    # We only keep Pincode, State, District (No Lat/Long as requested)
    df = df[['Pincode', 'State', 'District']]
    
    # Rename to "Official" to avoid collision during merge
    df.columns = ['Pincode', 'Official_State', 'Official_District']
    
    # Deduplicate (One State/District per Pincode)
    df.drop_duplicates(subset=['Pincode'], inplace=True)
    return df

# ==========================================
# 2. THE CLEANING FUNCTION
# ==========================================
def clean_file(filename, master_df):
    if not os.path.exists(filename):
        print(f"Skipping {filename} (File not found)")
        return

    print(f"\nProcessing {filename}...")
    
    # Load raw data
    # low_memory=False is crucial for large files
    df = pd.read_csv(filename, low_memory=False)
    
    # Normalize Pincode Column Name and Type
    # Users file has lowercase 'pincode', Master has 'Pincode'
    # We standardize to 'Pincode'
    col_map = {c: c for c in df.columns}
    for c in df.columns:
        if c.lower() == 'pincode':
            col_map[c] = 'Pincode'
    df.rename(columns=col_map, inplace=True)
    
    # Clean Pincode values (remove decimals, ensure string)
    df['Pincode'] = df['Pincode'].astype(str).str.replace(r'\.0$', '', regex=True)
    
    # MERGE
    print("  Merging with Pincode Master...")
    merged = df.merge(master_df, on='Pincode', how='left')
    
    # IDENTIFY STATE/DISTRICT COLUMNS
    # The raw file might have 'state', 'State', 'district', 'District'
    state_col = next((c for c in df.columns if c.lower() == 'state'), None)
    dist_col = next((c for c in df.columns if c.lower() == 'district'), None)
    
    if state_col and dist_col:
        # REPLACE LOGIC
        # Use Official Name. If NaN (Pincode not found), keep Original Name.
        merged[state_col] = merged['Official_State'].fillna(merged[state_col])
        merged[dist_col] = merged['Official_District'].fillna(merged[dist_col])
        
        # TITLE CASE (Clean formatting)
        merged[state_col] = merged[state_col].astype(str).str.title().str.strip()
        merged[dist_col] = merged[dist_col].astype(str).str.strip().str.title()
        
        print("  State/District names standardized.")
    else:
        print("  WARNING: Could not find 'state' or 'district' columns to clean.")

    # DROP HELPER COLUMNS
    merged.drop(columns=['Official_State', 'Official_District'], inplace=True, errors='ignore')
    
    # SAVE
    output_name = "Cleaned_" + filename
    merged.to_csv(output_name, index=False)
    print(f"  Saved to: {output_name}")

# ==========================================
# EXECUTION
# ==========================================
if __name__ == "__main__":
    # 1. Load Master Key
    master_df = get_pincode_master()
    print(f"Master Pincode Database loaded ({len(master_df)} unique codes).")
    
    # 2. Loop through your files
    for f in FILES_TO_CLEAN:
        clean_file(f, master_df)
        
    print("\nAll files cleaned successfully. 🚀")