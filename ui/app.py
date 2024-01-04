import streamlit as st
import datetime


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

    # request


def analyze_youtube():
    global last_update_time, coin_dict

    st.title("Youtube")
    url = st.text_input("Enter the YouTube video URL (e.g., https://www.youtube.com/watch?v=i2RTXJqy1j8):").strip()
    button_clicked = st.button("Get Analysis!")

    if button_clicked:
        
        with st.spinner("Please wait, analyzing the video..."):
            st.warning("Only the coins that are in the top 250 by market capitalization are detected by the system.")
            #request



def __display_video_info(video_info):
    st.write("Title: ", video_info.metadata['title'])
    st.write("Account: ", video_info.metadata['author'])
    st.write("View Count: ", video_info.metadata['view_count'])
    st.write("Publish Date: ", video_info.metadata['publish_date'])
    st.write("Transcription: ", video_info.page_content.lower())


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

def influencer_comparison():
    st.title("Crypto Influencer Comparison")
    new_influencers = st.text_input("Update influencers (e.g cryptokemal, CoinBureau):")

    if st.button("Update Influencers") and new_influencers:
        if "," not in new_influencers:
            new_influencers_list = [new_influencers]
        else:
            new_influencers_list = new_influencers.split(',')
        new_influencers_list = [string.strip() for string in new_influencers_list]
        crypto_influencers = list(set(new_influencers_list))
        st.session_state.crypto_influencers_list = crypto_influencers.copy()
        st.write(st.session_state.crypto_influencers_list)

    #if st.button("Analyze"):
        # request
    return None


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
    
    main() # streamlit run app.py
    
    footer_html = """
        <div style="text-align:center; padding: 10px; border-top: 1px solid #d3d3d3;">
            <p style="font-size: 12px; color: #888;">CryptoSpotlight version 1.1.0. Data powered by CoinGecko</p>
        </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)