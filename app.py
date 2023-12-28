import streamlit as st
import snscrape.modules.twitter as sntwitter
import datetime
from langchain.document_loaders import YoutubeLoader
import requests
from textblob import TextBlob
import translators as ts
import utils

last_update_time = datetime.datetime.now() - datetime.timedelta(hours=23)
coin_dict = utils.coin_dict

def analyze_twitter():
    st.title("Twitter")
    
    username = st.text_input("Enter the username of the Twitter account (e.g @TestUser):")
    username = username.replace("@","").strip()

    # Calculate the start and end timestamps for the 24-hour period
    now = datetime.datetime.now()
    end_time = now.strftime("%Y-%m-%d")  # today
    start_time = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")  # yesterday

    # Create a query string with the username and date range
    query = f"from:{username} since:{start_time} until:{end_time}"

    button_clicked = st.button("Get Analysis!")

    if button_clicked:
        tweets = []
        st.subheader("Tweets:")
        try:
            for tweet in sntwitter.TwitterSearchScraper(query).get_items():
                tweets.append(tweet.content)
                st.write(tweet)
                st.markdown("---")
        except Exception as e:
            st.error(f"Error fetching tweets: {e}")
    

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
            total_detected_coins = __analyze_text(text, video_info)

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
        print(coin_dict)
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
    chunk_size = 500

    progress_bar = st.progress(0)

    for i in range(0, len(text), chunk_size):
        progress_percentage = min(100, (i + chunk_size) / len(text) * 100)
        progress_fraction = progress_percentage / 100
        progress_bar.progress(progress_fraction)

        translated_chunk = ts.translate_text(text[i:i + chunk_size], translator="bing", to_language="en").lower()
        
        detected_coins = [coin for coin in coin_dict.keys() if f' {coin}' in translated_chunk]

        total_detected_coins.extend(detected_coins)

        if detected_coins:
            __analyze_text_chunks(translated_chunk, detected_coins, video_info)

    return total_detected_coins

        
def __analyze_text_chunks(text_chunk, detected_coins, video_info):
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

    for coin in detected_coins:
        percentage_change = get_coin_price_change(coin, video_info.metadata['publish_date'],datetime.datetime.now())
        if percentage_change == 0:
            continue
        st.write("Text: \n",text_chunk)
        st.write("Detected Coin: ",coin)
        st.write(f"Detected guess: <span style='color:{color}'>{guess}</span>", unsafe_allow_html=True)
        color_change = 'green' if percentage_change > 0 else 'red'
        st.write(f"Coin's value change since then: <span style='color:{color_change}'>%{percentage_change}</span>", unsafe_allow_html=True)

def get_coin_price_change(coin_name, start_date, end_date):
    
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
    print(data)

    if ('prices' in data and data['prices']==[]) or ('prices' not in data):
        return 0

    # Extract prices from the response data
    prices = data['prices']

    # Calculate percentage change
    start_price = prices[0][1]
    end_price = prices[-1][1]
    percentage_change = ((end_price - start_price) / start_price) * 100

    return percentage_change


def main():
    tabs = ["Youtube", "Twitter"]
    active_tab = st.radio("Choose your operation:", tabs)
    
    if active_tab == "Twitter":
        analyze_twitter()
    
    elif active_tab == "Youtube":
        analyze_youtube()
        

if __name__ == "__main__":

    # just, ordi, gas

    main() # streamlit run app.py
    
    footer_html = """
        <div style="text-align:center; padding: 10px; border-top: 1px solid #d3d3d3;">
            <p style="font-size: 12px; color: #888;">Data powered by <a href="https://www.coingecko.com/" target="_blank" style="text-decoration: none; color: #6f6f6f;">CoinGecko</a></p>
        </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)