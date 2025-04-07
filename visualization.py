"""
CIT5900-002 Project 2
Step 5: Data Analysis & Visualization (Comprehensive)

This script covers the major tasks for Step 5:
1. Load the final curated CSV (default: "ProcessedData.csv")
2. Print data overview (head, info, descriptive stats, missing values)
3. Generate various plots:
   - Histograms & box plots (for numeric columns: citations, FuzzScores, etc.)
   - Bar charts (e.g., FSRDC_related, dataname if present)
   - Time-series line charts (e.g., OutputYear or year)
4. OPTIONAL advanced stats:
   - Correlation (if numeric columns exist, like year vs. citations)
   - Two-sample t-test (older vs. newer) if year & citations exist
5. Display or skip each plot gracefully based on column presence and data availability

Usage:
  python visualization.py
(Or import run_step5_analysis into main.py and call it from there.)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats  # For correlation, t-tests, etc.


def run_step5_analysis(csv_file: str = "ProcessedData.csv"):
    """
    Perform Step 5: Data Analysis & Visualization.

    :param csv_file: Path or filename of the final curated CSV.
    :return: None (prints and shows plots in a graphical environment)
    """
    # 1. LOAD DATA
    try:
        df = pd.read_csv(csv_file)
        print(f"Successfully loaded {csv_file}.")
    except FileNotFoundError:
        print(f"ERROR: {csv_file} not found. Please place the file in the correct path.")
        return

    # 2. BASIC OVERVIEW
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
    # 3. OPTIONAL VISUALIZATIONS / STATS FOR SPECIFIC COLUMNS
    #    We check each commonly expected column and produce a relevant plot.
    # ---------------------------------------------------------------------

    # 3A. CITATIONS (Histogram, Box Plot, Correlation, T-test)
    if 'citations' in df.columns:
        # Convert to numeric, drop missing
        df['citations'] = pd.to_numeric(df['citations'], errors='coerce')
        valid_citations = df['citations'].dropna()

        if not valid_citations.empty:
            # Histogram
            plt.figure(figsize=(8, 5))
            valid_citations.hist(bins=30)
            plt.title("Citation Count Distribution")
            plt.xlabel("Citations")
            plt.ylabel("Frequency")
            plt.show()

            # Box plot
            plt.figure(figsize=(5, 4))
            valid_citations.plot(kind='box')
            plt.title("Citation Count Box Plot")
            plt.ylabel("Citations")
            plt.show()
        else:
            print("\nNo valid numeric data in 'citations' to plot.")

    else:
        print("\n[SKIP] 'citations' column not found in this CSV.")

    # 3B. FUZZSCORES (Histogram, Box Plot)
    if 'FuzzScores' in df.columns:
        df['FuzzScores'] = pd.to_numeric(df['FuzzScores'], errors='coerce')
        valid_fuzz = df['FuzzScores'].dropna()
        if not valid_fuzz.empty:
            plt.figure(figsize=(8, 5))
            valid_fuzz.hist(bins=20)
            plt.title("FuzzScores Distribution")
            plt.xlabel("FuzzScore")
            plt.ylabel("Frequency")
            plt.show()

            plt.figure(figsize=(5, 4))
            valid_fuzz.plot(kind='box')
            plt.title("FuzzScores Box Plot")
            plt.ylabel("FuzzScore")
            plt.show()
        else:
            print("\nNo valid numeric data in 'FuzzScores' to plot.")
    else:
        print("\n[SKIP] 'FuzzScores' column not found in this CSV.")

    # 3C. OUTPUTYEAR or YEAR (Histogram, Time-Series Line Chart)
    #     If you have 'year' instead, just swap the references below.
    year_col_name = None
    if 'OutputYear' in df.columns:
        year_col_name = 'OutputYear'
    elif 'year' in df.columns:
        year_col_name = 'year'

    if year_col_name:
        df[year_col_name] = pd.to_numeric(df[year_col_name], errors='coerce')
        valid_years = df[year_col_name].dropna()
        if not valid_years.empty:
            # Histogram
            plt.figure(figsize=(8, 5))
            valid_years.hist(bins=20)
            plt.title(f"{year_col_name} Distribution")
            plt.xlabel("Year")
            plt.ylabel("Count of Papers")
            plt.show()

            # Line chart
            year_counts = valid_years.value_counts().sort_index()
            plt.figure(figsize=(8, 5))
            year_counts.plot(marker='o')
            plt.title(f"Number of Papers Published per {year_col_name}")
            plt.xlabel("Year")
            plt.ylabel("Number of Papers")
            plt.show()
        else:
            print(f"\nNo valid numeric data in '{year_col_name}' to plot.")
    else:
        print("\n[SKIP] No 'OutputYear' or 'year' column found.")

    # 3D. FSRDC_related (Bar Chart)
    if 'FSRDC_related' in df.columns:
        # Attempt to convert to bool if not already
        if df['FSRDC_related'].dtype != bool:
            try:
                df['FSRDC_related'] = df['FSRDC_related'].astype(bool)
            except ValueError:
                print("\nCould not convert 'FSRDC_related' to bool; skipping bar chart.")
                df['FSRDC_related'] = None  # or continue
        fsrdc_counts = df['FSRDC_related'].value_counts(dropna=False)
        if not fsrdc_counts.empty:
            plt.figure(figsize=(5, 4))
            fsrdc_counts.plot(kind='bar')
            plt.title("FSRDC_related (True vs False)")
            plt.xlabel("Value")
            plt.ylabel("Count")
            plt.xticks(rotation=0)
            plt.show()
        else:
            print("\n'FSRDC_related' column is present but empty.")
    else:
        print("\n[SKIP] No 'FSRDC_related' column found.")

    # 3E. DATANAME (Bar Chart) - If your CSV might have this
    if 'dataname' in df.columns:
        # Possibly a bar chart of dataset usage
        valid_data = df['dataname'].dropna()
        if not valid_data.empty:
            plt.figure(figsize=(10, 5))
            valid_data.value_counts().plot(kind='bar')
            plt.title("Dataset Usage (dataname)")
            plt.xlabel("Dataset Name")
            plt.ylabel("Count of Papers")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.show()
        else:
            print("\n'dataname' column is present but empty.")
    else:
        print("\n[SKIP] No 'dataname' column found.")

    # 3F. ADVANCED STATISTICS (Optional):
    # Example: correlation between year and citations
    # Example: older vs newer t-test
    # Only do if both columns exist and have data.
    if ('citations' in df.columns) and (year_col_name is not None):
        valid_merge = df[[year_col_name, 'citations']].dropna()
        if len(valid_merge) > 1:
            # Pearson correlation
            r_value, p_value = stats.pearsonr(valid_merge[year_col_name], valid_merge['citations'])
            print(f"\n=== PEARSON CORRELATION: {year_col_name} vs. citations ===")
            print(f"r = {r_value:.4f}, p = {p_value:.4e}")

            # T-test (older < 2015 vs. newer >= 2015)
            older_group = valid_merge.loc[valid_merge[year_col_name] < 2015, 'citations']
            newer_group = valid_merge.loc[valid_merge[year_col_name] >= 2015, 'citations']
            if len(older_group) > 1 and len(newer_group) > 1:
                t_stat, p_val = stats.ttest_ind(older_group, newer_group, equal_var=False)
                print("\n=== TWO-SAMPLE T-TEST (Older vs Newer Citations) ===")
                print(f"t-statistic = {t_stat:.4f}, p-value = {p_val:.4e}")
                print(f"Mean Citations (Older <2015): {older_group.mean():.2f}")
                print(f"Mean Citations (Newer >=2015): {newer_group.mean():.2f}")
            else:
                print("\nNot enough data in older/newer subsets for a two-sample t-test.")
        else:
            print("\nNot enough data for correlation or t-test on year vs. citations.")

    # 4. WRAP-UP
    print("\n=== STEP 5 ANALYSIS COMPLETE ===")
    print("Generated numeric summaries & plots for any relevant columns that exist.")
    print("If nothing displayed for certain columns, they may be missing or empty.")
