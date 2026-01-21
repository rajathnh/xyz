import pandas as pd

# 1. Load the Official Pincode Directory
print("Loading Pincode Directory...")
df = pd.read_csv("official_pincode_directory.csv", low_memory=False)

# 2. Fix Latitude/Longitude format
# Sometimes 'NA' or empty strings are read as text. Force them to numeric.
df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')

# 3. The Sorting Trick
# We sort by Latitude (Descending). 
# Why? Because NaN (Empty) values usually go to the bottom.
# This ensures that when we delete duplicates, we keep the row that HAS valid GPS data.
df_sorted = df.sort_values(by=['Latitude', 'Longitude'], ascending=False)

# 4. Deduplicate
# subset=['Pincode'] -> Look for duplicate Pincodes
# keep='first' -> Keep the top one (which we ensured has GPS data), delete the rest
df_unique = df_sorted.drop_duplicates(subset=['Pincode'], keep='first')

# 5. Select only the columns you need for the merge
# We don't need 'officename' (Bareguda/Mosam) anymore, just the State/District mappings
final_master = df_unique[['Pincode', 'State', 'District', 'Latitude', 'Longitude']]

print(f"Original Rows: {len(df)}")
print(f"Unique Pincodes: {len(final_master)}")
print(f"Removed {len(df) - len(final_master)} duplicate rows.")

# 6. Save the Safe File
final_master.to_csv("pincode_master_unique.csv", index=False)
print("Saved to 'pincode_master_unique.csv'. Use THIS file for your Aadhaar merge.")