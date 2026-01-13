import pandas as pd

# --- CONFIGURATION ---
FILE_TO_CHECK = "Final_Submission_Data.csv" 

print(f"Loading {FILE_TO_CHECK}...")
df = pd.read_csv(FILE_TO_CHECK, low_memory=False)

print("-" * 40)
print(f"TOTAL ROWS: {len(df):,}")
print("-" * 40)

# TEST 1: DID THE "WEST BENGLI" FIX WORK?
# We check if any of the old garbage names still exist in the 'State' column.
garbage_list = ["West Bengli", "West Bangal", "GURGAON", "100000", "Telengana", "Orissa"]
print("TEST 1: GARBAGE NAME CHECK")
errors_found = 0
for bad_name in garbage_list:
    # Check for exact match or partial match
    count = df[df['State'].astype(str).str.contains(bad_name, case=False, na=False)].shape[0]
    if count > 0:
        print(f"  ❌ FAILED: Found {count} rows with '{bad_name}'")
        errors_found += 1
    else:
        print(f"  ✅ PASSED: No trace of '{bad_name}'")

if errors_found == 0:
    print("  >>> VERDICT: Text Cleaning was SUCCESSFUL.")
else:
    print("  >>> VERDICT: Some garbage remains. Check your merge logic.")

print("-" * 40)

# TEST 2: GEOLOCATION SUCCESS RATE
# How many rows successfully got a Latitude/Longitude?
total = len(df)
missing_geo = df['Latitude'].isna().sum()
success_geo = total - missing_geo
percent = (success_geo / total) * 100

print("TEST 2: GEOLOCATION COVERAGE")
print(f"  Rows with Lat/Long: {success_geo:,} ({percent:.2f}%)")
print(f"  Rows missing Loc:   {missing_geo:,}")

if percent > 85:
    print("  >>> VERDICT: EXCELLENT coverage.")
elif percent > 50:
    print("  >>> VERDICT: GOOD. Some missing pincodes are normal.")
else:
    print("  >>> VERDICT: WARNING. Low match rate. Check Pincode format (strings vs numbers).")

print("-" * 40)

# TEST 3: LOGIC CHECK (TOP STATES)
# Does the data look real? Uttar Pradesh should have more records than Goa.
print("TEST 3: TOP 5 STATES BY VOLUME")
print(df['State'].value_counts().head(5))

# TEST 4: PEEK AT DATA
print("-" * 40)
print("TEST 4: RANDOM SAMPLE (5 ROWS)")
# Random_state ensures we see the same random rows every time we run this
print(df.sample(5, random_state=42)[['Date', 'State', 'District', 'Pincode', 'Latitude']].to_string())
print("-" * 40)