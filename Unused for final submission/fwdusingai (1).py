import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# --- CONFIGURATION ---
FILE_ENROL = "Cleaned_Final_Monthly_Data_Combined.csv"    
FILE_UPDATE = "Cleaned_Final_Biometric_Data_Combined.csv" 
OUTPUT_FOLDER = "National_Top_20_Fraud_Districts"

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# ==========================================
# 1. LOAD & AGGREGATE DATA (National Level)
# ==========================================
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

print("Aggregating by District...")
grp_enrol = df_enrol.groupby(['state', 'district', pd.Grouper(key='date', freq='W-MON')])['age_0_5'].sum().reset_index()
grp_update = df_update.groupby(['state', 'district', pd.Grouper(key='date', freq='W-MON')])[adult_bio_col].sum().reset_index()

merged = pd.merge(grp_enrol, grp_update, on=['state', 'district', 'date'], how='inner')
merged.rename(columns={'age_0_5': 'New_Kids', adult_bio_col: 'Adult_Updates'}, inplace=True)

# ==========================================
# 2. RUN AI MODEL (Global Anomaly Detection)
# ==========================================
print("Training AI Model on National Data...")

# Feature Engineering for AI
# AI needs to compare "Kids" vs "Ratio"
merged['Adult_Updates_Safe'] = merged['Adult_Updates'].replace(0, 1)
merged['Dependency_Ratio'] = merged['New_Kids'] / merged['Adult_Updates_Safe']

features = ['New_Kids', 'Dependency_Ratio']
scaler = StandardScaler()
X_scaled = scaler.fit_transform(merged[features])

# Isolation Forest: We assume 5% of data points might be anomalous/fraudulent
model = IsolationForest(contamination=0.05, random_state=42)
merged['AI_Anomaly_Score'] = model.fit_predict(X_scaled)

# Flag: -1 is Anomaly, 1 is Normal
merged['IS_AI_FRAUD'] = merged['AI_Anomaly_Score'] == -1

# ==========================================
# 3. HYBRID RANKING (Find the Worst Offenders)
# ==========================================
print("Ranking Districts by Hybrid Severity (Rule + AI)...")
district_scores = []

unique_districts = merged[['state', 'district']].drop_duplicates()

for _, row in unique_districts.iterrows():
    state = row['state']
    district = row['district']
    
    dist_df = merged[(merged['state'] == state) & (merged['district'] == district)]
    
    # Noise Filter: Skip districts with negligible activity
    if dist_df['New_Kids'].sum() < 50: continue
    
    # --- RULE BASED THRESHOLD (The Green Line) ---
    ratio = (dist_df['New_Kids'] / dist_df['Adult_Updates_Safe']).median()
    safety_buffer = dist_df['New_Kids'].std() * 0.5
    threshold = (dist_df['Adult_Updates'] * ratio) + safety_buffer
    min_floor = dist_df['New_Kids'].quantile(0.1)
    threshold = threshold.clip(lower=min_floor)
    
    # --- HYBRID DETECTION ---
    # It is ONLY a fraud spike if:
    # 1. It is above the Green Line (Visual Threshold)
    # 2. AND The AI says it's weird (IS_AI_FRAUD == True)
    
    anomalies = dist_df[
        (dist_df['New_Kids'] > threshold) & 
        (dist_df['IS_AI_FRAUD'] == True)
    ]
    
    if not anomalies.empty:
        # Score = Sum of "Extra Kids" in these confirmed spikes
        extra_kids = (anomalies['New_Kids'] - threshold.loc[anomalies.index]).sum()
        district_scores.append({
            'state': state,
            'district': district,
            'fraud_severity': extra_kids,
            'anomaly_count': len(anomalies)
        })

# Sort and Pick Top 20
score_df = pd.DataFrame(district_scores)
if not score_df.empty:
    score_df = score_df.sort_values(by='fraud_severity', ascending=False)
    top_20 = score_df.head(20)

    print("\n" + "="*50)
    print(" NATIONAL FRAUD HIT-LIST (TOP 20 DISTRICTS)")
    print(" Sorted by Severity of AI-Confirmed Spikes")
    print("="*50)
    print(top_20[['state', 'district', 'fraud_severity', 'anomaly_count']].to_string(index=False))
    print("="*50 + "\n")
