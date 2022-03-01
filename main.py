import math
import alpaca_trade_api as tradeapi
from alpaca_trade_api import TimeFrame
import numpy as np
import time
import csv
import analyzer
import threading
import yfinance as yf

polykey = "G2sOBR18ZcXTX1pvOvVsu1PQGWs6vtl2"
SEC_KEY = 'TpxaYhfokqEco7lmv8sff9hCWOvZUwV4Rqjb0ALB' # Enter Your Secret Key Here
PUB_KEY = 'PK5RJZFYIZC6XAYSB6CA' # Enter Your Public Key Here
BASE_URL = 'https://paper-api.alpaca.markets' # This is the base URL for paper trading
api = tradeapi.REST(key_id= PUB_KEY, secret_key=SEC_KEY, base_url=BASE_URL) # For real trading, don't enter a base_url

new_symb = "USER"
pos_held = False
buy_power = 20

# print(api.get_bars(new_symb, TimeFrame.Minute, limit=5))

# def recalc_loop():
#   global new_symb
#   while True:
#     calculation = analyzer.recalculate()
#     if new_symb != calculation and len(api.get_bars(calculation, TimeFrame.Minute, limit=5))>0:
#       # print("New symbol found! "+calculation)
#       while pos_held == True:
#           time.sleep(.1)
#       print("Successfully changed symbol to "+calculation)
#       # global new_symb
#       new_symb = calculation
#     time.sleep(60*30)


# loop = threading.Thread(target=recalc_loop)
# loop.daemon = True
# loop.start()

# api.submit_order(
#     symbol=new_symb,
#     qty=.5,
#     side='buy',
#     type='market',
#     time_in_force='day'
# )

while True:
  calculation = analyzer.recalculate()
  if new_symb != calculation and len(api.get_bars(calculation, TimeFrame.Minute, limit=5))>0:
    # print("New symbol found! "+calculation)
    if pos_held:
      api.submit_order(
          symbol=new_symb,
          qty=pos_held,
          side='sell',
          type='market',
          time_in_force='day'
        )
    print("Successfully changed symbol to "+calculation)
    # global new_symb
    new_symb = calculation
  for i in range(31):
    symb = new_symb
  #   print("")
  #   print("Checking Price on "+symb)
    
    # market_data = None # Get one bar object for each of the past 5 minutes

    # sf = yf.Ticker(new_symb)
    market_data = yf.download(tickers=new_symb, period='1d', interval='1m')['Close']
    market_data = market_data[max(len(market_data)-5, 0):]

    close_list = [] # This array will store all the closing prices from the last 5 minutes
    for bar in market_data:
        close_list.append(bar) # bar.c is the closing price of that bar's time interval

    close_list = np.array(close_list, dtype=np.float64) # Convert to numpy array
    last_price = market_data[4] # Most recent closing price
    ma = np.mean(close_list)

    print("Moving Average for "+new_symb+": " + str(ma))
    print("Last Price for "+new_symb+": " + str(last_price))

    
    if ma + 0.1 < last_price and not pos_held: # If MA is more than 10cents under price, and we haven't already bought
      if api.get_asset(new_symb).fractionable == True:
          pos_held = (buy_power/last_price)
          api.submit_order(
              symbol=symb,
              qty=pos_held,
              side='buy',
              type='market',
              time_in_force='day'
          )
      else:
          pos_held = math.min(math.floor(buy_power/last_price), 1)
          api.submit_order(
              symbol=symb,
              qty=pos_held,
              side='buy',
              type='market',
              time_in_force='gtc'
          )
      print("\nBought "+str(pos_held)+" "+new_symb+"\n")
    elif ma - 0.1 > last_price and pos_held: # If MA is more than 10cents above price, and we already bought
        api.submit_order(
            symbol=new_symb,
            qty=pos_held,
            side='sell',
            type='market',
            time_in_force='day'
        )
        print("\nSold "+str(pos_held)+" "+new_symb+"\n")
        pos_held = None
    time.sleep(60)