import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- CONFIGURATION ---
INPUT_REPORT_FILE = "State_Accessibility_Report.csv" 
OUTPUT_CHART_FILE = "Chart_State_Accessibility_VERTICAL.png"

print(f"Loading report from {INPUT_REPORT_FILE}...")
# We need to explicitly load the 'state' column from the CSV's index
report_df = pd.read_csv(INPUT_REPORT_FILE)

# Ensure the states are sorted from best to worst for a clean visual ranking
report_df = report_df.sort_values(by='Sunday_Score_%', ascending=False)

# --- VISUALIZATION SCRIPT (MODIFIED FOR VERTICAL) ---
print("Generating Vertical Bar Chart for ALL states...")

# 1. Adjust Figure Size to be WIDER
# A wider aspect ratio is better for vertical bars
plt.figure(figsize=(20, 10)) # Increased width, reduced height
sns.set_style("whitegrid")

# Create a color palette based on grade
palette = {'EXCELLENT': '#27AE60', 'GOOD': '#2ECC71', 'AVERAGE': '#F1C40F', 'POOR (Weekday Only)': '#E74C3C'}

# 2. SWAP X and Y axes
barplot = sns.barplot(
    data=report_df,
    x='state',              # States are now on the X-axis
    y='Sunday_Score_%',     # Percentages are now on the Y-axis
    hue='Accessibility_Grade',
    palette=palette,
    dodge=False 
)

# 3. ROTATE X-AXIS LABELS
# This is crucial to prevent state names from overlapping
plt.xticks(rotation=90, fontsize=12) 
plt.yticks(fontsize=12)

# 4. SWAP AXIS LABELS
plt.title('"Sunday Service" Score: State Accessibility for Daily Wage Earners', fontsize=20, fontweight='bold')
plt.ylabel('Percentage of Total Aadhaar Activity Occurring on Sunday (%)', fontsize=14)
plt.xlabel('State', fontsize=14)
plt.legend(title='Accessibility Grade', fontsize=12)

# Use tight_layout to make sure the rotated labels fit in the image
plt.tight_layout() 

plt.savefig(OUTPUT_CHART_FILE, dpi=300)
print(f"SUCCESS! Saved VERTICAL chart to {OUTPUT_CHART_FILE}")