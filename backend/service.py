import snscrape.modules.twitter as sntwitter
import datetime
from langchain.document_loaders import YoutubeLoader
import requests
from textblob import TextBlob
import translators as ts
import utils
import time
import os
from googleapiclient.discovery import build
import models

last_update_time = datetime.datetime.now() - datetime.timedelta(hours=23)
coin_dict = utils.coin_dict
crypto_influencers_list = []

async def analyze_twitter(username: str):
        
    username = username.replace("@","").strip()

    # Calculate the start and end timestamps for the 24-hour period
    now = datetime.datetime.now()
    end_time = now.strftime("%Y-%m-%d")  # today
    start_time = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")  # yesterday  

    # Create a query string with the username and date range
    query = f"from:{username} since:{start_time} until:{end_time}"

    tweets = []
    try:
        for tweet in sntwitter.TwitterSearchScraper(query).get_items():
            tweets.append(tweet.content)
    except Exception as e:
        print(f"Error fetching tweets: {e}")
    return tweets


async def analyze_youtube(url: str):
    global last_update_time, coin_dict

    loader = YoutubeLoader.from_youtube_url(url, add_video_info=True, language=["en", "tr"], translation="en")
    doc_list = loader.load()
    video_info = doc_list[0]

    current_time = datetime.datetime.now()
    await __update_coin_list(current_time)

    text = video_info.page_content.lower()

    total_detected_coins, analysis_result_list, coin_list = await __analyze_text(text, video_info)

    if not total_detected_coins:
        return "No coin is detected!", True
    
    youtube_analysis_response = models.AnalyzeYoutubeResponse(
        title=video_info.metadata['title'],
        author=video_info.metadata['author'],
        view_count=video_info.metadata['view_count'],
        publish_date=video_info.metadata['publish_date'],
        transcription=video_info.page_content.lower(),
        coin_names=total_detected_coins,
        analysis=analysis_result_list,
        coin_change=coin_list
        )

    return youtube_analysis_response, False

async def compare_influencers(influencer_list):
    charted_coin_list, analysis_result_list = await __get_influencer_data(influencer_list)
    for coin in charted_coin_list:
        start_date = str(datetime.datetime.now() - datetime.timedelta(days=90))
        end_date = datetime.datetime.now()
        _, prices = await __get_coin_price_change(coin, start_date, end_date)
        analysis_results_by_coin = [analysis for analysis in analysis_result_list if analysis.coin == coin]
    return None


async def __update_coin_list(current_time):
    print("Updating Coin List...")
    global last_update_time, coin_dict

    time_difference = current_time - last_update_time
    if time_difference.total_seconds() >= 24 * 60 * 60:
        coin_dict = __get_coins()
        last_update_time = current_time


async def __get_coins():
    print("Getting coins...")
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 500,
        'page': 1,
        'sparkline': False,
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        coin_dict = {}
        for coin in data:
            coin_dict[coin['name'].lower()] = coin['id']
        return coin_dict
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None


async def __analyze_text(text, video_info):
    print("Analyzing text...")
    global coin_list

    total_detected_coins = []
    analysis_result_list = []
    chunk_size = 500

    for i in range(0, len(text), chunk_size):

        translated_chunk = ts.translate_text(text[i:i + chunk_size], translator="google", to_language="en").lower()
        
        detected_coins = [coin for coin in coin_dict.keys() if f' {coin} ' in translated_chunk]

        total_detected_coins.extend(detected_coins)

        if detected_coins == []:
            continue
    
        analysis_list = await __analyze_text_chunks(translated_chunk, detected_coins)
        analysis_result_list.extend(analysis_list)
    

    total_detected_coins = list(set(total_detected_coins))
    coin_list = []
    for coin in total_detected_coins:
        percentage_change, _ = await __get_coin_price_change(coin, video_info.metadata['publish_date'], datetime.datetime.now())
        if percentage_change == 0:
            while percentage_change == 0:
                time.sleep(60)
                percentage_change, _ = await __get_coin_price_change(coin, video_info.metadata['publish_date'], datetime.datetime.now())
        else:
            time.sleep(5)
        coin = models.Coin(coin=coin,change_percent=percentage_change)
        coin_list.append(coin)
        

    return total_detected_coins, analysis_result_list, coin_list


