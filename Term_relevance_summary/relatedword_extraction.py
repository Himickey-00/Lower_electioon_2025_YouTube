import re
import subprocess
from collections import Counter
from typing import List, Set, Tuple, Optional

import pandas as pd
import numpy as np

# 形態素解析：mecab-python3
import MeCab
import os

# 文字正規化
try:
    import mojimoji
except ImportError:
    mojimoji = None

try:
    import jaconv
except ImportError:
    jaconv = None



# ------- 設定 -------

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


def build_corpus_tokens(
    df: pd.DataFrame,
    text_columns: List[str],
    tagger: MeCab.Tagger,
    stopwords: Set[str],
    chunk_noun_phrases: bool = False,
) -> List[List[str]]:
    corpus = []
    for _, row in df.iterrows():
        parts = []
        for col in text_columns:
            val = row.get(col, "")
            if pd.isna(val):
                continue
            parts.append(str(val))
        raw = " ".join(parts)
        norm = normalize_text(raw)
        tokens = tokenize(norm, tagger, stopwords, chunk_noun_phrases=chunk_noun_phrases)
        # ドキュメントごとに重複排除（順序を保つ）
        tokens = list(dict.fromkeys(tokens))
        corpus.append(tokens)
    return corpus


def tokens_to_documents(corpus_tokens: List[List[str]]) -> List[str]:
    return [" ".join(tokens) for tokens in corpus_tokens]


def compute_tf_df(corpus_tokens: List[List[str]]) -> pd.DataFrame:
    # 各ドキュメント内で重複が除かれている前提なので、tf は文書頻度と同義になる（1ドキュメントあたり1カウント）
    tf = Counter()
    df_counter = Counter()
    for tokens in corpus_tokens:
        tf.update(tokens)
        df_counter.update(set(tokens))
    data = []
    for term, cnt in tf.most_common():
        data.append({"term": term, "tf": cnt, "df": df_counter[term]})
    df_terms = pd.DataFrame(data)
    return df_terms


def suggest_stopword_candidates(df_terms: pd.DataFrame, existing_stopwords: Set[str], top_n: int = 100):
    candidates = []
    for _, row in df_terms.head(top_n * 2).iterrows():
        term = row["term"]
        if term in existing_stopwords:
            continue
        candidates.append((term, int(row["tf"])))
        if len(candidates) >= top_n:
            break
    return candidates




# ------- 生出現頻度用コーパス構築 -------
def build_raw_corpus_tokens(
    df: pd.DataFrame,
    text_columns: List[str],
    tagger: MeCab.Tagger,
    stopwords: Set[str],
    chunk_noun_phrases: bool = False,
) -> List[List[str]]:
    """各ドキュメント内の重複を潰さずにトークンを集めたコーパス（生出現頻度用）"""
    corpus = []
    for _, row in df.iterrows():
        parts = []
        for col in text_columns:
            val = row.get(col, "")
            if pd.isna(val):
                continue
            parts.append(str(val))
        raw = " ".join(parts)
        norm = normalize_text(raw)
        tokens = tokenize(norm, tagger, stopwords, chunk_noun_phrases=chunk_noun_phrases)  # 重複を潰さない
        corpus.append(tokens)
    return corpus


# ------- 実行部 -------

def main(
    csv_path: str,
    text_columns: List[str] = ["title", "description", "tags"],
    ipadic_path: Optional[str] = None,
    chunk_noun_phrases: bool = False,
):
    df = pd.read_csv(csv_path, dtype=str).fillna("")

    # 辞書パス未指定なら自動取得を試みる
    if ipadic_path is None:
        ipadic_path = get_default_ipadic_path()
    tagger = make_tagger(ipadic_path)

    stopwords = set(DEFAULT_STOPWORDS)

    corpus_tokens = build_corpus_tokens(df, text_columns, tagger, stopwords, chunk_noun_phrases=chunk_noun_phrases)
    df_terms = compute_tf_df(corpus_tokens)

    # ストップワード候補表示
    candidates = suggest_stopword_candidates(df_terms, stopwords, top_n=50)
    print("=== ストップワードレビュー候補（上位50） ===")
    for term, tf in candidates:
        print(f"{term} (tf={tf})")
    print("=========================================")

    # ------- 保存処理（入力ファイル名由来のサフィックス付き） -------
    basename = os.path.basename(csv_path)
    m = re.search(r'(20\d{6})', basename)
    if m:
        date_part = m.group(1)
    else:
        date_part = os.path.splitext(basename)[0]

    term_relevance_filename = f"term_relevance_summary_top100_{date_part}.csv"
    global_freq_filename = f"global_term_freq_top100_{date_part}.csv"

    # 1. 文書頻度上位100
    try:
        df_terms.head(100).to_csv(term_relevance_filename, index=False, encoding="utf-8-sig")
        print(f"保存: {term_relevance_filename}")
    except Exception as e:
        print(f"CSV保存に失敗しました: {e}")

    # 2. 生出現頻度上位100
    raw_corpus_tokens = build_raw_corpus_tokens(df, text_columns, tagger, stopwords, chunk_noun_phrases=chunk_noun_phrases)
    from collections import Counter
    global_flat = [token for doc in raw_corpus_tokens for token in doc]
    global_freq = Counter(global_flat)
    global_freq_top100 = global_freq.most_common(100)
    try:
        pd.DataFrame(global_freq_top100, columns=["term", "freq"]).to_csv(global_freq_filename, index=False, encoding="utf-8-sig")
        print(f"保存: {global_freq_filename}")
    except Exception as e:
        print(f"CSV保存に失敗しました: {e}")

    return {
        "df_terms": df_terms,
        "global_freq": global_freq,
        "corpus_tokens": corpus_tokens,
        "raw_corpus_tokens": raw_corpus_tokens,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MeCab-ipadic を使った前処理＋TF集計")
    parser.add_argument("csv_path", nargs="?", default="Query_20250703_547.csv", help="参照するCSVファイルのパス")
    parser.add_argument("--columns", nargs="+", help="解析対象のカラム名リスト（例: --columns title description tags）")
    parser.add_argument("--ipadic", default=None, help="mecab-ipadic の辞書ディレクトリ（自動検出が失敗したら明示指定）")
    parser.add_argument("--chunk", action='store_true', help="連続する名詞を結合して複合語化する")
    args = parser.parse_args()

    csv_path = args.csv_path
    if not os.path.isfile(csv_path):
        print(f"CSVファイルが見つかりません: {csv_path}")
        exit(1)

    main(csv_path, text_columns=args.columns if args.columns else ["title", "description", "tags"], ipadic_path=args.ipadic, chunk_noun_phrases=args.chunk)