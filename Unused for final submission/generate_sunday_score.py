import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- CONFIGURATION ---
FILES_TO_MERGE = [
    "Cleaned_Final_Monthly_Data_Combined.csv",
    "Cleaned_Final_Biometric_Data_Combined.csv",
    "Cleaned_Final_Demographic_Data_Combined.csv"
]
OUTPUT_REPORT_FILE = "State_Accessibility_Report_V2.csv"
OUTPUT_CHART_FILE = "Chart_State_Accessibility_V2.png"

# --- 1. LOAD AND MERGE DATA ---
print("Loading and merging all datasets...")
all_dfs = []
for file in FILES_TO_MERGE:
    if os.path.exists(file):
        try:
            df = pd.read_csv(file, low_memory=False)
            all_dfs.append(df)
        except Exception as e:
            print(f"Warning: Could not read {file}. Error: {e}")

if not all_dfs:
    print("CRITICAL ERROR: No data files found. Exiting.")
    exit()

full_df = pd.concat(all_dfs, ignore_index=True)
full_df.columns = full_df.columns.str.lower()
full_df['date'] = pd.to_datetime(full_df['date'], dayfirst=True, errors='coerce')
full_df = full_df.dropna(subset=['date'])

# --- THE FIX: DEFINE 'valid_cols' HERE ---
metric_cols = [
    'age_0_5', 'age_5_17', 'age_18_greater', 
    'bio_age_5_17', 'bio_age_17_', 'bio_age_17+',
    'demo_age_5_17', 'demo_age_17_', 'demo_age_17+'
]
valid_cols = [c for c in metric_cols if c in full_df.columns]
# ---------------------------------------------

full_df['total_events'] = full_df[valid_cols].sum(axis=1)

# --- 2. DAY OF WEEK ANALYSIS ---
print("Analyzing Day of Week activity...")
full_df['day_name'] = full_df['date'].dt.day_name()
state_day_activity = full_df.groupby(['state', 'day_name'])['total_events'].sum().reset_index()
pivot_df = state_day_activity.pivot(index='state', columns='day_name', values='total_events').fillna(0)
pivot_df['Total_Weekly_Events'] = pivot_df.sum(axis=1)
if 'Sunday' in pivot_df.columns:
    pivot_df['Sunday_Score_%'] = (pivot_df['Sunday'] / pivot_df['Total_Weekly_Events']) * 100
else:
    pivot_df['Sunday_Score_%'] = 0

# --- 3. UPDATED CLASSIFICATION LOGIC ---
def classify_accessibility_v2(score):
    if score > 14: return "EXCELLENT (> Avg Day)"
    elif score > 10: return "GOOD"
    elif score > 5: return "AVERAGE"
    else: return "POOR (< 5%)"

pivot_df['Accessibility_Grade'] = pivot_df['Sunday_Score_%'].apply(classify_accessibility_v2)

# --- 4. FINAL REPORT & CHART ---
report = pivot_df.sort_values(by='Sunday_Score_%', ascending=False)
report_final = report[['Sunday_Score_%', 'Accessibility_Grade', 'Total_Weekly_Events']]
report_final.to_csv(OUTPUT_REPORT_FILE)
print(f"Saved report to {OUTPUT_REPORT_FILE}")

# Generate Vertical Chart
print("Generating new chart...")
plt.figure(figsize=(20, 12))
sns.set_style("whitegrid")
palette = {
    'EXCELLENT (> Avg Day)': '#008272', # Dark Emerald/Teal
    'GOOD': '#2ECC71',                 # Bright Jade Green
    'AVERAGE': '#F1C40F',              # Standard Yellow
    'POOR (< 5%)': '#C0392B'           # Standard Red
}
sns.barplot(
    data=report_final.reset_index(),
    x='state',
    y='Sunday_Score_%',
    hue='Accessibility_Grade',
    palette=palette,
    dodge=False
)

# Add the "Average Day" line
plt.axhline(y=14.28, color='red', linestyle='--', label='Theoretical Average (1/7)')
plt.xticks(rotation=90)
plt.title('"Sunday Service" Score: State Accessibility (Rigorous Model)', fontsize=18)
plt.ylabel('Sunday Activity as % of Weekly Total', fontsize=14)
plt.xlabel('State', fontsize=14)
plt.legend()
plt.tight_layout()
plt.savefig(OUTPUT_CHART_FILE, dpi=300)

print(f"SUCCESS! New chart saved to {OUTPUT_CHART_FILE}")