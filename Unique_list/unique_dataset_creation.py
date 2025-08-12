import numpy as np
import pandas as pd
import os
import glob

try:
    _csv_dir = os.path.dirname(__file__)
except NameError:
    _csv_dir = os.getcwd()

_csv_files = glob.glob(os.path.join(_csv_dir, "*20250702*.csv"))

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
df_combined = pd.concat(dataframes.values(), ignore_index=True)
# 基本情報（None を出さないため print を使わずに）
print("[INFO] 結合後の DataFrame 概要:")
df_combined.info()

# view count の型混在・非数値をデバッグ
if "view count" in df_combined.columns:
    types = df_combined["view count"].apply(lambda x: type(x).__name__).value_counts()
    print(f"[DEBUG] 結合後 view count の Python 型分布:\n{types.to_string()}")
    cleaned = df_combined["view count"].astype(str).str.replace(r"[\,\s]", "", regex=True)
    non_digit_mask = ~cleaned.str.match(r"^\d+$")
    
    if non_digit_mask.any():
        print(f"[WARN] 結合後 view count に数字以外の形式が {non_digit_mask.sum()} 件あります。例:")
        print(df_combined.loc[non_digit_mask, ["id", "view count"]].head(10).to_string(index=False))
    # 数値変換用カラム
    df_combined["view_count_numeric"] = pd.to_numeric(cleaned, errors="coerce")
    bad = df_combined[df_combined["view_count_numeric"].isna() & ~df_combined["view count"].isna()]
    if not bad.empty:
        print("[WARN] view count を数値に変換できなかった行の例:")
        print(bad.loc[:, ["id", "view count"]].head(5).to_string(index=False))
else:
    print("[WARN] 'view count' カラムが存在しないため view count 関連のデバッグをスキップします。")

# 重複除去
orig_rows = df_combined.shape[0]
print(f"[INFO] 重複削除前の行数: {orig_rows}")
df_combined = df_combined.drop_duplicates(subset="id", keep='first')
new_rows = df_combined.shape[0]
print(f"[INFO] 重複削除後の行数: {new_rows} (削除された重複: {orig_rows - new_rows})")

# ソート（数値化した view_count_numeric があればそれで、なければ元の view count で）
if "view_count_numeric" in df_combined.columns:
    df_combined = df_combined.sort_values(by="view_count_numeric", ascending=False)
else:
    df_combined = df_combined.sort_values(by="view count", ascending=False)

# インデックスリセット
df_combined = df_combined.reset_index(drop=True)
print("[INFO] 最終的な DataFrame 情報:")
df_combined.info()

df_combined.to_csv(os.path.join(_csv_dir, "combined_20250702.csv"), index=False, encoding="utf-8-sig")