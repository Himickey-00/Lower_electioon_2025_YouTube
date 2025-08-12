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

API_KEY = "AIzaSyCGDuqkF_U13tfUjtGPLkQRO2jukWosUN0"
youtube = build(
    "youtube", "v3",
    developerKey=API_KEY
)

party_channel_list = {   
    "自民党": "UCQVGAwZGA9jrH2XF7feK2xQ", # "@LDPchannel", 
    "立憲民主党": "UCghxR0rXQOH31bZwzTBY-yw", # "@立憲民主党-cdp", 
    "日本維新の会": "UCWt-OZ_PzMvXHijm9J87zKQ", #"@OishinJpn", 
    "国民民主党": "UCJc_jL0yOBGychLgiTCGtPw", # "@DPFPofficial", 
    "公明党": "UCn4qYPyxDdhvMn8-NIS0ydw", # "@Newkomeito_komei", 
    "れいわ新選組": "UCgIIlSmbGB5Tn9_zzYMCuNQ", # "@official_reiwa",
    "日本共産党": "UC_7GbtufUtR9l3pwvvn7Zlg", # "@jcpmovie",
    "参政党": "UCjrN-o1HlLk22qcauIKDtlQ", # "@sanseito-official",
    "日本保守党": "UCAFV09iwEkr9q-oSD6AtXNA", # "@hoshutojp",
    "社会民主党": "UCYrr5rY9SiPR4hrKMglap-g",  # "@shaminparty",
    "幸福実現党": "UCQct5yygDq1PBbpaePbdFdg", # "@hrpchannel",
    "チームみらい": "UCiMwbmcCSMORJ-85XWhStBw", # "@安野貴博"
    "再生の道": "UC9ykbjiUeYAgiuC9uiCmGJg" # "@The-Path-to-Rebirth",
    }

TV_channel_list = {
    "テレ東Biz": "UCkKVQ_GNjd8FbAuT6xDcWgg", # "@tvtokyobiz",
    "日テレNEWS": "UCuTAXTexrhetbOe3zgskJBQ", # "@ntv_news",
    "TBS NEWS DIG Powered by JNN": "UC6AG81pAkf6Lbi_1VC5NmPA", # "@tbsnewsdig",
    "ANNnewsCH": "UCGCZAYq5Xxojl_tSXcVJhiQ", # "@ANNnewsCH",
    "FNNプライムオンライン": "UCoQBJMzcwmXrRSHBFAlTsIw", # "@FNNnewsCH",
    "読売テレビニュース": "UCv7_krlrre3GQi79d4guxHQ", # "@ytv_news",
    "産経ニュース": "UC1zYGo1jIIjMVDTLL3dydow", # "@SankeiNews",
    }

Influential_Organizations_list = {
    "THE PAGE": "UC8XBizOfQBLUrUcv_9DHCog", # "@ThepageJp",
    "選挙ドットコムちゃんねる": "UCpdtHm6VFP_Qc-IDIsyLh1A", # "@thesenkyo",
    "Niconico News": "UC28hcmMG3TJv60Byo528VVg", # "@niconico_news",
    "NewsPicks /ニューズピックス": "UCfTnJmRQP79C4y_BMF_XrlA", # "@NewsPicks",
    "PIVOT 公式チャンネル": "UC8yHePe_RgUBE-waRWy6olw", # "@pivot00",
    "真相深入り! 虎ノ門ニュース": "UCuSPai4fj2nvwcCeyfq2sIA", # "@toranomonnews",
    "ReHacQ−リハック−【公式】": "UCG_oqDSlIYEspNpd2H4zWhw", # "@rehacq"
    "時事通信映像センター": "UCNLxBzguoGLqXWA8_BtHSHA", # "@時事通信映像センター",
    "共同通信  KYODO NEWS": "UCwJXtk_1CKlCrh7YJDP2uPw", # "KyodoNews",
    "ABEMA Prime #アベプラ【公式】": "UCB1dgsqLiEp57oDAyNV_vww" # "@prime_ABEMA"
    }

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
    "Ripbanwinkle": "3168UCC1Ue8b5oGMo1RQdDIv59KA", # "@ripbanwinkle"
    "WCJP-世界に誇る日本-": "UCI2V8_oyLILHLVw2KisgsjQ", # "@WCJP--mi8yh". #2023/11/01 に登録. チャンネル登録者数 26.7万人. 149 本の動画. 75,581,270 回視聴
    }

# Combine all channel dictionaries into one mapping
all_channel_lists = [party_channel_list, TV_channel_list, Influential_Organizations_list, Influential_Individuals_list]
all_channels = {}
for ch_dict in all_channel_lists:
    all_channels.update(ch_dict)


