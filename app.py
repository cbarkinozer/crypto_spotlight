import streamlit as st
import snscrape.modules.twitter as sntwitter
import datetime
import time

def twitter():
    st.title("Twitter")
    
    username = st.text_input("Enter the username of the Twitter account (e.g @TestUser):")
    username = username.replace("@","").strip()

    # Calculate the start and end timestamps for the 24-hour period
    now = datetime.datetime.now()
    end_time = now.strftime("%Y-%m-%d")  # today
    start_time = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")  # yesterday

    # Create a query string with the username and date range
    query = f"from:{username} since:{start_time} until:{end_time}"

    button_clicked = st.button("Get Tweets!")

    if button_clicked:
        tweets = []
        st.subheader("Tweets:")
        try:
            for tweet in sntwitter.TwitterSearchScraper(query).get_items():
                time.sleep(1)
                tweets.append(tweet.content)
                st.write(tweet)
                st.markdown("---")
        except Exception as e:
            st.error(f"Error fetching tweets: {e}")
    

def youtube():
    st.title("Youtube")

        

def main():
    tabs = ["Twitter", "Youtube"]
    active_tab = st.radio("İşleminizi seçin:", tabs)
    
    if active_tab == "Twitter":
        twitter()
    
    elif active_tab == "Youtube":
        youtube()
        

if __name__ == "__main__":
    main() # streamlit run app.py