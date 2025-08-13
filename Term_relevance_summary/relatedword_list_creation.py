#!/usr/bin/env python3

import argparse
import glob
import os
import pandas as pd
import re

# 内部ストップワード（明らかに参院選関連ではないと思われる語を小文字化して列挙）
INTERNAL_STOPLIST = {
    "日本", "月", "政治", "youtube", "にゅーす", "お願い", "東京", "動画", "登録", "配信", "twitter", "日", "news",
    "channel", "情報", "人", "co", "社会", "nhk", "instagram", "join", "facebook", "sns", "年",
    "経済", "最新", "回", "解説", "報道", "shorts", "live", "line", "tiktok", "特典", "視聴", "放送", 
    "内容", "voicevox", "be", "ch", "提供", "連絡", "運営", "hp", "sub", "生活", "声", "募集", "youtu",
    "発信", "新聞", "go", "企業", "html", "watch", "url", "生放送", "世界", "tv", "番組", "出演" 
}

def load_terms_from_file(path):
    df = pd.read_csv(path, dtype=str)
    if 'term' not in df.columns:
        raise ValueError(f"{path} に 'term' 列がありません")
    terms = df['term'].dropna().astype(str).tolist()
    return terms


def main(dir_path, pattern='term_relevance*.csv', output='merged_unique_terms.csv'):
    search_path = os.path.join(dir_path, pattern)
    files = sorted(glob.glob(search_path))
    if not files:
        print(f"一致するファイルが見つかりません: {search_path}")
        return

    all_terms = []
    for f in files:
        try:
            terms = load_terms_from_file(f)
        except Exception as e:
            print(f"読み込み失敗 {f}: {e}")
            continue
        print(f"{os.path.basename(f)}: {len(terms)} 語読み込み")
        all_terms.extend(terms)

    # 重複を除いて順序を保つ
    seen = set()
    unique_terms = []
    for term in all_terms:
        if term not in seen:
            seen.add(term)
            unique_terms.append(term)

    print(f"ファイル数: {len(files)}, 元の語数: {len(all_terms)}, ユニーク語数: {len(unique_terms)}")

    filtered_terms = [term for term in unique_terms if not (re.fullmatch(r'[A-Za-z]', term) or re.fullmatch(r'^[\u3041-\u3096]+$', term))]
    print(f"フィルタ前ユニーク語数: {len(unique_terms)}, フィルタ後: {len(filtered_terms)}")
    before_stop = len(filtered_terms)
    filtered_terms = [t for t in filtered_terms if t.lower() not in {w.lower() for w in INTERNAL_STOPLIST}]
    after_stop = len(filtered_terms)
    removed = before_stop - after_stop
    print(f"内部ストップリスト適用: {removed} 語を除外しました（残り {after_stop} 語）")

    out_df = pd.DataFrame({'term': filtered_terms})
    try:
        out_df.to_csv(output, index=False, encoding='utf-8-sig')
        print(f"保存: {output}")
    except Exception as e:
        print(f"保存失敗: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='term_relevance* ファイルから term 列を集めてユニーク化')
    parser.add_argument('--dir', default='.', help='ファイルを探すディレクトリ')
    parser.add_argument('--pattern', default='term_relevance*.csv', help='glob パターン (デフォルト term_relevance*.csv)')
    parser.add_argument('--output', default='merged_unique_terms.csv', help='出力ファイル名')
    args = parser.parse_args()
    main(args.dir, pattern=args.pattern, output=args.output)