def get_channel_statistics(youtube):
    channel_stats = []
    for channel_label, channel_id in all_channels.items():
        request = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        )
        response = request.execute()
        if 'items' in response and response['items']:
            item = response['items'][0]
            stats = item['statistics']
            snippet = item['snippet']
            channel_stats.append({
                'channelLabel': channel_label,
                'channelId': item['id'],
                'title': snippet.get('title'),
                'description': snippet.get('description'),
                'customUrl': snippet.get('customUrl'),
                'publishedAt': snippet.get('publishedAt'),
                'viewCount': stats.get('viewCount'),
                'subscriberCount': stats.get('subscriberCount'),
                'videoCount': stats.get('videoCount')
            })
    return channel_stats


if __name__ == "__main__":

    # Fetch and save channel-level statistics
    channel_stats = get_channel_statistics(youtube)
    import pandas as pd
    pd.DataFrame(channel_stats).to_csv('channel_statistics_20250720.csv', index=False)


# AUTHじゃなぜか上手くいかん😭
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


# party_channel_list = {   
#     "自民党": "UCQVGAwZGA9jrH2XF7feK2xQ", # "@LDPchannel", # 12,3日前に参院選関連の動画を投稿し始めている
#     "立憲民主党": "UCghxR0rXQOH31bZwzTBY-yw", # "@立憲民主党-cdp", # 3週間前に参院選関連の動画を投稿し始めている
#     "日本維新の会": "UCWt-OZ_PzMvXHijm9J87zKQ", #"@OishinJpn", 
#     "国民民主党": "UCJc_jL0yOBGychLgiTCGtPw", # "@DPFPofficial", 
#     "公明党": "UCn4qYPyxDdhvMn8-NIS0ydw", # "@Newkomeito_komei", # 6日前に参院選関連の動画を投稿し始めている
#     "れいわ新選組": "UCgIIlSmbGB5Tn9_zzYMCuNQ", # "@official_reiwa",
#     "日本共産党": "UC_7GbtufUtR9l3pwvvn7Zlg", # "@jcpmovie",
#     "参政党": "UCjrN-o1HlLk22qcauIKDtlQ", # "@sanseito-official",
#     "日本保守党": "UCAFV09iwEkr9q-oSD6AtXNA", # "@hoshutojp",
#     "社会民主党": "UCYrr5rY9SiPR4hrKMglap-g",  # "@shaminparty",
#     "幸福実現党": "UCQct5yygDq1PBbpaePbdFdg", # "@hrpchannel",
#     "チームみらい": "UCiMwbmcCSMORJ-85XWhStBw", # "@安野貴博"
#     }

# TV_channel_list = {
#     "テレ東Biz": "UCkKVQ_GNjd8FbAuT6xDcWgg", # "@tvtokyobiz",
#     "日テレNEWS": "UCuTAXTexrhetbOe3zgskJBQ", # "@ntv_news",
#     "TBS NEWS DIG Powered by JNN": "UC6AG81pAkf6Lbi_1VC5NmPA", # "@tbsnewsdig",
#     "ANNnewsCH": "UCGCZAYq5Xxojl_tSXcVJhiQ", # "@ANNnewsCH",
#     "FNNプライムオンライン": "UCoQBJMzcwmXrRSHBFAlTsIw", # "@FNNnewsCH",
#     "読売テレビニュース": "UCv7_krlrre3GQi79d4guxHQ", # "@ytv_news"
#     }

# Influential_channel_list = {
#     "THE PAGE": "UC8XBizOfQBLUrUcv_9DHCog", # "@ThepageJp",
#     "中田敦彦のYouTube大学": "UCFo4kqllbcQ4nV83WCyraiw", # "@NKTofficial",
#     "選挙ドットコムチャンネル": "UCpdtHm6VFP_Qc-IDIsyLh1A", # "@thesenkyo",
#     "堀江貴文 ホリエモン": "UCXjTiSGclQLVVU83GVrRM4w", # "@takaponjp",
#     "Niconico News": "UC28hcmMG3TJv60Byo528VVg", # "@niconico_news",
#     "NewsPicks /ニューズピックス": "UCfTnJmRQP79C4y_BMF_XrlA", # "@NewsPicks",
#     "PIVOT 公式チャンネル": "UC8yHePe_RgUBE-waRWy6olw", # "@pivot00",
#     "真相深入り! 虎ノ門ニュース": "UCuSPai4fj2nvwcCeyfq2sIA", # "@toranomonnews",
#     "ReHacQ−リハック−【公式】": "UCG_oqDSlIYEspNpd2H4zWhw", # "@rehacq"
#     }