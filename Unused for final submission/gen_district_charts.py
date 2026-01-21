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
OUTPUT_FOLDER = "District_Accessibility_Charts_Vertical"

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# --- 1. LOAD AND PREPARE DATA ---
print("Loading and preparing data...")
all_dfs = [pd.read_csv(f, low_memory=False) for f in FILES_TO_MERGE if os.path.exists(f)]
full_df = pd.concat(all_dfs, ignore_index=True)
full_df.columns = full_df.columns.str.lower()
full_df['date'] = pd.to_datetime(full_df['date'], dayfirst=True, errors='coerce')
full_df = full_df.dropna(subset=['date'])
metric_cols = [c for c in ['age_0_5', 'age_5_17', 'age_18_greater', 'bio_age_5_17', 'bio_age_17_', 'bio_age_17+', 'demo_age_5_17', 'demo_age_17_', 'demo_age_17+'] if c in full_df.columns]
full_df['total_events'] = full_df[metric_cols].sum(axis=1)

# --- 2. CALCULATE DISTRICT-LEVEL SCORES ---
print("Calculating scores for all districts...")
full_df['day_name'] = full_df['date'].dt.day_name()
district_day_activity = full_df.groupby(['state', 'district', 'day_name'])['total_events'].sum().reset_index()
pivot_df = district_day_activity.pivot_table(index=['state', 'district'], columns='day_name', values='total_events').fillna(0)
pivot_df['Total_Weekly_Events'] = pivot_df.sum(axis=1)
if 'Sunday' in pivot_df.columns:
    pivot_df['Sunday_Score_%'] = (pivot_df['Sunday'] / pivot_df['Total_Weekly_Events']) * 100
else:
    pivot_df['Sunday_Score_%'] = 0

def classify_accessibility_v2(score):
    if score > 14: return "EXCELLENT (> Avg Day)"
    elif score > 10: return "GOOD"
    elif score > 5: return "AVERAGE"
    else: return "POOR (< 5%)"
pivot_df['Accessibility_Grade'] = pivot_df['Sunday_Score_%'].apply(classify_accessibility_v2)

# --- 3. THE VERTICAL CHART FACTORY ---
states = pivot_df.index.get_level_values('state').unique()

print(f"Generating VERTICAL charts for {len(states)} states...")
sns.set_style("whitegrid")
palette = {'EXCELLENT (> Avg Day)': '#008272', 'GOOD': '#2ECC71', 'AVERAGE': '#F1C40F', 'POOR (< 5%)': '#C0392B'}

for state in states:
    try:
        state_data = pivot_df.loc[state]
        state_data = state_data.sort_values(by='Sunday_Score_%', ascending=False)
        
        # --- DYNAMIC SIZING FOR VERTICAL ---
        num_districts = len(state_data)
        # The more districts, the WIDER it needs to be
        fig_width = 8 + (num_districts * 0.3)
        
        plt.figure(figsize=(fig_width, 8)) # Fixed height, dynamic width
        
        # --- SWAPPED AXES ---
        ax = sns.barplot(
            data=state_data.reset_index(),
            x='district',           # Districts on X-axis
            y='Sunday_Score_%',     # Score on Y-axis
            hue='Accessibility_Grade',
            palette=palette,
            dodge=False
        )
        
        # Add the average line (now horizontal)
        plt.axhline(y=14.28, color='red', linestyle='--', label='Theoretical Average (1/7)')
        
        # ROTATE LABELS
        plt.xticks(rotation=90)
        
        plt.title(f'"Sunday Service" Score for Districts in {state}', fontsize=16, fontweight='bold')
        plt.ylabel('Percentage of Activity on Sunday (%)', fontsize=12)
        plt.xlabel('District', fontsize=12)
        plt.legend()
        plt.tight_layout()
        
        clean_name = str(state).replace(" ", "_").replace("&", "and")
        filename = f"{OUTPUT_FOLDER}/{clean_name}_District_Scores_Vertical.png"
        plt.savefig(filename, dpi=150)
        plt.close()
        
        print(f"  Saved chart for {state}")

    except Exception as e:
        print(f"  Could not plot {state}. Error: {e}")

print("-" * 40)
print(f"All charts saved to the '{OUTPUT_FOLDER}' folder.")