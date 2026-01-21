import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- CONFIGURATION ---
FILE_ENROL = "Cleaned_Final_Monthly_Data_Combined.csv"    
FILE_UPDATE = "Cleaned_Final_Biometric_Data_Combined.csv" 
OUTPUT_FOLDER = "Final_Fraud_Detection_Graphs"

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# 1. LOAD DATA
print("Loading Data...")
df_enrol = pd.read_csv(FILE_ENROL, dtype={'Pincode': str}, low_memory=False)
df_update = pd.read_csv(FILE_UPDATE, dtype={'Pincode': str}, low_memory=False)

df_enrol.columns = df_enrol.columns.str.lower()
df_update.columns = df_update.columns.str.lower()

adult_bio_col = [c for c in df_update.columns if '17' in c and '5' not in c][0]

for df in [df_enrol, df_update]:
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    
df_enrol = df_enrol.dropna(subset=['date'])
df_update = df_update.dropna(subset=['date'])

# 2. AGGREGATE
print("Aggregating...")
grp_enrol = df_enrol.groupby(['state', pd.Grouper(key='date', freq='W-MON')])['age_0_5'].sum().reset_index()
grp_update = df_update.groupby(['state', pd.Grouper(key='date', freq='W-MON')])[adult_bio_col].sum().reset_index()

merged = pd.merge(grp_enrol, grp_update, on=['state', 'date'], how='inner')
merged.rename(columns={'age_0_5': 'New_Kids', adult_bio_col: 'Adult_Updates'}, inplace=True)

# 3. GENERATE GRAPHS
states = merged['state'].unique()
sns.set_style("white") 

print(f"Generating Stricter Graphs...")

for state in states:
    try:
        state_df = merged[merged['state'] == state].copy()
        if state_df['New_Kids'].sum() < 50: continue

        # --- REFINED LOGIC ---
        
        # 1. Calculate the Ratio (Kids per Adult Update)
        # We use the median to find the "Normal" relationship
        ratio = (state_df['New_Kids'] / state_df['Adult_Updates'].replace(0, 1)).median()
        
        # 2. TIGHTER BUFFER (Requested Change)
        # Reduced from 1.5 SD to 0.5 SD. 
        # This brings the Green Line DOWN, closer to the real trend.
        safety_buffer = state_df['New_Kids'].std() * 0.5 
        
        # 3. Calculate Threshold
        # Threshold = (Adults * Ratio) + Small Buffer
        state_df['Safe_Limit'] = (state_df['Adult_Updates'] * ratio) + safety_buffer
        
        # Ensure the line is never below the absolute minimum kid count (sanity check)
        min_floor = state_df['New_Kids'].quantile(0.1) 
        state_df['Safe_Limit'] = state_df['Safe_Limit'].clip(lower=min_floor)

        # --- VISUAL SCALING FIX ---
        
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # AXIS 1 (LEFT): CHILDREN & THRESHOLD
        sns.lineplot(
            data=state_df, x='date', y='Safe_Limit', 
            color='#27AE60', linewidth=2, linestyle='--', label='Camp Threshold (Strict)', ax=ax1
        )
        sns.lineplot(
            data=state_df, x='date', y='New_Kids', 
            color='#C0392B', linewidth=2.5, label='Actual Kids (0-5)', ax=ax1
        )

        # AXIS 2 (RIGHT): ADULTS
        ax2 = ax1.twinx()
        
        # VISUAL HACK: 
        # We want the Grey Mountain to look "Big" in the background.
        # So we set the max of the Right Axis to be just enough to contain the peak,
        # but we align the zeros so they start together.
        max_adults = state_df['Adult_Updates'].max()
        ax2.set_ylim(0, max_adults * 1.2) # Tighten the headroom so mountain looks bigger
            
        ax2.fill_between(state_df['date'], state_df['Adult_Updates'], color='grey', alpha=0.15, label='Adult Updates (Volume)')
        
        # Highlight Fraud
        anomalies = state_df[state_df['New_Kids'] > state_df['Safe_Limit']]
        
        # Only plot anomalies if they are SIGNIFICANT (ignore tiny blips)
        # It must exceed the threshold by at least 10%
        real_anomalies = anomalies[anomalies['New_Kids'] > (anomalies['Safe_Limit'] * 1.1)]
        
        if not real_anomalies.empty:
            ax1.scatter(real_anomalies['date'], real_anomalies['New_Kids'], color='red', s=100, zorder=10, edgecolors='black')
            
            # Annotate top spike
            top_spike = real_anomalies.loc[real_anomalies['New_Kids'].idxmax()]
            ax1.annotate('FRAUD SPIKE', 
                         xy=(top_spike['date'], top_spike['New_Kids']),
                         xytext=(top_spike['date'], top_spike['New_Kids'] + (safety_buffer * 2)),
                         arrowprops=dict(facecolor='black', shrink=0.05),
                         horizontalalignment='center', color='#C0392B', fontweight='bold')

        # Titles & Layout
        plt.title(f"Fraud Detection: {state}\n(Stricter Threshold: 0.5 SD Buffer)", fontsize=16, fontweight='bold')
        ax1.set_ylabel("Child Enrolments", color='#C0392B', fontsize=12)
        ax2.set_ylabel("Adult Updates (Volume)", color='grey', fontsize=12)
        ax2.grid(False)
        
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper left')
        
        plt.tight_layout()
        clean_name = str(state).replace(" ", "_")
        plt.savefig(f"{OUTPUT_FOLDER}/{clean_name}_Strict_Fraud.png", dpi=150)
        plt.close()
        print(f"  Saved: {state}")

    except Exception as e:
        print(f"  Skipped {state}: {e}")

print("Done.")