# -*- coding: utf-8 -*-
"""visualization.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1hVzRNd49wGMj9L26rdpsTZfsoxxg1YP0
"""

from google.colab import files

# Upload file
uploaded = files.upload()

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# If you have advanced stats to do, you can import scipy.stats as needed
# import scipy.stats as stats

csv_file = "ProcessedData.csv"  # rename if your file is different

try:
    df = pd.read_csv(csv_file)
    print(f"Successfully loaded {csv_file}.")
except FileNotFoundError:
    print(f"ERROR: {csv_file} not found. Please upload or correct the path.")
    raise SystemExit

print("\n=== DATAFRAME HEAD ===")
print(df.head())

print("\n=== DATAFRAME INFO ===")
df.info()

print("\n=== DESCRIPTIVE STATISTICS (NUMERIC COLUMNS) ===")
print(df.describe(include=[np.number]))

print("\n=== MISSING VALUES PER COLUMN ===")
missing_vals = df.isnull().sum()
print(missing_vals)

# ---------------------------------------------------------------------
# 1. EXAMPLE: FuzzScores HISTOGRAM + BOX PLOT
#    (If 'FuzzScores' is in your CSV and is numeric)
# ---------------------------------------------------------------------
if 'FuzzScores' in df.columns and df['FuzzScores'].dropna().shape[0] > 0:
    # Convert to numeric
    df['FuzzScores'] = pd.to_numeric(df['FuzzScores'], errors='coerce')

    print("\nPlotting FuzzScores Distribution & Box Plot...")
    plt.figure(figsize=(8,5))
    df['FuzzScores'].dropna().hist(bins=20)
    plt.title("FuzzScores Distribution")
    plt.xlabel("FuzzScores")
    plt.ylabel("Frequency")
    plt.show()

    plt.figure(figsize=(5,4))
    df['FuzzScores'].dropna().plot(kind='box')
    plt.title("FuzzScores Box Plot")
    plt.ylabel("FuzzScores")
    plt.show()
else:
    print("\nNo valid 'FuzzScores' data found. Skipping those plots.")

# ---------------------------------------------------------------------
# 2. EXAMPLE: OutputYear HISTOGRAM + LINE CHART
#    (If 'OutputYear' is in your CSV)
# ---------------------------------------------------------------------
if 'OutputYear' in df.columns and df['OutputYear'].dropna().shape[0] > 0:
    # Convert to numeric
    df['OutputYear'] = pd.to_numeric(df['OutputYear'], errors='coerce')
    valid_years = df['OutputYear'].dropna()
    if len(valid_years) > 0:
        print("\nPlotting OutputYear Distribution & Yearly Count...")
        plt.figure(figsize=(8,5))
        valid_years.hist(bins=20)
        plt.title("OutputYear Distribution")
        plt.xlabel("Year")
        plt.ylabel("Count of Papers")
        plt.show()

        # LINE CHART of outputs by year
        year_counts = valid_years.value_counts().sort_index()
        plt.figure(figsize=(8,5))
        year_counts.plot(marker='o')
        plt.title("Number of Papers Published per OutputYear")
        plt.xlabel("Year")
        plt.ylabel("Number of Papers")
        plt.show()
else:
    print("\nNo valid 'OutputYear' data found. Skipping year-based plots.")

# ---------------------------------------------------------------------
# 3. EXAMPLE: Bar Chart for FSRDC_related
#    (If 'FSRDC_related' is in your CSV and is boolean)
# ---------------------------------------------------------------------
if 'FSRDC_related' in df.columns and df['FSRDC_related'].dropna().shape[0] > 0:
    # Convert to bool if not already
    if df['FSRDC_related'].dtype != bool:
        # Try to interpret string "True"/"False"
        df['FSRDC_related'] = df['FSRDC_related'].astype(bool, errors='ignore')

    # Count how many True vs False
    fsrdc_counts = df['FSRDC_related'].value_counts()
    print("\nPlotting FSRDC_related bar chart (True/False)...")
    plt.figure(figsize=(4,4))
    fsrdc_counts.plot(kind='bar')
    plt.title("FSRDC_related (True vs False)")
    plt.xlabel("Value")
    plt.ylabel("Count of Records")
    plt.xticks(rotation=0)
    plt.show()
else:
    print("\nNo 'FSRDC_related' column or no valid data. Skipping bar chart.")

# ---------------------------------------------------------------------
# WRAP-UP
# ---------------------------------------------------------------------
print("\n=== STEP 5 ANALYSIS COMPLETE ===")
print("All relevant plots have been displayed above.")
print("If you did not see certain plots, that likely means the columns were missing or empty.")

