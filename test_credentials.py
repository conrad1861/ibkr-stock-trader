import ib_insync
from ib_insync import IB

# Create an IB instance
ib = IB()

# Connect to TWS or IB Gateway
# '127.0.0.1' is the localhost, '7497' is the default port for paper trading, and 'clientId=1' is a unique identifier for your session.
ib.connect('127.0.0.1', 7497, clientId=1)

# Check the connection
if ib.isConnected():
    print("Connected to Interactive Brokers")
else:
    print("Connection failed")

# Example: Request account summary
account_summary = ib.accountSummary()
print(account_summary)

# Example: Request market data for a stock
contract = ib_insync.Stock('AAPL', 'SMART', 'USD')
ticker = ib.reqMktData(contract)
print(ticker)
