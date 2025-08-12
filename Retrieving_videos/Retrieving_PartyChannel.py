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

party_channel_list = {   
    "自民党": "UCQVGAwZGA9jrH2XF7feK2xQ", # "@LDPchannel", # 12,3日前に参院選関連の動画を投稿し始めている
    "立憲民主党": "UCghxR0rXQOH31bZwzTBY-yw", # "@立憲民主党-cdp", # 3週間前に参院選関連の動画を投稿し始めている
    "日本維新の会": "UCWt-OZ_PzMvXHijm9J87zKQ", #"@OishinJpn", 
    "国民民主党": "UCJc_jL0yOBGychLgiTCGtPw", # "@DPFPofficial", 
    "公明党": "UCn4qYPyxDdhvMn8-NIS0ydw", # "@Newkomeito_komei", # 6日前に参院選関連の動画を投稿し始めている
    "れいわ新選組": "UCgIIlSmbGB5Tn9_zzYMCuNQ", # "@official_reiwa",
    "日本共産党": "UC_7GbtufUtR9l3pwvvn7Zlg", # "@jcpmovie",
    "参政党": "UCjrN-o1HlLk22qcauIKDtlQ", # "@sanseito-official",
    "日本保守党": "UCAFV09iwEkr9q-oSD6AtXNA", # "@hoshutojp",
    "社会民主党": "UCYrr5rY9SiPR4hrKMglap-g",  # "@shaminparty",
    "幸福実現党": "UCQct5yygDq1PBbpaePbdFdg", # "@hrpchannel",
    "チームみらい": "UCiMwbmcCSMORJ-85XWhStBw", # "@安野貴博"
    "再生の道": "UC9ykbjiUeYAgiuC9uiCmGJg" # "@The-Path-to-Rebirth",
    }

# Combine all channel dictionaries into one mapping
all_channel_lists = [party_channel_list]
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
    
    # Extract necessary infomation
    for info_thread in info_threads:
         info_elements.append({
            'id': info_thread['id'],
            'published at': info_thread['snippet']['publishedAt'],
            'channel Id': info_thread['snippet']['channelId'],
            'channelTitle': info_thread['snippet']['channelTitle'],
            'title': info_thread['snippet']['title'],
            'description': info_thread['snippet']['description'],
            'tags': info_thread['snippet'].get('tags',[]),
            'thumbnailUrl': info_thread['snippet']['thumbnails'].get('high', {}).get('url'),
            'category Id': info_thread['snippet']['categoryId'],
            'view count': info_thread['statistics']['viewCount'],
            'like count': info_thread['statistics'].get('likeCount',0),
            'comment count': info_thread['statistics'].get('commentCount',0),
            'duration': info_thread['contentDetails']['duration'],
            'caption': info_thread['contentDetails']['caption'],
            'channelLabel': info_thread['snippet'].get('channelLabel'),
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
    outcome.to_csv('Videos_PartyChannel_rightbefore.csv', index=False)

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

