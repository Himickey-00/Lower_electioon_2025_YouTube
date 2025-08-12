import pandas as pd
import time

# -*- coding: utf-8 -*-

# Sample Python code for youtube.search.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python

import os

import google_auth_oauthlib.flow
import googleapiclient.errors

from googleapiclient.discovery import build

API_KEY = "AIzaSyDp_KpERCSioGswNbHlCXmqMrtWiK8XIik"
youtube = build(
    "youtube", "v3",
    developerKey=API_KEY
)

Influential_Individuals_list = {
    "中田敦彦のYouTube大学": "UCFo4kqllbcQ4nV83WCyraiw", # "@NKTofficial",
    "高須幹弥（高須クリニック）": "UCwywumWHI4_hQtZpJwsC8cw", # "@takasumikiya",
    "堀江貴文 ホリエモン": "UCXjTiSGclQLVVU83GVrRM4w", # "@takaponjp",
    "たまきチャンネル": "UCLJNZ7osIjNix4bbkM-rj5w", # "@tamaki-channel",
    "立花孝志": "UC80FWuvIAtY-TRtYuDocfUw", # "@chnhk6055"
    "石丸伸二と日本を動かそう": "UCX8xD9LlHOZf0dF7yo9mFkw", # "@michas140shinri"
    "高橋洋一チャンネル": "UCECfnRv8lSbn90zCAJWC7cg", # "@takahashi_yoichi"
    "撮って出しニュース": "UCBKn5J5o01uBYzwuC7HnUbQ", # "@soocnews"
    "石川典行チャンネル": "UCL9KXuGkAt5qCfUlMrJayMQ", # "@noriyukiradio"
    "Ripbanwinkle": "UCC1Ue8b5oGMo1RQdDIv59KA" # "@ripbanwinkle3168"
}

# Combine all channel dictionaries into one mapping
all_channel_lists = [Influential_Individuals_list]
all_channels = {}
for ch_dict in all_channel_lists:
    all_channels.update(ch_dict)


def get_all_info(youtube):
    info_threads = []
    max_results = 3000
    seen_video_ids = set()

    for channel_label, channel_id in all_channels.items():
        next_page_token = None
        total_results = 0

        while total_results < max_results:
            # Use the search endpoint to find video IDs for this channel
            search_request = youtube.search().list(
                part="id,snippet",
                maxResults=50,
                order="viewCount",
                publishedAfter="2025-07-02T00:00:00+09:00",
                publishedBefore="2025-07-20T23:59:00+09:00",
                channelId=channel_id,
                regionCode="JP",
                relevanceLanguage="ja",
                safeSearch="none",
                type="video",
                videoDimension="2d",
                pageToken=next_page_token
            )
            search_response = search_request.execute()

            # Extract unique video IDs
            video_ids = [
                item['id']['videoId']
                for item in search_response['items']
                if item['id'].get('videoId') and item['id']['videoId'] not in seen_video_ids
            ]
            if not video_ids:
                break
            seen_video_ids.update(video_ids)

            # Fetch detailed video info
            video_request = youtube.videos().list(
                part="id,snippet,statistics,topicDetails,contentDetails",
                id=",".join(video_ids)
            )
            video_responses = video_request.execute()

            # Annotate each item with channel_label and collect
            for item in video_responses['items']:
                item['snippet']['channelLabel'] = channel_label
            info_threads.extend(video_responses['items'])
            total_results += len(video_responses['items'])
            next_page_token = search_response.get('nextPageToken')
            if not next_page_token:
                break

    # Return up to max_results videos across all channels
    return info_threads[:max_results]



def info_tables(info_threads):
    info_elements = []
    
    for info_thread in info_threads:
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
            'channelLabel': snippet.get('channelLabel'),
        })
        
    return info_elements


def create_info_tebles(youtube):
    info_threads = get_all_info(youtube)
    info_elements = info_tables(info_threads)

    # Convert lists of video infomation to DataFrame
    outcome = pd.DataFrame(info_elements)
    
    return outcome


if __name__ == "__main__":
    # youtube = authenticate_youtube_service()
    outcome = create_info_tebles(youtube)

    # Save info table to CSV file
    outcome.to_csv('Videos_InfluentialIndividuals_rightbefore.csv', index=False)

    # Print summary
    print(outcome.info())
    print(outcome.tail())

# Koike: UCy7aH7KKlIpjX-9aHFfFRSA
# Ishimaru: UCidQ51J5ysCWeGBnLuNvnhQ
# Renho: UCeigzVkpXmZ_t79PBDjh4fQ
# Tamogami: UCwvtbgfEiyGG4VqojoePuEw
# Anno: UCiMwbmcCSMORJ-85XWhStBw


# def authenticate_youtube_service():
#     # Disable OAuthlib's HTTPS verification when running locally.
#     # *DO NOT* leave this option enabled in production.
#     os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

#     api_service_name = "youtube"
#     api_version = "v3"
#     client_secrets_file = "CLIENT_SECRET_FILE.json"

#     scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
#     flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
#         client_secrets_file, scopes)
#     credentials = flow.run_local_server()
#     youtube = googleapiclient.discovery.build(
#         api_service_name, api_version, credentials=credentials)
#     return youtube

# scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
# # API_KEY = 'AIzaSyDSOJklOefyaepLGxXRTaJ-5NaLTbydm08'

