import datetime as dt
import pandas as pd
from pandas_datareader.fred import FredReader
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import requests
import yfinance as yf

### Get the Data
start_date = '2005-01-01'
end_date = dt.datetime.today().strftime("%Y-%m-%d")
recession_periods = [
    ("2008-01-01", "2009-06-01"), # Submortgage Crisis
    ("2020-04-01", "2020-06-01") # Covid Recession
]

## Macroeconomics Data
def chart_recession_periods(fig, recession_periods):
    for start_date, end_date in recession_periods:
        fig.add_vrect(x0=start_date, x1=end_date, fillcolor='grey', opacity=0.5, line_width=0)

def get_sp500_data():
    """
    This function will return the S&P 500 data.
    """
    sp500 = yf.download('^GSPC', start=start_date, end=end_date)['Adj Close']
    sp500 = pd.DataFrame(sp500)
    sp500.columns = ['S&P 500']
    sp500['Diff (%)'] = round(sp500.pct_change() * 100, 2)
    return sp500

def get_commodities_data():
    # Define the assets and the ticker you'd like to get HERE
    assets = {
        'Gold': 'GC=F',
        'Crude Oil': 'CL=F',
        'Brent Crude Oil': 'BZ=F',
        'Natural Gas': 'NG=F'
    }
    
    commodities_data = {}
    for asset_name, asset_ticker in assets.items():
        commodities_data[asset_name] = yf.download(asset_ticker, start=start_date, end=end_date)['Adj Close']

    commodities_data = pd.concat(commodities_data, axis=1)
    commodities_data.columns = assets.keys()
    return commodities_data

def get_treasury_yield_data():
    treasury_yield_10y = FredReader('DGS10', start_date).read()
    treasury_yield_2y = FredReader('DGS2', start_date).read()
    treasury_yield = pd.concat([treasury_yield_10y, treasury_yield_2y], axis=1)
    treasury_yield.columns = ['10Y', '2Y']
    treasury_yield['Spread'] = treasury_yield['10Y'] - treasury_yield['2Y']
    return treasury_yield

def get_ccc_data():
    return FredReader('BAMLH0A3HYC', start_date).read()

def get_vix_data():
    return yf.download('^VIX', start=start_date)['Adj Close']

## Financial Market Data
def get_eurtwd_data():
    finmind_url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanExchangeRate",
        "data_id": "EUR",
        "start_date": start_date,
    }

    try:
        response = requests.get(finmind_url, params=params)
        response.raise_for_status()
        data = response.json()['data']
        
        eurtwd_data = pd.DataFrame(data).set_index('date')
        eurtwd_data.index = pd.to_datetime(eurtwd_data.index)
        
        # Impute missing data (-1) with the previous value
        eurtwd_data.replace(-1, method="ffill", inplace=True)
        
        # Calculate the average of 'cash_sell' and 'cash_buy'
        eurtwd_data['TWDEUR'] = (eurtwd_data['cash_sell'] + eurtwd_data['cash_buy']) / 2
        
        # Calculate percentage change
        eurtwd_data['Diff (%)'] = round(eurtwd_data['TWDEUR'].pct_change() * 100, 2)
        
        # Drop rows with NaN values
        eurtwd_data.dropna(inplace=True)
        
        # Select relevant columns
        eurtwd = eurtwd_data[['TWDEUR', 'Diff (%)']]
        
        return eurtwd

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_eurusd_data():
    usd_eur = pd.DataFrame(yf.download('EUR=X', start=start_date, end=end_date)['Adj Close'])
    usd_eur.columns = ['USDEUR']
    usd_eur['USDEUR'] = round(usd_eur['USDEUR'], 2)
    usd_eur['Diff (%)'] = round(usd_eur['USDEUR'].pct_change() * 100, 3)
    return usd_eur

def get_crypto_data():
    # Define the assets and the ticker you'd like to get HERE
    crypto = {
        'Bitcoin': 'BTC-USD',
        'Ethereum': 'ETH-USD'
    }
    
    crypto_data = {}
    for crypto_name, crypto_ticker in crypto.items():
        crypto_data[crypto_name] = yf.download(crypto_ticker, start=start_date, end=end_date)['Adj Close']
        
    crypto_data = pd.concat(crypto_data, axis=1)
    crypto_data.columns = crypto.keys()
    return crypto_data

def get_stock_data():
    # Define the assets and the ticker you'd like to get HERE
    stocks = {
        'ASML': 'ASML',
        'Maersk': 'MAERSK-B.CO',
        'Airbnb': 'ABNB'
    }
    
    stocks_data = {}
    for stock_name, stock_ticker in stocks.items():
        stocks_data[stock_name] = yf.download(stock_ticker, start=start_date, end=end_date)['Adj Close']

    stocks_data = pd.concat(stocks_data, axis=1)
    stocks_data.columns = stocks_data.keys()
    return stocks_data

