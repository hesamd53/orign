from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Bybit API keys
BYBIT_API_KEY = "P3tnlImbl9o5NMDsX8"
BYBIT_API_SECRET = "PoyuL1C79si35DGqquC3CNUHl3yUzvZ1MCvM"
BYBIT_API_URL = "https://api.bybit.com"

# Webhook listener
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    # Extract signal data
    signal_type = data.get("signal")  # Buy or Sell
    entry_price = float(data.get("price"))
    stop_loss = float(data.get("stop_loss"))
    take_profit = float(data.get("take_profit"))
    symbol = data.get("symbol", "BTCUSDT")  # Default to BTCUSDT if not provided
    quantity = float(data.get("quantity", 0.01))  # Default quantity

    # Adjust entry price based on signal type
    if signal_type == "Buy":
        entry_price *= 0.998  # 0.2% lower for Buy orders
    elif signal_type == "Sell":
        entry_price *= 1.002  # 0.2% higher for Sell orders

    # Set leverage to 20
    set_leverage(symbol, 20)

    # Custom conditions
    if signal_type == "Buy":
        if current_price(symbol) < entry_price:
            create_order(symbol, "Buy", quantity, entry_price, stop_loss, take_profit)
    elif signal_type == "Sell":
        if current_price(symbol) > entry_price:
            create_order(symbol, "Sell", quantity, entry_price, stop_loss, take_profit)

    return jsonify({"message": "Signal processed"}), 200

# Get current price (Bybit API)
def current_price(symbol):
    response = requests.get(f"{BYBIT_API_URL}/v2/public/tickers", params={"symbol": symbol})
    data = response.json()
    return float(data["result"][0]["last_price"])

# Set leverage
def set_leverage(symbol, leverage):
    leverage_data = {
        "api_key": BYBIT_API_KEY,
        "symbol": symbol,
        "buy_leverage": leverage,
        "sell_leverage": leverage
    }

    response = requests.post(f"{BYBIT_API_URL}/v2/private/position/leverage/save", json=leverage_data)
    print(response.json())
    return response.json()

# Create order
def create_order(symbol, side, quantity, entry_price, stop_loss, take_profit):
    order = {
        "api_key": BYBIT_API_KEY,
        "symbol": symbol,
        "side": "Buy" if side == "Buy" else "Sell",
        "order_type": "Limit",
        "qty": quantity,
        "price": entry_price,
        "time_in_force": "GoodTillCancel",
        "reduce_only": False,
        "close_on_trigger": False,
        "stop_loss": stop_loss,
        "take_profit": take_profit
    }

    # Sign request (if necessary) and send
    response = requests.post(f"{BYBIT_API_URL}/v2/private/order/create", json=order)
    print(response.json())
    return response.json()

# Trailing Stop Implementation
def set_trailing_stop(symbol, side, quantity, activation_price, trailing_distance):
    trailing_order = {
        "api_key": BYBIT_API_KEY,
        "symbol": symbol,
        "side": "Buy" if side == "Buy" else "Sell",
        "trail_value": trailing_distance,
        "activation_price": activation_price,
        "time_in_force": "GoodTillCancel",
        "reduce_only": False,
    }

    response = requests.post(f"{BYBIT_API_URL}/v2/private/stop-order/create", json=trailing_order)
    print(response.json())
    return response.json()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
