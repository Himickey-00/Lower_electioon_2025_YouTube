

#!/usr/bin/env python3
import argparse
import glob
import os
import re

"""Batch rename sangiin_related_* files to RelatedVideos_TVchannel_YYYYMMDD.csv"""

def unique_name(path: str) -> str:
    # If the target exists, append _1, _2, ... before extension to avoid overwrite
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while True:
        candidate = f"{base}_{i}{ext}"
        if not os.path.exists(candidate):
            return candidate
        i += 1


def main(pattern: str, dry_run: bool):
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"パターンに一致するファイルが見つかりません: {pattern}")
        return

    for src in files:
        dirname = os.path.dirname(src) or "."
        basename = os.path.basename(src)
        # Extract date after InfluentialOrganizations_
        m = re.search(r'InfluentialOrganizations_(20\d{6})', basename)
        if not m:
            print(f"[スキップ] 日付パターンが取れませんでした: {basename}")
            continue
        date = m.group(1)
        new_basename = f"RelatedVideos_InfluentialOrganizations_{date}.csv"
        dest = os.path.join(dirname, new_basename)
        dest = unique_name(dest)
        print(f"{src} -> {dest}" + (" (dry-run)" if dry_run else ""))
        if not dry_run:
            try:
                os.rename(src, dest)
            except Exception as e:
                print(f"リネーム失敗 {src} -> {dest}: {e}")

0
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='sangiin_related_* を RelatedVideos_InfluentialOrganizations_YYYYMMDD.csv に一括リネーム')
    parser.add_argument('--pattern', default='sangiin_related_*.csv', help='マッチさせる glob パターン')
    parser.add_argument('--dry-run', action='store_true', help='実際にはリネームせず表示のみ')
    args = parser.parse_args()
    main(args.pattern, dry_run=args.dry_run)