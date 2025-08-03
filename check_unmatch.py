import pandas as pd

try:
    from IPython.display import display
except ImportError:
    def display(df):
        # Jupyter の display が使えないときのフォールバック
        print(df)

# ファイルパスを指定
file1 = "Videos_InfluentialOrganizations_20250711_30.csv"
file2 = "sangiin_related_videos_Videos_InfluentialOrganizations_20250711_30.csv"

# CSVファイルの読み込み
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

# idカラムの抽出
ids1 = set(df1['id'])
ids2 = set(df2['id'])

# df1にのみ存在するid
only_in_df1 = ids1 - ids2

# df2にのみ存在するid
only_in_df2 = ids2 - ids1

print(f"df1にのみ存在するid数: {len(only_in_df1)}")
print(f"df2にのみ存在するid数: {len(only_in_df2)}")

# df1にのみ存在するレコード
df1_only = df1[df1['id'].isin(only_in_df1)]
print("df1にのみ存在するレコード:")
df1_only.to_csv("df1_only.csv", index=False)

