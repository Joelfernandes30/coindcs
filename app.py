from flask import Flask, render_template, jsonify
import requests
import numpy as np
import pandas as pd
import yfinance as yf
import ta
import joblib
from tensorflow.keras.models import load_model

app = Flask(__name__)


NEWSAPI_KEY = 'd3de19fb3c9745e7b93b3b23c533dda6'

@app.route('/')
def home():
    return render_template('index.html')
@app.route('/api/crypto')
def get_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'inr',
        'order': 'market_cap_desc',
        'per_page': 10,
        'page': 1,
        'sparkline': False
    }
    response = requests.get(url, params=params)
    return jsonify(response.json())
@app.route('/crypto/<symbol>')
def crypto_detail(symbol):
    try:
        # Ensure lowercase ID for CoinGecko
        coin_id = symbol.lower()

        # Fetch OHLC data
        ohlc_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
        params = {"vs_currency": "inr", "days": 7}
        ohlc_response = requests.get(ohlc_url, params=params)
        ohlc_response.raise_for_status()  # Raise exception for HTTP errors

        ohlc_data = ohlc_response.json()
        chart_data = []
        if ohlc_data:
            chart_data = [
                {"x": item[0], "o": item[1], "h": item[2], "l": item[3], "c": item[4]}
                for item in ohlc_data
            ]

        # Fetch news
        news_url = (
            f"https://newsapi.org/v2/everything?"
            f"q={coin_id}&language=en&sortBy=publishedAt&pageSize=1&apiKey={NEWSAPI_KEY}"
        )
        news_resp = requests.get(news_url)
        news_data = {}
        if news_resp.status_code == 200:
            news_json = news_resp.json()
            if news_json.get("articles"):
                art = news_json["articles"][0]
                news_data = {
                    "title": art.get("title"),
                    "description": art.get("description"),
                    "url": art.get("url"),
                    "publishedAt": art.get("publishedAt")
                }

        return render_template("crypto_detail.html",
                               symbol=coin_id,
                               chart_data=chart_data,
                               news=news_data)

    except requests.exceptions.RequestException as e:
        return f"Error fetching {symbol} data: {e}", 500
    except ValueError:
        return f"Error parsing {symbol} data", 500

@app.route('/coins/<symbol>')
def coin_page(symbol):
    # Fetch same OHLC data and stats
    coin_id = symbol.lower()
    ohlc_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
    params = {"vs_currency": "inr", "days": 7}
    ohlc_resp = requests.get(ohlc_url, params=params)
    chart_data = []
    if ohlc_resp.status_code == 200:
        ohlc_json = ohlc_resp.json()
        chart_data = [{"x": item[0], "o": item[1], "h": item[2], "l": item[3], "c": item[4]} for item in ohlc_json]

    return render_template("coin_page.html", symbol=coin_id, chart_data=chart_data)



#------------------mlprediction---------------------
def predict_crypto(symbol, model_path, scaler_path):
    model = load_model(model_path)
    scaler = joblib.load(scaler_path)

    btc = yf.download(symbol, period="400d", interval="1d")

    if isinstance(btc.columns, pd.MultiIndex):
        btc.columns = [col[0] for col in btc.columns]

    close = btc['Close'].squeeze()
    btc['rsi'] = ta.momentum.RSIIndicator(close).rsi()
    btc['ema_10'] = ta.trend.EMAIndicator(close, window=10).ema_indicator()
    btc['ema_50'] = ta.trend.EMAIndicator(close, window=50).ema_indicator()
    btc['ema_200'] = ta.trend.EMAIndicator(close, window=200).ema_indicator()
    btc['macd'] = ta.trend.MACD(close).macd()
    btc['roc'] = ta.momentum.ROCIndicator(close).roc()
    bb = ta.volatility.BollingerBands(close)
    btc['bollinger_high'] = bb.bollinger_hband()
    btc['bollinger_low'] = bb.bollinger_lband()
    btc['returns'] = close.pct_change()
    btc.dropna(inplace=True)

    features = [
        'rsi','ema_10','ema_50','ema_200','macd',
        'roc','returns','bollinger_high','bollinger_low'
    ]

    X = btc[features].values
    X_scaled = scaler.transform(X)

    TIME_STEPS = 30
    if len(X_scaled) < TIME_STEPS:
        return {
            "price": round(float(btc['Close'].iloc[-1]), 2),
            "suggestion": "HOLD 🤝 (Insufficient data)"
        }

    latest_seq = X_scaled[-TIME_STEPS:].reshape(1, TIME_STEPS, len(features))
    pred_class = np.argmax(model.predict(latest_seq), axis=1)[0]

    signal_map = {0: "SELL 🔻", 1: "HOLD 🤝", 2: "BUY 💹"}
    latest_price = round(float(btc['Close'].iloc[-1]), 2)

    return {
        "price": latest_price,
        "suggestion": signal_map[pred_class]
    }



@app.route('/api/predict_btc')
def predict_btc():
    result = predict_crypto(
        symbol="BTC-INR",
        model_path="models/lstm_btc_model.keras",
        scaler_path="models/scaler.pkl"
    )
    return jsonify(result)


@app.route('/api/predict_eth')
def predict_eth():
    result = predict_crypto(
        symbol="ETH-INR",
        model_path="models/lstm_eth_model.keras",
        scaler_path="models/eth_scaler.pkl"
    )
    return jsonify(result)




if __name__ == "__main__":
    app.run(debug=True)
