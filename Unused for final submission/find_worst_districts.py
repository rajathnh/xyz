import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- CONFIGURATION ---
FILE_ENROL = "Cleaned_Final_Monthly_Data_Combined.csv"    
FILE_UPDATE = "Cleaned_Final_Biometric_Data_Combined.csv" 
OUTPUT_FOLDER = "Top_20_District_Fraud_Graphs"

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

# 2. AGGREGATE BY DISTRICT (The Granular View)
print("Aggregating by District...")
grp_enrol = df_enrol.groupby(['state', 'district', pd.Grouper(key='date', freq='W-MON')])['age_0_5'].sum().reset_index()
grp_update = df_update.groupby(['state', 'district', pd.Grouper(key='date', freq='W-MON')])[adult_bio_col].sum().reset_index()

merged = pd.merge(grp_enrol, grp_update, on=['state', 'district', 'date'], how='inner')
merged.rename(columns={'age_0_5': 'New_Kids', adult_bio_col: 'Adult_Updates'}, inplace=True)

# 3. RANKING LOGIC (Find the Worst Offenders)
print("Ranking Districts by Fraud Severity...")
district_scores = []

unique_districts = merged[['state', 'district']].drop_duplicates()

for _, row in unique_districts.iterrows():
    state = row['state']
    district = row['district']
    
    dist_df = merged[(merged['state'] == state) & (merged['district'] == district)]
    
    # Skip tiny districts (Noise filter)
    if dist_df['New_Kids'].sum() < 50: continue
    
    # Calculate Logic
    ratio = (dist_df['New_Kids'] / dist_df['Adult_Updates'].replace(0, 1)).median()
    safety_buffer = dist_df['New_Kids'].std() * 0.5
    threshold = (dist_df['Adult_Updates'] * ratio) + safety_buffer
    min_floor = dist_df['New_Kids'].quantile(0.1)
    threshold = threshold.clip(lower=min_floor)
    
    # Check for anomalies
    anomalies = dist_df[dist_df['New_Kids'] > threshold]
    
    if not anomalies.empty:
        # Severity Score = Total number of extra kids found in fraud spikes
        # This prioritizes BIG scams over tiny statistical blips
        extra_kids = (anomalies['New_Kids'] - threshold.loc[anomalies.index]).sum()
        district_scores.append({
            'state': state,
            'district': district,
            'fraud_severity': extra_kids
        })

# Create DataFrame of scores and sort
score_df = pd.DataFrame(district_scores)
score_df = score_df.sort_values(by='fraud_severity', ascending=False)

# Get Top 20
top_20 = score_df.head(20)
print("-" * 40)
print("TOP 5 SUSPICIOUS DISTRICTS:")
print(top_20[['state', 'district', 'fraud_severity']].head(5).to_string(index=False))
print("-" * 40)

# 4. GENERATE GRAPHS FOR ONLY TOP 20
print("Generating Graphs for Top 20 Targets...")

sns.set_style("white")

for _, row in top_20.iterrows():
    state = row['state']
    district = row['district']
    
    try:
        dist_df = merged[(merged['state'] == state) & (merged['district'] == district)].copy()
        
        # Recalculate Threshold for plotting
        ratio = (dist_df['New_Kids'] / dist_df['Adult_Updates'].replace(0, 1)).median()
        safety_buffer = dist_df['New_Kids'].std() * 0.5
        dist_df['Safe_Limit'] = (dist_df['Adult_Updates'] * ratio) + safety_buffer
        min_floor = dist_df['New_Kids'].quantile(0.1)
        dist_df['Safe_Limit'] = dist_df['Safe_Limit'].clip(lower=min_floor)

        # Plotting
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Axis 1: Kids & Threshold
        sns.lineplot(data=dist_df, x='date', y='Safe_Limit', color='#27AE60', linewidth=2, linestyle='--', label='Camp Threshold', ax=ax1)
        sns.lineplot(data=dist_df, x='date', y='New_Kids', color='#C0392B', linewidth=2.5, label='Actual Kids', ax=ax1)

        # Axis 2: Adults
        ax2 = ax1.twinx()
        max_adults = dist_df['Adult_Updates'].max()
        ax2.set_ylim(0, max_adults * 1.5)
        ax2.fill_between(dist_df['date'], dist_df['Adult_Updates'], color='grey', alpha=0.15, label='Adult Activity')
        
        # Highlight Fraud
        anomalies = dist_df[dist_df['New_Kids'] > dist_df['Safe_Limit']]
        real_anomalies = anomalies[anomalies['New_Kids'] > (anomalies['Safe_Limit'] * 1.1)]
        
        if not real_anomalies.empty:
            ax1.scatter(real_anomalies['date'], real_anomalies['New_Kids'], color='red', s=100, zorder=10, edgecolors='black')
            
            top_spike = real_anomalies.loc[real_anomalies['New_Kids'].idxmax()]
            ax1.annotate('SUSPICIOUS', 
                         xy=(top_spike['date'], top_spike['New_Kids']),
                         xytext=(top_spike['date'], top_spike['New_Kids'] + (safety_buffer * 2)),
                         arrowprops=dict(facecolor='black', shrink=0.05),
                         horizontalalignment='center', color='#C0392B', fontweight='bold')

        plt.title(f"Target: {district}, {state}\n(High Severity Anomaly Detected)", fontsize=16, fontweight='bold')
        ax1.set_ylabel("Child Enrolments", color='#C0392B')
        ax2.set_ylabel("Adult Updates", color='grey')
        ax2.grid(False)
        
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper left')
        
        plt.tight_layout()
        clean_name = f"{state}_{district}".replace(" ", "_")
        plt.savefig(f"{OUTPUT_FOLDER}/{clean_name}_Fraud.png", dpi=150)
        plt.close()
        print(f"  Generated: {district}")

    except Exception as e:
        print(f"  Error {district}: {e}")

print("Done. Check the folder for the Hit List.")