import os
import time
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- 設定項目 ---
# ここにあなたのYouTube Data API v3キーを入力してください
API_KEY = "AIzaSyCGDuqkF_U13tfUjtGPLkQRO2jukWosUN0"

# 動画IDが含まれるCSVファイルのパス
CSV_PATH = "refetched_20250709.csv"
# 出力先のディレクトリ (このフォルダ内にチャンクごとのCSVが作成されます)
OUTPUT_DIR = "comment_chunks"
# 1つのチャンクに含まれる動画IDの数
CHUNK_SIZE = 50

# API情報
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"


# --- コメント取得ロジック ---

def _flatten_top_level_comment(tlc_obj: dict, video_id: str) -> dict:
    s = tlc_obj.get("snippet", {})
    author_channel = s.get("authorChannelId", {})
    return {
        "videoId": video_id, "commentId": tlc_obj.get("id"), "parentId": None,
        "isReply": False, "authorChannelId": author_channel.get("value"),
        "authorDisplayName": s.get("authorDisplayName"), "text": s.get("textOriginal") or s.get("textDisplay"),
        "likeCount": s.get("likeCount"), "publishedAt": s.get("publishedAt"), "updatedAt": s.get("updatedAt"),
    }

def _flatten_reply_comment(reply_obj: dict) -> dict:
    s = reply_obj.get("snippet", {})
    author_channel = s.get("authorChannelId", {})
    return {
        "videoId": s.get("videoId"), "commentId": reply_obj.get("id"), "parentId": s.get("parentId"),
        "isReply": True, "authorChannelId": author_channel.get("value"),
        "authorDisplayName": s.get("authorDisplayName"), "text": s.get("textOriginal") or s.get("textDisplay"),
        "likeCount": s.get("likeCount"), "publishedAt": s.get("publishedAt"), "updatedAt": s.get("updatedAt"),
    }

def fetch_replies_for_parent(youtube, parent_id: str):
    all_replies = []
    page_token = None
    while True:
        try:
            resp = youtube.comments().list(
                part="snippet", parentId=parent_id, maxResults=100,
                pageToken=page_token, textFormat="plainText",
            ).execute()
            for item in resp.get("items", []):
                all_replies.append(_flatten_reply_comment(item))
            page_token = resp.get("nextPageToken")
            if not page_token: break
        except HttpError as e:
            print(f"  [警告] 親コメントID {parent_id} の返信取得中にエラー: {e}")
            break
    return all_replies

def fetch_comments_for_video(youtube, video_id: str):
    """
    1つの動画IDに対するコメントを取得する。
    コメント無効などのスキップ可能なエラーが発生しても、プログラム全体は中断しない。
    """
    all_comments = []
    page_token = None
    while True:
        try:
            resp = youtube.commentThreads().list(
                part="snippet,replies", videoId=video_id, maxResults=100,
                pageToken=page_token, order="time", textFormat="plainText",
            ).execute()
            for item in resp.get("items", []):
                top_level_comment = item.get("snippet", {}).get("topLevelComment", {})
                if not top_level_comment: continue
                all_comments.append(_flatten_top_level_comment(top_level_comment, video_id=video_id))
                total_reply_count = item.get("snippet", {}).get("totalReplyCount", 0)
                if total_reply_count > 0:
                    parent_id = top_level_comment.get("id")
                    replies = fetch_replies_for_parent(youtube, parent_id=parent_id)
                    all_comments.extend(replies)
            page_token = resp.get("nextPageToken")
            if not page_token: break
            time.sleep(0.1)
        except HttpError as e:
            # エラーハンドリングを改善
            if e.resp.status == 403:
                print(f"  [情報] 動画ID '{video_id}' のコメントは無効か、非公開です。スキップします。")
            elif e.resp.status == 404:
                print(f"  [情報] 動画ID '{video_id}' が見つかりません。スキップします。")
            else:
                # 致命的ではないが予期せぬエラー
                print(f"  [警告] 動画ID '{video_id}' のコメントスレッド取得中にAPIエラー: {e}")
            
            # どのようなエラーでも、この動画の処理を中断し、次の動画に移るためにループを抜ける
            break
    return all_comments

# --- メイン処理 (チャンク分割対応) ---

