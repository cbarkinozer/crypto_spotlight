import streamlit as st
import snscrape.modules.twitter as sntwitter
import datetime
from langchain.document_loaders import YoutubeLoader
import requests
from textblob import TextBlob
import translators as ts
import utils
import time
from dotenv import load_dotenv
import googleapiclient.discovery
from googleapiclient.errors import HttpError
import os
import plotly.graph_objects as go
import pandas as pd

last_update_time = datetime.datetime.now() - datetime.timedelta(hours=23)
coin_dict = utils.coin_dict

def analyze_twitter():
    st.title("Twitter")
    st.warning("Our Twitter service is coming soon...")
    
    #username = st.text_input("Enter the username of the Twitter account (e.g @TestUser):")
    #username = username.replace("@","").strip()
    username = ""

    # Calculate the start and end timestamps for the 24-hour period
    now = datetime.datetime.now()
    end_time = now.strftime("%Y-%m-%d")  # today
    start_time = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")  # yesterday

    # Create a query string with the username and date range
    query = f"from:{username} since:{start_time} until:{end_time}"

    #button_clicked = st.button("Get Analysis!")

    #if button_clicked:
    #    tweets = []
    #    st.subheader("Tweets:")
    #    try:
    #        for tweet in sntwitter.TwitterSearchScraper(query).get_items():
    #            tweets.append(tweet.content)
    #            st.write(tweet)
    #            st.markdown("---")
    #    except Exception as e:
    #        st.error(f"Error fetching tweets: {e}")


def analyze_youtube():
    global last_update_time, coin_dict

    st.title("Youtube")
    url = st.text_input("Enter the YouTube video URL (e.g., https://www.youtube.com/watch?v=i2RTXJqy1j8):").strip()
    button_clicked = st.button("Get Analysis!")

    if button_clicked:
        loader = YoutubeLoader.from_youtube_url(url, add_video_info=True, language=["en", "tr"], translation="en")
        doc_list = loader.load()
        video_info = doc_list[0]

        current_time = datetime.datetime.now()
        __update_coin_list(current_time)

        text = video_info.page_content.lower()
        __display_video_info(video_info)

        with st.spinner("Please wait, analyzing the video..."):
            st.warning("Only the coins that are in the top 250 by market capitalization are detected by the system.")
            total_detected_coins, _ = __analyze_text(text, video_info)

            if not total_detected_coins:
                st.write("No coins detected.")


def __update_coin_list(current_time):
    global last_update_time, coin_dict

    time_difference = current_time - last_update_time
    if time_difference.total_seconds() >= 24 * 60 * 60:
        coin_dict = __get_coins()
        last_update_time = current_time


def __get_coins():
    url = f'https://api.coingecko.com/api/v3/coins/markets'
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


def __display_video_info(video_info):
    st.write("Title: ", video_info.metadata['title'])
    st.write("Account: ", video_info.metadata['author'])
    st.write("View Count: ", video_info.metadata['view_count'])
    st.write("Publish Date: ", video_info.metadata['publish_date'])
    st.write("Transcription: ", video_info.page_content.lower())


def __analyze_text(text, video_info):
    global coin_list

    total_detected_coins = []
    analysis_result_list = []
    chunk_size = 500

    progress_bar = st.progress(0)

    for i in range(0, len(text), chunk_size):
        progress_percentage = min(100, (i + chunk_size) / len(text) * 100)
        progress_fraction = progress_percentage / 100
        progress_bar.progress(progress_fraction)

        translated_chunk = ts.translate_text(text[i:i + chunk_size], translator="google", to_language="en").lower()
        
        detected_coins = [coin for coin in coin_dict.keys() if f' {coin} ' in translated_chunk]

        total_detected_coins.extend(detected_coins)

        if detected_coins:
            analysis_list = __analyze_text_chunks(translated_chunk, detected_coins)
            analysis_result_list.append(analysis_list)
    
    total_detected_coins = list(set(total_detected_coins))
    
    st.warning("Utilizing CoinGecko's free API, might take up to 2-3 minutes to finish.")
    for coin in total_detected_coins:
        percentage_change, _ = __get_coin_price_change(coin, video_info.metadata['publish_date'], datetime.datetime.now())
        if percentage_change == 0:
            while percentage_change == 0:
                time.sleep(60)
                percentage_change, _ = __get_coin_price_change(coin, video_info.metadata['publish_date'], datetime.datetime.now())
        else:
            time.sleep(5)
        color_change = 'green' if percentage_change > 0 else 'red'
        st.write(f"{coin}'s value change since then: <span style='color:{color_change}'>%{percentage_change}</span>", unsafe_allow_html=True)

    return total_detected_coins, analysis_result_list


