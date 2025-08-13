import numpy as np
import pandas as pd

import argparse
import os
import glob

try:
    _csv_dir = os.path.dirname(__file__)
except NameError:
    _csv_dir = os.getcwd()

_csv_files = glob.glob(os.path.join(_csv_dir, "refetched_*.csv"))
                       
dataframes = {}
for f in _csv_files:
    base = os.path.splitext(os.path.basename(f))[0]
    df = pd.read_csv(f)
    print(f"[INFO] 読み込み完了: {f} (行数: {df.shape[0]}, 列数: {df.shape[1]})")
    print(f"[DEBUG] {base} カラム: {df.columns.tolist()}")
    print(f"[DEBUG] {base} サンプル (先頭3行):\n{df.head(3).to_string(index=False)}")
    dataframes[base] = df

print("[INFO] 正常に読み込めたファイル一覧:")
for name in dataframes:
    print(f"  - {name}")

print("[INFO] 正常に読み込めたデータフレームを縦方向に結合します...")
df_delated = pd.concat(dataframes.values(), ignore_index=True)
df_delated.info()

df_delated.to_csv(os.path.join(_csv_dir,"Refetched_LowerElection_Videos.csv"), index=False, encoding="utf-8-sig")