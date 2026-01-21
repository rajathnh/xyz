import pandas as pd

# --- CONFIGURATION ---
INPUT_FILE = "aadhaar_biometric_5M_rows.csv"  # The messy file with 6M rows
OUTPUT_FILE = "aadhaar_biometric_clean.csv"    # The new clean file

print(f"Loading {INPUT_FILE}... (This may take a minute)")
# low_memory=False ensures it reads messy columns correctly
df = pd.read_csv(INPUT_FILE, low_memory=False)

original_count = len(df)
print(f"Original Row Count: {original_count:,}")

# THE CLEANING STEP
print("Removing duplicate rows...")
df.drop_duplicates(inplace=True)

new_count = len(df)
removed_count = original_count - new_count

print("-" * 30)
print(f"Clean Row Count:    {new_count:,}")
print(f"Duplicates Removed: {removed_count:,}")
print("-" * 30)

print(f"Saving to {OUTPUT_FILE}...")
df.to_csv(OUTPUT_FILE, index=False)
print("Done! Use the new file for your analysis.")