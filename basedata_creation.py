import numpy as np
import pandas as pd
import argparse
import os
import glob
import matplotlib.pyplot as plt
import seaborn as sns

import ydata_profiling
from ydata_profiling import ProfileReport


def create_totalcsv() -> pd.DataFrame:
    csvs = glob.glob("combined_*.csv")
    if not csvs:
        print("No combined CSV files found.")
        return pd.DataFrame()
    dfs = [pd.read_csv(csv) for csv in csvs]
    totalcsv = pd.concat(dfs, ignore_index=True)
    return totalcsv

## Unused now
# def generate_profile_report(input_file: str, output_file: str):
#     # Load the dataset
#     df = pd.read_csv(input_file)
#     
#     # Generate the profile report
#     profile = ProfileReport(df, title="Total Descriptive Statistics Report", explorative=True)
#     
#     # Save the report to an HTML file
#     profile.to_file(output_file)
#     print(f"Profile report saved to {output_file}")

def main():
    # Find and combine all CSV files
    df = create_totalcsv()
    if df.empty:
        return

    df.to_csv("lower_election_2025.csv", index=False, encoding='utf-8-sig')
    # Ensure output directory exists
    # output_dir = "reports"
    # os.makedirs(output_dir, exist_ok=True)

    # # Generate single profile report for combined DataFrame
    # output_file = os.path.join(output_dir, "profile_report_combined.html")
    # profile = ProfileReport(df, title="Combined Descriptive Statistics Report", explorative=True)
    # profile.to_file(output_file)
    # print(f"Profile report saved to {output_file}")

if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Generate descriptive statistics reports for CSV files.")
    # parser.add_argument('--input-pattern', default='total.csv', help='Glob pattern to match input CSV files')
    # parser.add_argument('--output-dir', default='reports', help='Directory to save the output reports')
    # args = parser.parse_args()
    # main(args.input_pattern, args.output_dir)
    main()