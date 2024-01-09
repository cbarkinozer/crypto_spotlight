import streamlit as st
import datetime
import plotly.graph_objects as go
import requests
import pandas as pd
import pandas_ta as ta

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
    st.session_state.url = st.text_input("Enter the YouTube video URL (e.g., https://www.youtube.com/watch?v=i2RTXJqy1j8):").strip()
    button_clicked = st.button("Get Analysis!")

    if button_clicked:
        with st.spinner("Please wait, analyzing the video..."):
            st.warning("Only the coins that are in the top 250 by market capitalization are detected by the system.")
            url = 'http://localhost:8000/analyze_youtube'
            payload = {'url': st.session_state.url}
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                    json_data = response.json()
                    st.write(json_data)
            

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

    if st.button("Analyze"):
        url = 'http://127.0.0.1:8000/influencer_comparison'
        params = {'influencers': 'BuCoinNedir'}
        files = {'video_count': (None, '2')} 
        try:    
            with st.spinner("Please wait, analyzing the video..."):
                st.warning("It might take 2 to 20 minutes depending on influencer and video count.")
                response = requests.post(url, params=params, files=files)
                if response.status_code == 200:
                    json_data = response.json()

                    # Accessing the value of analysis_results_by_coin
                    coin = json_data.get("coin", [])
                    prices = json_data.get("prices", [])
                    analysis_results_by_coin = json_data.get("analysis_results_by_coin", [])
                    
                    for _ in coin:
                        fig = __plot_coin_chart(coin=coin,prices=prices,analysis_results_by_coin=analysis_results_by_coin)
                        st.plotly_chart(fig)
        except requests.exceptions.RequestException as e:
            st.error(f"An error occurred: {e}")

def technical_analysis():
    st.title("Coin Technical Analyzer")
    st.write("Do not forget that there might be error in these automated analysis.")
    st.write("Everyone analyze different please do your own research.")
    st.write("This is NOT a investment advice.")
    
    coin_name = st.text_input("Enter a coin that is in the top 250 by marketcap:")
    
    if st.button("Analyze"):
        url = 'http://127.0.0.1:8000/technical_analysis'
        files = {'coin_name': (None, coin_name)} 
        try:    
            with st.spinner("Please wait, analyzing the coin..."):
                st.warning("It might take couple of minutes to analyze.")
                response = requests.post(url, files=files)
                if response.status_code == 200:
                    json_data = response.json()

                    # Accessing the value of analysis_results_by_coin
                    symbol = json_data.get("symbol", None)
                    timestamp = json_data.get("timestamp", None)
                    open = json_data.get("open", None)
                    high = json_data.get("high", None)
                    low = json_data.get("low", None)
                    close = json_data.get("close", None)
                    
                    data = pd.DataFrame({
                        'timestamp': timestamp,
                        'open': open,
                        'high': high,
                        'low': low,
                        'close': close
                    })
                
                    # Calculate Exponential Moving Averages (EMAs)
                    data['ema_short'] = ta.ema(data['close'], length=9)
                    data['ema_long'] = ta.ema(data['close'], length=21)
                    # Generate signals based on EMA crossover
                    data['signal'] = ta.crossover(data['ema_short'], data['ema_long'])
                    # Create candlestick chart
                    fig = go.Figure(data=[go.Candlestick(x=data['timestamp'],
                                                        open=data['open'],
                                                        high=data['high'],
                                                        low=data['low'],
                                                        close=data['close'])])
                    # Add EMA indicators
                    fig.add_trace(go.Scatter(x=data['timestamp'],
                                            y=data['ema_short'],
                                            mode='lines',
                                            name='Short EMA'))
                    fig.add_trace(go.Scatter(x=data['timestamp'],
                                            y=data['ema_long'],
                                            mode='lines',
                                            name='Long EMA'))
                    # Add Buy/Sell signals
                    buy_signals = data[data['signal'] == 1]
                    sell_signals = data[data['signal'] == -1]
                    fig.add_trace(go.Scatter(x=buy_signals['timestamp'],
                                            y=buy_signals['close'],
                                            mode='markers',
                                            marker=dict(color='green', size=10),
                                            name='Buy Signal'))
                    fig.add_trace(go.Scatter(x=sell_signals['timestamp'],
                                            y=sell_signals['close'],
                                            mode='markers',
                                            marker=dict(color='red', size=10),
                                            name='Sell Signal'))
                    # Customize the chart
                    fig.update_layout(title=f'{symbol.capitalize()} Candlestick Chart with Trend-Following Strategy',
                                    xaxis_title='Date',
                                    yaxis_title='Price (USD)',
                                    xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig)
        except requests.exceptions.RequestException as e:
            st.error(f"An error occurred: {e}")


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
    return fig 


def main():
    st.write("Welcome to CryptoSpotlight. You can select a social media type bellow and get a content analysis for FREE.")
    st.write("This system is NOT an investment advice, also there may be errors in the system as well.")
    tabs = ["Youtube", "Twitter", "Influencer Comparison", "Technical Analysis"]
    active_tab = st.radio("Choose your operation:", tabs)
    if active_tab == "Twitter":
        analyze_twitter()
    elif active_tab == "Youtube":
        analyze_youtube()
    elif active_tab == "Influencer Comparison":
        influencer_comparison()
    elif active_tab == "Technical Analysis":
        technical_analysis()


if __name__ == "__main__":
    st.set_page_config(page_title='CryptoSpotlight', page_icon='page_icon.jpg', layout="centered", initial_sidebar_state="auto", menu_items=None)
    
    main() # streamlit run app.py
    
    footer_html = """
        <div style="text-align:center; padding: 10px; border-top: 1px solid #d3d3d3;">
            <p style="font-size: 12px; color: #888;">CryptoSpotlight version 1.1.0. Data powered by CoinGecko</p>
        </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)