### Macro Page
## Charts

def make_treasury_chart():
    treasury_yield_data = get_treasury_yield_data()
    fig_treasury = px.line(treasury_yield_data, x=treasury_yield_data.index, y=['10Y', '2Y'], title='10Y 2Y Treasury Yield Spread')
    fig_treasury.add_bar(x=treasury_yield_data.index, y=treasury_yield_data['Spread'], name='Spread')

    chart_recession_periods(fig_treasury, recession_periods)
    return fig_treasury

def make_ccc_sp500_chart():
    sp500 = yf.download('^GSPC', start=start_date)['Adj Close']
    ccc = get_ccc_data()
    ccc_sp500 = pd.concat([ccc, sp500], axis=1)
    ccc_sp500.columns = ['CCC-Rated Bond Yield Spread', 'S&P 500']
    
    fig_ccc_sp500 = make_subplots(specs=[[{"secondary_y": True}]])
    # Add CCC-Rated Bond Yield Spread line plot (primary y-axis)
    fig_ccc_sp500.add_trace(
        go.Scatter(x=ccc_sp500.index, y=ccc_sp500['CCC-Rated Bond Yield Spread'], name='CCC'),
        secondary_y=False
    )

    # Add S&P 500 line plot (secondary y-axis)
    fig_ccc_sp500.add_trace(
        go.Scatter(x=ccc_sp500.index, y=ccc_sp500['S&P 500'], name='S&P 500'),
        secondary_y=True
    )

    # Update layout
    fig_ccc_sp500.update_layout(
        title='CCC-Rated Bond Yield Spread and S&P 500 Over Time',
        xaxis_title='Date',
        yaxis_title='CCC',
        yaxis2_title='S&P 500',
        template='plotly_dark'
    )
    
    chart_recession_periods(fig_ccc_sp500, recession_periods)

    return fig_ccc_sp500

def make_vix_chart():
    vix = get_vix_data()
    sp500 = yf.download('^GSPC', start=start_date)['Adj Close']
    vix_sp500 = pd.concat([vix, sp500], axis=1)
    vix_sp500.columns = ['VIX', 'S&P 500']
    
    fig_vix_sp500 = make_subplots(specs=[[{"secondary_y": True}]])
    # Add VIX line plot (primary y-axis)
    fig_vix_sp500.add_trace(
        go.Scatter(x=vix_sp500.index, y=vix_sp500['VIX'], name='VIX'),
        secondary_y=False
    )

    # Add S&P 500 line plot (secondary y-axis)
    fig_vix_sp500.add_trace(
        go.Scatter(x=vix_sp500.index, y=vix_sp500['S&P 500'], name='S&P 500'),
        secondary_y=True
    )

    # Update layout
    fig_vix_sp500.update_layout(
        title='VIX and S&P 500 Over Time',
        xaxis_title='Date',
        yaxis_title='VIX',
        yaxis2_title='S&P 500',
        yaxis=dict(
            title='VIX'
        ),
        yaxis2=dict(
            title='S&P 500',
            overlaying='y',
            side='right'
        )
    )
    
    chart_recession_periods(fig_vix_sp500, recession_periods)
    
    return fig_vix_sp500

def display_chart_mac():
    tab1_mac, tab2_mac, tab3_mac = st.tabs([
        "10Y 2Y Treasury Yield Spread", 
        "CCC-rated Bond Yield Spread and S&P 500",
        "Chicago Board Options Exchange Volatility Index (VIX)"
        ])

    # 1. Treasury yeild spread    
    with tab1_mac:
        tab1_fig = make_treasury_chart()
        st.plotly_chart(tab1_fig, theme="streamlit", use_container_width=True)
    
    # 2. CCC Bond Yield Spread and S&P 500    
    with tab2_mac:
        tab2_fig = make_ccc_sp500_chart()
        st.plotly_chart(tab2_fig, theme="streamlit", use_container_width=True)
        
    # 3. VIX and S&P 500
    with tab3_mac:
        tab3_fig = make_vix_chart()
        st.plotly_chart(tab3_fig, theme="streamlit", use_container_width=True)

def display_commodities_chart_mac():
    commodities_data = get_commodities_data()
    
    col1_com, col2_com = st.columns([3, 1])
    with col2_com:
        selected_commodities = st.selectbox(
        'Select the commodities to display:',
        commodities_data.columns
        )
        
        recent_commodities_data = commodities_data[[selected_commodities]].sort_values('Date', ascending=False).head(8)
        st.dataframe(recent_commodities_data)
        
    with col1_com:
        com_fig = px.line(commodities_data, x=commodities_data.index, y=selected_commodities, title=f'{selected_commodities} Prices Over Time')
        com_fig.update_traces(line=dict(color='green'))
        st.plotly_chart(com_fig)

### Financial Market Page
## Investment Portfolio

