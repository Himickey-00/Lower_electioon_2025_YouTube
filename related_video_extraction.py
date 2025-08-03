#!/usr/bin/env python3
import argparse
import os
import re
import pandas as pd
from collections import Counter
import glob

# Add missing imports for subprocess and typing
import subprocess
from typing import Optional, Set, List

# MeCab周りのインポート（mecab-ipadic / neologd を想定）
import MeCab

# ---------- 正規化 / トークン化ロジック ----------

# 単語正規化
try:
    import mojimoji
except ImportError:
    mojimoji = None

try:
    import jaconv
except ImportError:
    jaconv = None

ALLOWED_POS = "名詞"
ALLOWED_SUBTYPES = {"一般", "固有名詞", "サ変接続"}   

DEFAULT_STOPWORDS = {
    "こと", "もの", "ため", "よう", "それ", "これ", "という", "その", "ある", "いる", "なる",
    "など", "そして", "から", "まで", "また", "において", "および", "にとって", "について", "に関する",
    "ような", "される", "する", "されて", "いる", "ます", "です", "https", "com", "www","ー", "jp", "http"
}

# 明示的に結合したい名詞列（順序付き）。例: ('参政','党') -> '参政党'
COMPOUND_WHITELIST_SEQS = [
    ("参政", "党"),
    ("立憲", "民主", "党"), 
    ("立憲", "民主党"), 
    ("日本", "維新", "の", "会"),
    ("国民", "民主", "党"),  
    ("国民", "民主党"),
    ("共産", "党"),
    ("社民", "党"),
    ("れいわ", "新選組"),  
    ("日本", "保守", "党"),  
    ("日本", "保守党"),
    ("再生", "の", "道"),
    ("再生", "道"),
    ("自民", "党"),
    ("公明", "党"),
    ("参院", "選"),
    ("参議院", "選挙"),
    ("党", "首")
]

# --- シード語リスト（高信頼語） ---
SEED_TERMS = {
    "参議院選挙", "参院", "参院選", "投票", "比例代表", "候補者", "改選", "期日前投票",
    "自民党", "公明党", "日本維新の会", "れいわ新選組", "立憲民主党", "国民民主党", "日本共産党", "社会民主党",
    "参政党", "日本保守党", "再生の道", "幸福実現党", "チームみらい"
}

RE_NUM_PUNC = re.compile(r"[0-9０-９]|[!-/:-@[-`{-~。「」、。・『』（）［］〈〉《》]+")


# ------- ユーティリティ -------

def get_default_ipadic_path() -> Optional[str]:
    # 環境変数で neologd を優先
    neologd = os.environ.get("MECAB_NEOLOGD")
    if neologd and os.path.isdir(neologd):
        return neologd
    try:
        out = subprocess.run(["mecab-config", "--dicdir"], capture_output=True, text=True, check=True)
        dicdir = out.stdout.strip()
        ipadic = f"{dicdir}/ipadic"
        return ipadic
    except Exception:
        return None
    
def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    s = text
    if mojimoji:
        s = mojimoji.zen_to_han(s, kana=False)
    if jaconv:
        s = jaconv.kata2hira(s)
    s = s.lower()
    s = RE_NUM_PUNC.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def make_tagger(ipadic_path: Optional[str] = None) -> MeCab.Tagger:
    """MeCab タガーを作成。ipadic のパスを明示的に与えられればそれを使う。"""
    options = ""
    if ipadic_path:
        options += f"-d {ipadic_path} "
    # 出力フォーマットはデフォルト（解析結果をノードで取得する）
    return MeCab.Tagger(options.strip())

def tokenize(
    text: str,
    tagger: MeCab.Tagger,
    stopwords: Set[str],
    allowed_pos: str = ALLOWED_POS,
    allowed_subtypes: Set[str] = ALLOWED_SUBTYPES,
    chunk_noun_phrases: bool = False,
) -> List[str]:
    """
    MeCab (ipadic) で分かち書きし、品詞/細分類・ストップワードでフィルタしたトークンを返す。
    連続する名詞を結合して複合語化するオプション chunk_noun_phrases をサポート。
    """
    if not text:
        return []
    candidates = []
    node = tagger.parseToNode(text)
    while node:
        surface = node.surface
        feature = node.feature.split(",")
        pos1 = feature[0] if len(feature) > 0 else ""
        subtype = feature[1] if len(feature) > 1 else ""
        if pos1 == allowed_pos and (not allowed_subtypes or subtype in allowed_subtypes):
            if surface and surface not in stopwords:
                candidates.append(surface)
        node = node.next
    # 明示的なホワイトリスト結合: 連続する surface が COMPOUND_WHITELIST_SEQS にあればまとめる
    def apply_whitelist(surfaces):
        i = 0
        merged = []
        while i < len(surfaces):
            matched = False
            for seq in COMPOUND_WHITELIST_SEQS:
                k = len(seq)
                if i + k <= len(surfaces) and tuple(surfaces[i:i+k]) == seq:
                    merged.append("".join(seq))
                    i += k
                    matched = True
                    break
            if not matched:
                merged.append(surfaces[i])
                i += 1
        return merged
    surfaces = apply_whitelist(candidates)
    if not chunk_noun_phrases:
        return surfaces
    # chunk_noun_phrases=True のときは非重複の pairwise bigram でのみ結合（長くなりすぎないように）
    chunked = []
    i = 0
    while i < len(surfaces):
        if i + 1 < len(surfaces):
            chunked.append(surfaces[i] + surfaces[i+1])
            i += 2
        else:
            chunked.append(surfaces[i])
            i += 1
    return chunked