def __analyze_text_chunks(text_chunk, detected_coins):
    analysis = TextBlob(text_chunk)
    
    if analysis.sentiment.polarity > 0:
        guess = "Bullish"
        color = "green"
    elif analysis.sentiment.polarity < 0:
        guess = "Bearish"
        color = "red"
    else:
        guess = "Neutral"
        color = "grey"
    
    analysis_list = []
    
    for coin in detected_coins:
        st.write("Text: \n",text_chunk)
        st.write("Detected Coin: ",coin)
        st.write(f"Detected guess: <span style='color:{color}'>{guess}</span>", unsafe_allow_html=True)
        analysis = utils.Analysis(text_chunk=text_chunk,coin=coin,guess=guess,color=color,influencer = None, date=None)
        analysis_list.append(analysis)
        st.markdown("---")
    return analysis_list


def __get_coin_price_change(coin_name, start_date, end_date):
    
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


def influencer_comparison():
    st.title("Crypto Influencer Comparison")
    crypto_influencers=["cryptokemal","CoinBureau"]
    new_influencers = st.text_input("Update influencers (e.g cryptokemal, CoinBureau):")
    
    if st.button("Update Influencers") and new_influencers:
        new_influencers_list = new_influencers.split(',')
        crypto_influencers = list(set([s.strip() for s in new_influencers_list]))

    st.write(crypto_influencers)                  
    if st.button("Analyze"):
        charted_coin_list, analysis_result_list = __get_influencer_data(crypto_influencers)
        for coin in charted_coin_list:
            start_date = str(datetime.datetime.now() - datetime.timedelta(days=90))
            end_date = datetime.datetime.now()
            _, prices = __get_coin_price_change(coin, start_date, end_date)
            analysis_results_by_coin = [analysis for analysis in analysis_result_list if analysis.coin == coin]
            __plot_coin_chart(coin,prices, analysis_results_by_coin)

def __plot_coin_chart(coin,prices,analysis_results_by_coin):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=list(range(1, len(prices) + 1)),
                                 open=[price['open'] for price in prices],
                                 high=[price['high'] for price in prices],
                                 low=[price['low'] for price in prices],
                                 close=[price['close'] for price in prices]))
    for analysis in analysis_results_by_coin:
        index = prices.index(analysis.date) + 1
        fig.add_trace(go.Scatter(x=[index], y=[analysis.price],
                                 mode='markers',
                                 marker=dict(color=analysis.color),
                                 text=analysis.text_chunk,
                                 name=f"{analysis.influencer}'s Analysis"))
    fig.update_layout(title=f'Candlestick Chart with Analysis for {coin}',
                      xaxis_title='Time',
                      yaxis_title='Price',
                      xaxis_rangeslider_visible=False)
    fig.show()  
    

def __get_influencer_data(crypto_influencers):
    api_key = os.getenv('API_KEY')
    for influencer_name in crypto_influencers:
        video_urls = get_youtube_videos(api_key, influencer_name, max_results=10)
        if video_urls == []:
            st.warning("Influencer named {influencer_name} not found, continuining.")
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
            total_detected_coins, analysis_result_list = __analyze_text(text, video_info)
            charted_coin_list.append(total_detected_coins)
            for analysis in analysis_result_list:
                analysis.influencer = channel
                analysis.date =  publish_date
        
        charted_coin_list = list(set(charted_coin_list))
        return charted_coin_list, analysis_result_list
    

def get_youtube_videos(api_key, username, max_results=10):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    try:
        # Get channel ID from the username
        channel_response = youtube.channels().list(
            part="id",
            forUsername=username
        ).execute()

        if not channel_response.get("items"):
            print(f"Channel with username '{username}' not found.")
            return []

        channel_id = channel_response["items"][0]["id"]

        # Get the last 10 videos from the channel
        videos_response = youtube.search().list(
            part="id",
            channelId=channel_id,
            order="date",
            type="video",
            maxResults=max_results
        ).execute()

        video_ids = [item["id"]["videoId"] for item in videos_response["items"]]

        # Get video details to extract URLs
        videos_details_response = youtube.videos().list(
            part="id,snippet",
            id=",".join(video_ids)
        ).execute()

        video_urls = ["https://www.youtube.com/watch?v=" + item["id"] for item in videos_details_response["items"]]
        return video_urls

    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred: {e.content}")
        return []


def main():
    st.write("Welcome to CryptoSpotlight. You can select a social media type bellow and get a content analysis for FREE.")
    st.write("This system is NOT an investment advice, also there may be errors in the system as well.")
    tabs = ["Youtube", "Twitter", "Influencer Comparison"]
    active_tab = st.radio("Choose your operation:", tabs)
    if active_tab == "Twitter":
        analyze_twitter()
    elif active_tab == "Youtube":
        analyze_youtube()
    elif active_tab == "Influencer Comparison":
        influencer_comparison()


if __name__ == "__main__":
    st.set_page_config(page_title='CryptoSpotlight', page_icon='page_icon.jpg', layout="centered", initial_sidebar_state="auto", menu_items=None)
    load_dotenv()
    try:
        main() # streamlit run app.py
    except Exception as e:
        st.error(e)
        print(e)
    footer_html = """
        <div style="text-align:center; padding: 10px; border-top: 1px solid #d3d3d3;">
            <p style="font-size: 12px; color: #888;">CryptoSpotlight version 1.1.0. Data powered by CoinGecko</p>
        </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)