# Current prices of portfolio invested
def get_current_prices(investment):
    current_prices = {}
    for asset in investment['asset'].unique():
        ticker = yf.Ticker(asset)
        current_prices[asset] = ticker.history(period='1d')['Close'][0]
    
    return current_prices

# Get the portfolio value and return
def calculate_portfolio_value_and_return(investment, current_prices):
    investment['current_value'] = investment.apply(
        lambda row: row['amount_invested'] * (current_prices[row['asset']] / row['price_at_investment']), axis=1
    )
    portfolio_value = investment.groupby('date')['current_value'].sum().reset_index()
    portfolio_current_value = round(portfolio_value['current_value'].sum(), 2)

    initial_value = investment['amount_invested'].sum()
    return_rate = round(((portfolio_current_value - initial_value) / initial_value * 100), 2)
    return [portfolio_current_value, return_rate]


## Metrics
sp500 = get_sp500_data()
twdeur = get_eurtwd_data()
usdeur = get_eurusd_data()

def display_main_figures_fin():
    # Get investment portfolio value & return
    investment = pd.read_excel('Investment.xlsx', sheet_name='Investment', parse_dates=['date'])
    current_prices = get_current_prices(investment=investment)
    portfolio_value_and_return = calculate_portfolio_value_and_return(investment=investment, current_prices=current_prices)
    
    fin1, fin2, fin3, fin4, fin5, fin6 = st.columns(6)
    fin1.metric(label='Date: ', value=end_date)
    fin2.metric(label='Portfolio Value (USD)', value=portfolio_value_and_return[0])
    fin3.metric(label='Portfolio Return (%)', value=portfolio_value_and_return[1])
    fin4.metric(label='S&P 500', value=round(sp500['S&P 500'][-1], 2), delta=f"{sp500['Diff (%)'][-1]}"+"%")
    fin5.metric(label='USD / EUR', value=usdeur['USDEUR'][-1], delta=f"{usdeur['Diff (%)'][-1]}"+"%")
    fin6.metric(label='TWD / EUR', value=twdeur['TWDEUR'][-1], delta=f"{twdeur['Diff (%)'][-1]}"+"%")

## Charts
def display_stock_chart_fin():
    stock_data = get_stock_data()
    
    col1_stock, col2_stock = st.columns([3, 1])
    with col2_stock:
        # Select which stock prices to show
        selected_stock = st.selectbox(
        'Select the stock to display:',
        stock_data.columns
        )
        
        recent_stock_data = stock_data[[selected_stock]].sort_values('Date', ascending=False).head(8)
        st.dataframe(recent_stock_data)                
        
    with col1_stock:
        stock_fig = px.line(stock_data, x=stock_data.index, y=selected_stock, title=f'{selected_stock} Stock Prices Over Time')
        st.plotly_chart(stock_fig)

def display_crypto_chart_fin():
    crypto_data = get_crypto_data()
    
    col_1_crypto, col_2_crypto = st.columns([3, 1])
    with col_2_crypto:
        selected_crypto = st.selectbox(
        'Select the crypto to display:',
        crypto_data.columns
        )
        
        recent_crypto_data = crypto_data[[selected_crypto]].sort_values('Date', ascending=False).head(8)
        st.dataframe(recent_crypto_data)
    
    with col_1_crypto:
        crypto_fig = px.line(crypto_data, x=crypto_data.index, y=selected_crypto, title=f'{selected_crypto} Prices Over Time')
        crypto_fig.update_traces(line=dict(color='yellow'))
        st.plotly_chart(crypto_fig)

### Page Configuration
def macrofin_page_config():
    st.set_page_config(
        page_title="Macroeconomics & Financial Market Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'About': 'Type the introduction of the page.'
        }
    )

## Page Sidebar and Main Page
def macrofin_page_layout():
    with st.sidebar:
        st.title("Macroeconomics & Financial Market Dashboard")
        page_option = st.selectbox(
            'Sections:',
            ('Financial Market', 'Macroeconomics')
        )
        container = st.container(border=True)
        container.write(
            "An interactive dashboard that allows you to track the asset prices, your investment portfolio, and some key indicators of financial markets. 📈🌎"
        )
        
        col1_contact, col2_contact = st.columns(2)
        with col1_contact:
            st.link_button("Source Code", "https://github.com/yrwang0913")
        
        with col2_contact:
            st.link_button("Contact Me", "https://www.linkedin.com/in/yrwang0913/")

    if page_option == 'Financial Market':
        st.subheader('Financial Market Indicators')
        display_main_figures_fin()
        display_stock_chart_fin()
        display_crypto_chart_fin()

    else:
        st.subheader('Macroeconomics Indicators')
        display_commodities_chart_mac()
        display_chart_mac()

### Page Layout
def main():
    
    ## Page Config
    macrofin_page_config()
    
    ## Sidebar
    macrofin_page_layout()


### Run the code
if __name__ == '__main__':
    main()
