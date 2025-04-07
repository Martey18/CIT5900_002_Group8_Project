# -*- coding: utf-8 -*-
"""Step5_Project_2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1biM-2RiFTPAWom7iPjl-rAFcbnQW8EgC
"""

from google.colab import files
uploaded = files.upload()

"""
CIT5900-002 Project 2
Step 5: Data Analysis & Visualization

This script implements all required data exploration, visualization, and
basic statistical analysis for Step 5 of the project,
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

# 1. LOAD DATA
csv_file = "ProcessedData.csv"
try:
    df = pd.read_csv(csv_file)
    print(f"Successfully loaded {csv_file}.")
except FileNotFoundError:
    print(f"ERROR: {csv_file} not found. Please ensure it is uploaded or the path is correct.")
    raise SystemExit

# 2. DATA OVERVIEW
print("\n=== DATAFRAME HEAD ===")
print(df.head())

print("\n=== DATAFRAME INFO ===")
df.info()

print("\n=== DESCRIPTIVE STATISTICS (NUMERIC COLUMNS) ===")
print(df.describe())

# 3. MISSING VALUE CHECK
missing_vals = df.isnull().sum()
print("\n=== MISSING VALUES PER COLUMN ===")
print(missing_vals)

# 4. DATA CLEANING FOR YEAR & CITATIONS
# Convert 'year' and 'citations' columns to numeric if they aren't already
if 'year' in df.columns:
    df['year'] = pd.to_numeric(df['year'], errors='coerce')

if 'citations' in df.columns:
    df['citations'] = pd.to_numeric(df['citations'], errors='coerce')

# 5. VISUALIZATIONS

# A. CITATION DISTRIBUTION (Histogram & Box Plot)
if 'citations' in df.columns:
    # Histogram
    plt.figure(figsize=(8, 5))
    df['citations'].dropna().hist(bins=30)
    plt.title("Citation Count Distribution")
    plt.xlabel("Citations")
    plt.ylabel("Frequency")
    plt.show()

    # Box Plot
    plt.figure(figsize=(5, 4))
    df['citations'].dropna().plot(kind='box')
    plt.title("Citation Count Box Plot")
    plt.ylabel("Citations")
    plt.show()

# B. YEAR DISTRIBUTION (Histogram)
if 'year' in df.columns:
    plt.figure(figsize=(8, 5))
    df['year'].dropna().hist(bins=20)
    plt.title("Publication Year Distribution")
    plt.xlabel("Year")
    plt.ylabel("Count of Papers")
    plt.show()

# C. NUMBER OF PAPERS PER YEAR (Line Plot)
if 'year' in df.columns:
    # We'll group by year and count how many papers per year
    year_counts = df['year'].dropna().value_counts().sort_index()
    plt.figure(figsize=(8, 5))
    year_counts.plot(marker='o')
    plt.title("Number of Papers Published per Year")
    plt.xlabel("Year")
    plt.ylabel("Number of Papers")
    plt.show()

# D. DATASET USAGE FREQUENCY (Bar Chart)
if 'dataname' in df.columns:
    plt.figure(figsize=(10, 5))
    df['dataname'].value_counts().plot(kind='bar')
    plt.title("Frequency of Datasets (dataname)")
    plt.xlabel("Dataset Name")
    plt.ylabel("Count of Papers")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

# 6. BASIC STATISTICAL ANALYSES

# 6A. CORRELATION (Pearson) BETWEEN YEAR AND CITATIONS
if 'year' in df.columns and 'citations' in df.columns:
    # Drop rows with missing year or citations
    corr_data = df[['year', 'citations']].dropna()
    if len(corr_data) > 1:
        r_value, p_value = stats.pearsonr(corr_data['year'], corr_data['citations'])
        print("\n=== PEARSON CORRELATION: YEAR vs CITATIONS ===")
        print(f"r = {r_value:.4f}, p = {p_value:.4e}")
    else:
        print("\nNot enough data to compute correlation between year and citations.")

# 6B. TWO-SAMPLE T-TEST: OLDER (year < 2015) vs NEWER (year >= 2015) CITATIONS
if 'year' in df.columns and 'citations' in df.columns:
    older_group = df.loc[df['year'] < 2015, 'citations'].dropna()
    newer_group = df.loc[df['year'] >= 2015, 'citations'].dropna()

    if len(older_group) > 1 and len(newer_group) > 1:
        t_stat, p_val = stats.ttest_ind(older_group, newer_group, equal_var=False)
        print("\n=== TWO-SAMPLE T-TEST (Older vs Newer Citations) ===")
        print(f"t-statistic = {t_stat:.4f}, p-value = {p_val:.4e}")
        print(f"Mean Citations (Older <2015): {older_group.mean():.2f}")
        print(f"Mean Citations (Newer >=2015): {newer_group.mean():.2f}")
    else:
        print("\nNot enough data in older/newer subsets for a two-sample t-test.")

# 7. CONCLUSION
print("\n=== STEP 5 ANALYSIS COMPLETE ===")
print("All summary statistics, visualizations, and basic statistical tests have been performed.")
print("Plots have been displayed above. Check console outputs for numeric summaries.")