async def __analyze_text_chunks(text_chunk, detected_coins):
    analysis = TextBlob(text_chunk)
    
    if analysis.sentiment.polarity > 0:
        guess = "Bullish"
    elif analysis.sentiment.polarity < 0:
        guess = "Bearish"
    else:
        guess = "Neutral"
    
    analysis_list = []
    
    for coin in detected_coins:
        analysis = models.Analysis(text_chunk=text_chunk,coin=coin,guess=guess)
        analysis_list.append(analysis)
    return analysis_list


async def __get_coin_price_change(coin_name, start_date, end_date):
    
    coin_id = coin_dict.get(coin_name)

    # Remove the time part from the date strings
    start_date = start_date.split()[0]
    end_date = str(end_date).split()[0]

    # Convert start_date and end_date to datetime objects
    start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_datetime = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    # Convert datetime objects to Unix timestamp
    start_timestamp = int(start_datetime.timestamp())
    end_timestamp = int(end_datetime.timestamp())

    # CoinGecko API endpoint for historical prices
    endpoint = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
    
    # Parameters for the API request
    params = {
        'vs_currency': 'usd',
        'from': start_timestamp,
        'to': end_timestamp,
    }

    # Send the API request
    response = requests.get(endpoint, params=params)
    data = response.json()

    if ('prices' in data and data['prices']==[]) or ('prices' not in data):
        return 0

    # Extract prices from the response data
    prices = data['prices']

    # Calculate percentage change
    start_price = prices[0][1]
    end_price = prices[-1][1]
    percentage_change = ((end_price - start_price) / start_price) * 100

    return percentage_change, prices


async def __get_influencer_data(crypto_influencers):
    api_key = os.getenv('API_KEY')
    for influencer_name in crypto_influencers:
        video_urls = await get_last_10_video_links(api_key, influencer_name, max_results=10)
        if video_urls == []:
            print("Influencer named {influencer_name} not found, continuining.")
            continue
        
        charted_coin_list = []

        for url in video_urls:
            loader = YoutubeLoader.from_youtube_url(url, add_video_info=True, language=["en", "tr"], translation="en")
            doc_list = loader.load()
            video_info = doc_list[0]
            channel = video_info.metadata['author']
            publish_date = video_info.metadata['publish_date']

            current_date = datetime.datetime.now()
            __update_coin_list(current_date)

            
            text = video_info.page_content.lower()
            total_detected_coins, analysis_result_list = await __analyze_text(text, video_info)
            charted_coin_list.append(total_detected_coins)
            for analysis in analysis_result_list:
                analysis.influencer = channel
                analysis.date =  publish_date
        
        charted_coin_list = list(set(charted_coin_list))
        return charted_coin_list, analysis_result_list

    
async def get_last_10_video_links(api_key, channel_name, max_results):
    channel_id = await get_youtube_channel_id(api_key, channel_name)

    youtube = build('youtube', 'v3', developerKey=api_key)

    # Get the last 10 videos from the channel
    videos_response = youtube.search().list(
        channelId=channel_id,
        type='video',
        part='id',
        order='date',
        maxResults=max_results
    ).execute()

    # Extract video IDs and construct video links
    video_links = ['https://www.youtube.com/watch?v=' + item['id']['videoId'] for item in videos_response['items']]
    return video_links


async def get_youtube_channel_id(api_key, channel_name):
    youtube = build('youtube', 'v3', developerKey=api_key)

    # Search for the channel by name
    search_response = youtube.search().list(
        q=channel_name,
        type='channel',
        part='id'
    ).execute()

    # Extract the channel ID
    channel_id = search_response['items'][0]['id']['channelId']
    return channel_id