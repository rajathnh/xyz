# AI-Driven Fraud Detection Engine

**Team Name:** XYZ   
**Context:** UIDAI Data Hackathon Submission

---

## 📋 Executive Summary
**Project Aadhaar Satark** (also referred to as Project SENTINEL) is a forensic analytics framework designed to detect **"Ghost Beneficiary" fraud** in child welfare schemes.

By analyzing **4.93 Million official Aadhaar records**, this system identifies statistically impossible spikes in child enrolments (Age 0-5) that do not correlate with adult biometric footfall. It utilizes a **Hybrid Neuro-Symbolic Engine** (Statistical Dynamic Thresholding + Isolation Forest) to distinguish between legitimate government camps and fraudulent bulk-data injection.

---

## 🛠️ Technology Stack
*   **Language:** Python 3.9+
*   **ETL & Processing:** `pandas`, `numpy`
*   **Machine Learning:** `scikit-learn` (Isolation Forest)
*   **Visualization:** `seaborn`, `matplotlib`
*   **External Data:** Official India Post Pincode Directory

---

## 📂 Repository Structure & File Guide

### 1. Data Ingestion & Merging
The raw data provided was fragmented into split-CSV files. These scripts consolidate them into unified master datasets.
*   **`merge_enrollment.py`**: Combines split Enrolment CSVs into `Final_Monthly_Data_Combined.csv`.
*   **`merge_biometric.py`**: Combines split Biometric Update CSVs into `Final_Biometric_Data_Combined.csv`.
*   **`merge_demographic.py`**: Combines split Demographic CSVs into `Final_Demographic_Data_Combined.csv`.

### 2. Standardization & Geotagging
*   **`get_pincode_master.py`**: Downloads the "Golden Source" Pincode Directory from government sources/GitHub to create a master mapping file (`pincode_master_unique.csv`).
*   **`clean_all_datasets.py`**: The core cleaning engine. It takes the merged datasets, maps every row against the Pincode Master, corrects spelling errors (e.g., "West Bengli" -> "West Bengal"), and standardizes the dataset for analysis.

### 3. Intelligence & Fraud Detection
*   **`detect_ghost_childern.py`**: 
    *   **Algorithm:** Statistical Dynamic Thresholding (Strict 0.5 SD).
    *   **Function:** Generates visualization graphs comparing Child Enrolment vs. Adult Biometric Updates. Creates the "Green Line vs Red Spike" forensic charts.
*   **`fwdusingai.py`**: 
    *   **Algorithm:** Hybrid Ensemble (Statistical Rule + Unsupervised Isolation Forest).
    *   **Function:** Scans all 806 districts, ranks them by fraud severity, and generates the **"National Vigilance Hit-List"** (Top 20 Districts) along with detailed evidence graphs.

---

## 🚀 How to Run the Pipeline

### Step 1: Setup
Ensure you have the required libraries installed:
```bash
pip install pandas numpy matplotlib seaborn scikit-learn requests
```
### Step 2: Ingest Raw Data
Update the file paths in the merge_*.py scripts to point to your local raw downloads, then run:
```bash
python merge_enrollment.py
python merge_biometric.py
python merge_demographic.py
```
### Step 3: Clean & Standardize
Generate the master Pincode key and clean the datasets:
```bash
python get_pincode_master.py
python clean_all_datasets.py
```
Output: Files named Cleaned_Final_.csv will appear in the directory.
### Step 4: Generate Intelligence
Run the Hybrid AI engine to identify top fraud targets:
```bash
python fwdusingai.py
```
Output:
1) Console: Prints the "National Fraud Hit-List" (Top 20 Districts).
2) Folder: Creates National_Top_20_Fraud_Districts/ containing forensic evidence graphs for the worst offenders.

### 📊 Key Output Examples
The system generates forensic graphs highlighting two specific fraud typologies:
1) The Hijacked Camp: Where legitimate adult footfall is used to mask a disproportionate injection of fake child records (e.g., Barpeta, Assam).
2) The Phantom Entry: Massive spikes in child enrolment during periods of zero adult activity (e.g., 24 Parganas North, West Bengal).