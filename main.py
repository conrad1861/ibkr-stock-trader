import ib_insync
from ib_insync import IB, MarketOrder
import decimal

# Initialize IB connection
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)  # Adjust IP, port, and clientId as needed

# Configuration
budget = decimal.Decimal(12000.0)
purchase_prices = {}
buy_order_filled = False
pending_buy_order_id = None

def fetch_latest_trade_price(symbol):
    try:
        # Create a proper contract object
        contract = ib_insync.Stock(symbol, 'SMART', 'USD')

        # Request market data for the contract
        ticker = ib.reqTickers(contract)

        # If there's no market data, raise an error
        if not ticker:
            raise Exception(f"No market data available for {symbol}")
        if ticker[0].last is None:
            raise Exception(f"Market data unavailable for {symbol}. You may need a subscription or check session conflicts.")

        return decimal.Decimal(ticker[0].last)

    except Exception as e:
        print(f"Error fetching trade price for {symbol}: {e}")
        return None

def buy_stock(symbol):
    try:
        # Fetch the latest trade price
        latest_price = fetch_latest_trade_price(symbol)
        if latest_price is None:
            print(f"Cannot fetch price for {symbol}.")
            return

        print(f"Placing market buy order for {symbol} based on latest price: {latest_price}")

        # Calculate the quantity to buy based on the budget
        quantity = budget // latest_price
        if quantity < 1:
            print(f"Calculated quantity is less than 1. Cannot place order for {symbol}.")
            return

        # Create the contract and place the market buy order
        contract = ib_insync.Stock(symbol, 'SMART', 'USD')
        order = MarketOrder('BUY', quantity)
        trade = ib.placeOrder(contract, order)

        global pending_buy_order_id
        pending_buy_order_id = trade.order.orderId

        # Wait for the order to be filled (synchronous)
        wait_for_order_fill(trade, True)

    except Exception as e:
        print(f"Error buying {symbol}: {e}")

def sell_all_positions():
    sell_all_positions_with_multiplier(1.0)

def sell_all_positions_with_multiplier(multiplier):
    global buy_order_filled, pending_buy_order_id

    positions = ib.positions()
    for position in positions:
        symbol = position.contract.symbol
        purchase_price = purchase_prices.get(symbol, None)
        if purchase_price is None:
            print(f"Purchase price for {symbol} not found. Skipping P&L calculation.")
            continue

        intended_sell_price = purchase_price * decimal.Decimal(multiplier)
        print(f"Placing sell order for {symbol} at target price: {intended_sell_price}")

        # Create the contract and place the sell order
        contract = ib_insync.Stock(symbol, 'SMART', 'USD')
        order = MarketOrder('SELL', position.position)
        trade = ib.placeOrder(contract, order)
        
        # Wait for the order to be filled (synchronous)
        wait_for_order_fill(trade, False)

def wait_for_order_fill(trade, is_buy_order):
    while trade.orderStatus.status != 'Filled':
        ib.sleep(0.05)

    filled_avg_price = decimal.Decimal(trade.orderStatus.avgFillPrice)
    print(f"Order {trade.order.orderId} filled. Filled Average Price: {filled_avg_price}")

    if is_buy_order:
        symbol = trade.contract.symbol
        print(f"Storing purchase price for {symbol}: {filled_avg_price}")
        purchase_prices[symbol] = filled_avg_price
        global buy_order_filled
        buy_order_filled = True
        print(f"Stored purchase price for {symbol}: {filled_avg_price}")

    else:
        symbol = trade.contract.symbol
        purchase_price = purchase_prices.get(symbol, None)
        if purchase_price:
            profit_or_loss = filled_avg_price - purchase_price
            if profit_or_loss > 0:
                print(f"Profit for {symbol}: {profit_or_loss}")
            else:
                print(f"Loss for {symbol}: {profit_or_loss}")

if __name__ == "__main__":
    print("Welcome to IB Trading!")
    print("Type 'buy SYMBOL' to buy a stock, 'sell' to sell all positions, 'sell 2x' to sell at 1.02 * filled price, or 'sell 1x' to sell at 1.01 * filled price.")

    while True:
        input_text = input("Enter command: ")
        commands = input_text.split(" ")

        if commands[0] == "buy":
            if len(commands) < 2:
                print("Usage: buy SYMBOL")
                continue
            symbol = commands[1]
            buy_stock(symbol)

        elif commands[0] == "sell":
            if len(commands) == 1:
                sell_all_positions()
            elif len(commands) == 2:
                if commands[1] == "2x":
                    sell_all_positions_with_multiplier(1.02)
                elif commands[1] == "1x":
                    sell_all_positions_with_multiplier(1.01)
                else:
                    print("Invalid command. Use 'sell', 'sell 2x', or 'sell 1x'.")
            else:
                print("Invalid command. Use 'sell', 'sell 2x', or 'sell 1x'.")
        else:
            print("Invalid command. Use 'buy SYMBOL', 'sell', 'sell 2x', or 'sell 1x'.")