else:
    print("No significant anomalies found.")
    top_20 = pd.DataFrame()

# ==========================================
# 4. GENERATE EVIDENCE GRAPHS 
# ==========================================
print("Generating Forensic Graphs for Top 20 Targets...")

sns.set_style("white")

# FIX: We use 'enumerate' to force a strict 1-20 count
# 'rank' will now be 1, 2, 3... regardless of the original row number
for rank, (_, row) in enumerate(top_20.iterrows(), 1):
    state = row['state']
    district = row['district']
    
    try:
        dist_df = merged[(merged['state'] == state) & (merged['district'] == district)].copy()
        
        # Recalculate Threshold for plotting
        ratio = (dist_df['New_Kids'] / dist_df['Adult_Updates_Safe']).median()
        safety_buffer = dist_df['New_Kids'].std() * 0.5
        dist_df['Safe_Limit'] = (dist_df['Adult_Updates'] * ratio) + safety_buffer
        min_floor = dist_df['New_Kids'].quantile(0.1)
        dist_df['Safe_Limit'] = dist_df['Safe_Limit'].clip(lower=min_floor)

        # Plotting Setup
        fig, ax1 = plt.subplots(figsize=(14, 7))

        # 1. GREEN LINE (AI Baseline)
        sns.lineplot(data=dist_df, x='date', y='Safe_Limit', color='#27AE60', linewidth=2, linestyle='--', label='AI-Adjusted Safe Limit', ax=ax1)
        
        # 2. RED LINE (Actual Kids)
        sns.lineplot(data=dist_df, x='date', y='New_Kids', color='#C0392B', linewidth=2.5, label='Actual Child Enrolments', ax=ax1)

        # 3. GREY MOUNTAIN (Adult Context)
        ax2 = ax1.twinx()
        max_adults = dist_df['Adult_Updates'].max()
        ax2.set_ylim(0, max_adults * 1.5)
        ax2.fill_between(dist_df['date'], dist_df['Adult_Updates'], color='grey', alpha=0.15, label='Adult Activity (Control)')
        
        # 4. HIGHLIGHT HYBRID ANOMALIES
        hybrid_anomalies = dist_df[
            (dist_df['New_Kids'] > dist_df['Safe_Limit']) & 
            (dist_df['IS_AI_FRAUD'] == True)
        ]
        
        if not hybrid_anomalies.empty:
            ax1.scatter(hybrid_anomalies['date'], hybrid_anomalies['New_Kids'], color='red', s=150, zorder=10, edgecolors='black')
            
            worst_spike = hybrid_anomalies.loc[hybrid_anomalies['New_Kids'].idxmax()]
            
            ax1.annotate('AI CONFIRMED\nFRAUD SPIKE', 
                         xy=(worst_spike['date'], worst_spike['New_Kids']),
                         xytext=(worst_spike['date'], worst_spike['New_Kids'] + (safety_buffer * 3)),
                         arrowprops=dict(facecolor='black', shrink=0.05),
                         horizontalalignment='center', color='darkred', fontweight='bold', 
                         bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="red", lw=2))

        # FIXED TITLE: Uses 'rank' variable (1, 2, 3...)
        plt.title(f"Target: {district.upper()}, {state.upper()}\n(Ranked #{rank} in National Fraud Severity)", fontsize=16, fontweight='bold')
        
        ax1.set_ylabel("Child Enrolment Volume", color='#C0392B', fontsize=12)
        ax2.set_ylabel("Adult Updates (Reference)", color='grey', fontsize=12)
        ax2.grid(False)
        
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper left')
        
        plt.tight_layout()
        clean_name = f"{rank:02d}_{state}_{district}".replace(" ", "_") # Adds 01, 02 prefix to file name
        plt.savefig(f"{OUTPUT_FOLDER}/{clean_name}_Hybrid_Evidence.png", dpi=150)
        plt.close()
        print(f"  Generated Graph #{rank}: {district}")

    except Exception as e:
        print(f"  Error plotting {district}: {e}")

print("Done. Graphs should now be numbered 01 to 20 correctly.")