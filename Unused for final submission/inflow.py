import pandas as pd

# --- CONFIGURATION ---
INPUT_FILE = "Final_Submission_Data.csv"

print(f"Loading {INPUT_FILE}...")
df = pd.read_csv(INPUT_FILE, dtype={'Pincode': str}, low_memory=False)

# 1. Setup Column
adult_col = [c for c in df.columns if '17' in c and '5' not in c][0]
df[adult_col] = pd.to_numeric(df[adult_col], errors='coerce').fillna(0)

# 2. Filter for Valid GPS
df = df.dropna(subset=['Latitude', 'Longitude'])

# 3. CREATE SMART GRID (Round to 2 decimals = ~1.1km grid)
df['Lat_Grid'] = df['Latitude'].round(2)
df['Long_Grid'] = df['Longitude'].round(2)

# 4. AGGREGATE
# We keep District/State just for labeling the zone
grid_view = df.groupby(['Lat_Grid', 'Long_Grid']).agg({
    adult_col: 'sum',
    'District': 'first',
    'State': 'first'
}).reset_index()

grid_view.rename(columns={adult_col: 'Inflow_Pressure'}, inplace=True)

# 5. SORT
top_zones = grid_view.sort_values(by='Inflow_Pressure', ascending=False).head(20)

print("-" * 60)
print("TOP 20 HIGH-DENSITY ZONES (1km x 1km Blocks)")
print("-" * 60)
print(top_zones[['State', 'District', 'Lat_Grid', 'Long_Grid', 'Inflow_Pressure']].to_string(index=False))

# 6. EXPORT
grid_view.to_csv("Grid_Hotspots_Final.csv", index=False)