import os
import time
import pandas as pd

import google_auth_oauthlib.flow
import googleapiclient.errors

from googleapiclient.discovery import build

csv_path = "combined_20250719_690.csv"
df = pd.read_csv(csv_path)

if "id" not in df.columns:
    raise KeyError(f"'id' カラムが見つかりません。CSV カラム一覧: {df.columns.tolist()}")

video_ids = df["id"].dropna().astype(str).unique().tolist()
print(f"Found {len(video_ids)} unique video IDs:")


def chunk_list(lst, n):
    """リスト lst を n 件ずつに分割して返す"""
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

chunks = list(chunk_list(video_ids, 50))
for idx, chunk in enumerate(chunks, start=1):
    print(f"Chunk {idx}: size {len(chunk)} — {chunk[:3]} ... {chunk[-3:]}")


# -*- coding: utf-8 -*-

API_KEY = "AIzaSyBy8ojC53lVLyPS5zHl0WaTdcKJ7_zr-dM"
youtube = build(
    "youtube", "v3",
    developerKey=API_KEY
)

def info_tables(items):
    info_elements = []
    for info_thread in items:
        content_details = info_thread.get('contentDetails', {})
        statistics = info_thread.get('statistics', {})
        snippet = info_thread.get('snippet', {})

        info_elements.append({
            'id': info_thread.get('id'),
            'published at': snippet.get('publishedAt'),
            'channel Id': snippet.get('channelId'),
            'channelTitle': snippet.get('channelTitle'),
            'title': snippet.get('title'),
            'description': snippet.get('description'),
            'tags': snippet.get('tags', []),
            'thumbnailUrl': snippet.get('thumbnails', {}).get('high', {}).get('url'),
            'category Id': snippet.get('categoryId'),
            'view count': statistics.get('viewCount'),
            'like count': statistics.get('likeCount', 0),
            'comment count': statistics.get('commentCount', 0),
            'duration': content_details.get('duration'),
            'caption': content_details.get('caption'),
            'channelLabel': snippet.get('channelLabel', None), 
        })
    return info_elements

# ===== 既に作成済みの chunks を使って取得 =====
def fetch_videos_by_chunks(youtube, chunks, part="id,snippet,statistics,topicDetails,contentDetails", sleep_sec=0.0):
    """25行目までで作成した `chunks` をそのまま使って videos.list を叩く"""
    results = []
    for idx, chunk in enumerate(chunks, start=1):
        resp = youtube.videos().list(part=part, id=",".join(chunk)).execute()
        items = resp.get("items", [])
        results.extend(info_tables(items))
        if sleep_sec:
            time.sleep(sleep_sec)
    return pd.DataFrame(results)

# ===== 事前に作成した chunks を使って再取得 → CSV 保存 =====
def refetch_from_chunks(chunks, out_csv="refetched_20250719.csv"):
    outcome = fetch_videos_by_chunks(youtube, chunks)
    outcome.to_csv(out_csv, index=False)
    print(outcome.info())
    print(outcome.tail())
    print(f"Saved: {out_csv}")
    return outcome

if __name__ == "__main__":
    refetch_from_chunks(chunks, out_csv="refetched_20250719.csv")