# ---------- マッチ処理本体 ----------

def load_unique_terms(path: str) -> set:
    df = pd.read_csv(path, dtype=str)
    if "term" not in df.columns:
        raise ValueError(f"{path} に 'term' 列がありません。")
    terms = df["term"].dropna().astype(str).tolist()
    # 正規化を揃えたいならここで normalize_text を通す（動画のテキストも同じ処理をする前提）
    normalized = set([normalize_text(t) for t in terms])
    return normalized


def match_terms_in_text(
    text: str,
    tagger: MeCab.Tagger,
    term_set: set,
    chunk_noun_phrases: bool,
    stopwords: set,
) -> list:
    norm = normalize_text(text)
    tokens = tokenize(norm, tagger, stopwords, chunk_noun_phrases=chunk_noun_phrases)
    # 文書内ユニーク化
    token_set = set(tokens)
    # 正規化済みの term_set と照合（必要なら token も normalize しておくが normalize_text は先にかけている）
    matches = [t for t in token_set if t in term_set]
    return matches


def process_video_file(
    video_csv: str,
    unique_terms_path: str,
    output_prefix: str,
    ipadic_path: str = None,
    chunk: bool = False,
    chunksize: int = None,
):
    tagger = make_tagger(ipadic_path)
    stopwords = set(DEFAULT_STOPWORDS)
    term_set = load_unique_terms(unique_terms_path)

    basename = os.path.basename(video_csv)
    out_name = f"{output_prefix}_{os.path.splitext(basename)[0]}.csv"

    related_rows = []
    total = 0
    matched_total = 0
    # 読み込み（大きければ chunksize を使う）
    reader = pd.read_csv(video_csv, dtype=str, chunksize=chunksize) if chunksize else [pd.read_csv(video_csv, dtype=str)]
    for df in reader:
        df = df.fillna("")
        # 各行処理
        for _, row in df.iterrows():
            total += 1
            # title, description, tags をまとめる
            text_parts = []
            for col in ["title", "description", "tags"]:
                if col in row:
                    text_parts.append(str(row[col]))
            combined = " ".join(text_parts)
            norm_full = normalize_text(combined)
            norm_full_nospace = norm_full.replace(" ", "")  # シード語はスペースなしでも拾えるように

            # シード語のヒットをチェック（高信頼語）
            seed_hits = []
            for seed in SEED_TERMS:
                if seed in norm_full_nospace:
                    seed_hits.append(seed)

            # unique_terms との一致（トークンレベル）
            term_matches = match_terms_in_text(
                combined, tagger, term_set, chunk_noun_phrases=chunk, stopwords=stopwords
            )

            # 判定: シード語があれば即採用、そうでなければ unique_terms の語が4つ以上
            if seed_hits or len(term_matches) >= 4:
                matched_total += 1
                row_out = row.to_dict()
                # seed と term_matches を統合（順序保持で重複除去）
                matches = list(dict.fromkeys(seed_hits + term_matches))
                row_out["matched_terms"] = ";".join(sorted(matches))
                row_out["matched_count"] = len(matches)
                related_rows.append(row_out)

    if not related_rows:
        print(f"{video_csv}: 参院選関連動画が見つかりませんでした（全 {total} 本中）")
        return

    out_df = pd.DataFrame(related_rows)
    # 保存
    try:
        out_df.to_csv(out_name, index=False, encoding="utf-8-sig")
        print(f"{video_csv}: 関連動画 {matched_total}/{total} 本を {out_name} に保存しました。")
    except Exception as e:
        print(f"保存失敗 {out_name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="unique_terms でフィルタして参院選関連動画を抽出")
    parser.add_argument("video_csv", help="Videos_*.csv")
    parser.add_argument("unique_terms", help="unique_terms.csv")
    parser.add_argument("--pattern", default="Videos_*.csv", help="Videos_*.csv"
    )
    parser.add_argument(
        "--ipadic", default=None, help="mecab-ipadic-neologd の辞書パス（省略で自動検出）"
    )
    parser.add_argument(
        "--output-prefix", default="sangiin_related_videos", help="出力ファイルのプレフィックス"
    )
    parser.add_argument(
        "--chunksize", type=int, default=None, help="大きいファイルを分割読みする場合のチャンクサイズ"
    )
    args = parser.parse_args()

    video_paths = sorted(glob.glob(args.pattern))
    if not video_paths:
        print(f"パターンに一致するファイルが見つかりません: {args.pattern}")
        return
    for video_csv in video_paths:
        process_video_file(
            video_csv,
            args.unique_terms,
            args.output_prefix,
            ipadic_path=args.ipadic,
            chunksize=args.chunksize,
        )


if __name__ == "__main__":
    main()