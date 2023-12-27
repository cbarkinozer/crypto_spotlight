import streamlit as st
import snscrape.modules.twitter as sntwitter
import datetime
from langchain.document_loaders import YoutubeLoader
import requests
from textblob import TextBlob

last_update_time = datetime.datetime.now() - datetime.timedelta(hours=24)
coin_list = []

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
    global last_update_time
    global coin_list

    st.title("Youtube")
    url = st.text_input("Enter the username of the Youtube account (e.g https://www.youtube.com/watch?v=i2RTXJqy1j8):").strip()
    button_clicked = st.button("Get Analysis!")
    if button_clicked:
        try:
            loader = YoutubeLoader.from_youtube_url(
                url, add_video_info=True,
                language=["en", "tr"],
                translation="en",
            )
            doc_list = loader.load()
            st.write("[DEBUG]",doc_list)
            current_time = datetime.datetime.now()

            # Check if 24 hours have passed since the last update
            time_difference = current_time - last_update_time
            if time_difference.total_seconds() >= 24 * 60 * 60:
                coin_list = get_top_crypto_names()
                last_update_time = current_time
            
            detected_coins = [coin for coin in coin_list if any(coin in doc.page_content for doc in doc_list)]

            
            analysis = TextBlob(doc_list[0].page_content)
    
            # Classify polarity as positive, negative, or neutral
            if analysis.sentiment.polarity > 0:
                guess = "Bullish"
                color = "green"
            elif analysis.sentiment.polarity < 0:
                guess = "Bearish"
                color = "red"
            else:
                guess = "Neutral"
                color = "grey"

            st.write("Detected Coins: ",detected_coins)
            st.write("[DEBUG] Coins:",coin_list)
            st.write(f"Detected guess: <span style='color:{color}'>{guess}</span>", unsafe_allow_html=True)
        except Exception as e:
            st.write(str(e))
    


def get_top_crypto_names():
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
        coin_names = [coin['name'] for coin in data]
        return coin_names
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None

        

def main():
    tabs = ["Twitter", "Youtube"]
    active_tab = st.radio("İşleminizi seçin:", tabs)
    
    if active_tab == "Twitter":
        analyze_twitter()
    
    elif active_tab == "Youtube":
        analyze_youtube()
        

if __name__ == "__main__":
    main() # streamlit run app.py