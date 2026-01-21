import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- CONFIGURATION ---
INPUT_FILE = "Cleaned_Final_Monthly_Data_Combined.csv"
OUTPUT_FOLDER = "Digital_Exclusion_Charts"

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# --- 1. LOAD AND PREPARE DATA ---
print(f"Loading {INPUT_FILE}...")
df = pd.read_csv(INPUT_FILE, low_memory=False)
df.columns = df.columns.str.lower()
age_cols = ['age_0_5', 'age_5_17', 'age_18_greater']
for col in age_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# --- 2. CALCULATE EXCLUSION SCORES (Same as before) ---
print("Calculating Digital Exclusion Score for all districts...")
district_totals = df.groupby(['state', 'district'])[age_cols].sum().reset_index()
district_totals['Total_Enrolments'] = district_totals[age_cols].sum(axis=1)
district_totals['Adult_Enrolment_Ratio'] = district_totals['age_18_greater'] / (district_totals['Total_Enrolments'] + 1)

def classify_exclusion(ratio):
    if ratio > 0.30: return "CRITICAL"
    elif ratio > 0.15: return "HIGH"
    elif ratio > 0.05: return "MODERATE"
    else: return "NORMAL"
district_totals['Exclusion_Level'] = district_totals['Adult_Enrolment_Ratio'].apply(classify_exclusion)

# --- 3. THE VERTICAL CHART FACTORY ---
states = district_totals['state'].unique()

print(f"Generating charts for {len(states)} states...")
sns.set_style("whitegrid")
# Define a color palette for the exclusion levels
palette = {'CRITICAL': '#8B0000', 'HIGH': '#E74C3C', 'MODERATE': '#F39C12', 'NORMAL': '#2ECC71'}

for state in states:
    try:
        # Filter data for the current state
        state_data = district_totals[district_totals['state'] == state]
        
        # Sort districts by score for a clean ranking
        state_data = state_data.sort_values(by='Adult_Enrolment_Ratio', ascending=False)
        
        # Skip states with no significant activity
        if state_data['Total_Enrolments'].sum() < 100:
            continue
            
        # --- DYNAMIC SIZING ---
        num_districts = len(state_data)
        # Wider chart for more districts
        fig_width = 8 + (num_districts * 0.3)
        
        plt.figure(figsize=(fig_width, 8))
        
        # --- VERTICAL BAR PLOT ---
        ax = sns.barplot(
            data=state_data,
            x='district',           # Districts on X-axis
            y='Adult_Enrolment_Ratio', # Score on Y-axis
            hue='Exclusion_Level',
            palette=palette,
            dodge=False
        )
        
        # Convert Y-axis to percentage
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y)))
        
        # ROTATE LABELS for readability
        plt.xticks(rotation=90)
        
        plt.title(f'Digital Exclusion Hotspots in {state}', fontsize=16, fontweight='bold')
        plt.ylabel('% of New Enrolments that are Adults (18+)', fontsize=12)
        plt.xlabel('District', fontsize=12)
        plt.legend(title='Exclusion Level')
        plt.tight_layout()
        
        clean_name = str(state).replace(" ", "_").replace("&", "and")
        filename = f"{OUTPUT_FOLDER}/{clean_name}_Exclusion_Scores_Vertical.png"
        plt.savefig(filename, dpi=150)
        plt.close()
        
        print(f"  Saved chart for {state}")

    except Exception as e:
        print(f"  Could not plot {state}. Error: {e}")

print("-" * 40)
print(f"All charts saved to the '{OUTPUT_FOLDER}' folder.")