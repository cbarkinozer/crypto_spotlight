import streamlit as st
import snscrape.modules.twitter as sntwitter
import datetime
from langchain.document_loaders import YoutubeLoader
import requests
from textblob import TextBlob
import translators as ts

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
    url = st.text_input("Enter the url of the Youtube video (e.g https://www.youtube.com/watch?v=i2RTXJqy1j8):").strip()
    button_clicked = st.button("Get Analysis!")
    if button_clicked:
        
            loader = YoutubeLoader.from_youtube_url(
                url, add_video_info=True,
                language=["en","tr"],
                translation="en",
            )
            doc_list = loader.load()
            
            current_time = datetime.datetime.now()
            # Check if 24 hours have passed since the last update
            time_difference = current_time - last_update_time
            if time_difference.total_seconds() >= 24 * 60 * 60:
                coin_list = __get_top_crypto_names()
                last_update_time = current_time
            
            text = doc_list[0].page_content.lower()
            
            st.write("Title: ", doc_list[0].metadata['title'])
            st.write("Account: ", doc_list[0].metadata['author'])
            st.write("View Count: ",doc_list[0].metadata['view_count'])
            st.write("Publish Date: ", doc_list[0].metadata['publish_date'])
            st.write("Transcription : ", text)
            

            progress_bar = st.progress(0)

            with st.spinner("Please wait, analyzing the video..."):
                total_detected_coins = []
                chunk_size = 500

                for i in range(0, len(text), chunk_size):
                    progress_percentage = min(100, (i + chunk_size) / len(text) * 100)
                    progress_fraction = progress_percentage / 100  # Convert to fraction
                    progress_bar.progress(progress_fraction)

                    translated_chunk = ts.translate_text(text[i:i + chunk_size], translator="bing", to_language="en").lower()
                    #print("TRANSLATED CHUNK: ", translated_chunk)
                    detected_coins = []
                    for coin in coin_list:
                        if f' {coin} ' in translated_chunk:
                            detected_coins.append(coin)
                    total_detected_coins.extend(detected_coins)

                    if detected_coins:
                        __analyze_text_chunks(translated_chunk, detected_coins)

                if not total_detected_coins:
                    st.write("No coins detected.")

            

            
        
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

    st.write("Text: ",text_chunk)
    st.write("Detected Coins: ",detected_coins)
    st.write(f"Detected guess: <span style='color:{color}'>{guess}</span>", unsafe_allow_html=True)



def __get_top_crypto_names():
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
        coin_names = [coin['name'].lower() for coin in data]
        coin_names.remove('just')
        return coin_names
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None

        

def main():
    tabs = ["Youtube", "Twitter"]
    active_tab = st.radio("Choose your operation:", tabs)
    
    if active_tab == "Twitter":
        analyze_twitter()
    
    elif active_tab == "Youtube":
        analyze_youtube()
        

if __name__ == "__main__":
    main() # streamlit run app.py
    
    footer_html = """
        <div style="text-align:center; padding: 10px; border-top: 1px solid #d3d3d3;">
            <p style="font-size: 12px; color: #888;">Data powered by <a href="https://www.coingecko.com/" target="_blank" style="text-decoration: none; color: #6f6f6f;">CoinGecko</a></p>
        </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)