def main():
    if API_KEY == "ここにあなたのAPIキーを入力してください":
        print("エラー: スクリプト上部の `API_KEY` 変数に、あなたのYouTube Data APIキーを設定してください。")
        return

    # 1. 出力用ディレクトリを作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. CSVから動画IDを読み込む
    try:
        df = pd.read_csv(CSV_PATH)
        if "id" not in df.columns:
            raise KeyError(f"'id' カラムが見つかりません。")
        video_ids = df["id"].dropna().astype(str).unique().tolist()
    except Exception as e:
        print(f"エラー: CSVファイル '{CSV_PATH}' の読み込みに失敗しました: {e}")
        return

    # 3. 動画IDをチャンクに分割
    chunks = [video_ids[i:i + CHUNK_SIZE] for i in range(0, len(video_ids), CHUNK_SIZE)]
    total_chunks = len(chunks)
    print(f"全 {len(video_ids)} 件の動画IDを、{CHUNK_SIZE} 件ずつの {total_chunks} 個のチャンクに分割しました。")

    # 4. YouTube APIサービスを構築
    youtube = build(API_SERVICE_NAME, API_VERSION, developerKey=API_KEY)

    # 5. 各チャンクを処理
    for i, chunk in enumerate(chunks, 1):
        chunk_file_path = os.path.join(OUTPUT_DIR, f"comments_20250709_{i}.csv")

        # 再開機能: 既に出力ファイルが存在すれば、このチャンクはスキップ
        if os.path.exists(chunk_file_path):
            print(f"[{i}/{total_chunks}] チャンク {i} は処理済みです。スキップします。 (ファイル: {chunk_file_path})")
            continue

        print(f"--- [{i}/{total_chunks}] チャンク {i} の処理を開始します ({len(chunk)}件の動画) ---")
        chunk_results = []
        all_videos_processed = True
        try:
            for j, video_id in enumerate(chunk, 1):
                print(f"  ({j}/{len(chunk)}) 動画ID '{video_id}' のコメントを取得中...")
                # fetch_comments_for_video は致命的なエラー以外は例外を発生させなくなった
                comments = fetch_comments_for_video(youtube, video_id)
                if comments:
                    chunk_results.extend(comments)
                    print(f"    -> {len(comments)} 件のコメントを取得しました。")
                time.sleep(0.5) # APIへの負荷軽減のための待機

        except HttpError as e:
            # APIキー無効やクォータ超過など、回復不能なエラーの場合
            all_videos_processed = False
            print(f"\nAPIの致命的なエラーが発生したため、処理を中断します。 (エラー詳細: {e})")
            print("APIキーが正しいか、APIクォータの上限に達していないか確認してください。")
            print("次回実行時には、このチャンクから処理が再開されます。")

        # チャンクの結果をCSVに保存 (ループが正常に完了した場合のみ)
        if all_videos_processed:
            if not chunk_results:
                print(f"チャンク {i} ではコメントが取得できませんでした。")
                # 空でもファイルを作成しておくことで、次回実行時にスキップされる
                pd.DataFrame([]).to_csv(chunk_file_path, index=False)
            else:
                df_chunk = pd.DataFrame(chunk_results)
                columns_order = [
                    "videoId", "parentId", "commentId", "isReply", "authorDisplayName",
                    "text", "likeCount", "publishedAt", "updatedAt", "authorChannelId"
                ]
                df_chunk = df_chunk.reindex(columns=columns_order)
                df_chunk.to_csv(chunk_file_path, index=False, encoding='utf-8-sig', escapechar='\\')
                print(f"チャンク {i} の結果 ({len(chunk_results)}件) を '{chunk_file_path}' に保存しました。")
        
        if not all_videos_processed:
            break # 致命的なエラーがあった場合は、次のチャンクに進まずに終了

    print("\nすべての処理が完了しました。")

if __name__ == "__main__":
    main()


"""

### 変更点と使い方

1.  **APIキーの設定**: スクリプト上部の `API_KEY` にご自身のキーを設定してください。
2.  **出力ディレクトリ**: `OUTPUT_DIR = "comment_chunks"` で指定された名前のフォルダが作成され、その中に `comments_chunk_1.csv`, `comments_chunk_2.csv`... という名前でファイルが保存されます。
3.  **チャンクサイズの調整**: `CHUNK_SIZE = 50` の数値を変更することで、1ファイルにまとめる動画の数を調整できます。APIクォータを考慮すると、50〜100程度がおすすめです。
4.  **実行と再開**:
    * スクリプトを実行すると、チャンク1から順に処理が始まります。
    * 途中でAPIエラーなどにより中断した場合でも、**再度同じスクリプトを実行するだけ**で、前回保存されなかったチャンクから自動的に処理を再開します。

### 分析のためにCSVを1つに結合する方法

全てのチャンクの取得が完了した後、分析のために1つのファイルにまとめたい場合は、以下の様な簡単なPythonコードで結合できます。

```python
import pandas as pd
import glob

# チャンクファイルが保存されているディレクトリ
chunk_dir = "comment_chunks"
# 結合後のファイル名
output_file = "all_comments_combined.csv"

# ディレクトリ内の全CSVファイルのパスを取得
csv_files = glob.glob(f"{chunk_dir}/comments_chunk_*.csv")
csv_files.sort() # ファイルを番号順にソート

# 各CSVを読み込んでリストに格納
df_list = [pd.read_csv(file) for file in csv_files]

# 全てのDataFrameを結合
combined_df = pd.concat(df_list, ignore_index=True)

# 1つのCSVファイルとして保存
combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"{len(csv_files)}個のファイルを結合し、{len(combined_df)}件のコメントを'{output_file}'に保存しました。")
"""