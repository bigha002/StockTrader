import math
import alpaca_trade_api as tradeapi
from alpaca_trade_api import TimeFrame
import numpy as np
import time
import csv
import analyzer
import threading
from datetime import datetime
from polygon import RESTClient

polykey = "G2sOBR18ZcXTX1pvOvVsu1PQGWs6vtl2"
SEC_KEY = 'CFD5PRwmZTADhdwDmuNNOu5RkKRWMtx0bVAp5Cnp' # Enter Your Secret Key Here
PUB_KEY = 'PKOXDHJKGY1QHE0QRYBO' # Enter Your Public Key Here
BASE_URL = 'https://paper-api.alpaca.markets' # This is the base URL for paper trading
api = tradeapi.REST(key_id= PUB_KEY, secret_key=SEC_KEY, base_url=BASE_URL) # For real trading, don't enter a base_url

new_symb = "ESLT"
pos_held = False
buy_power = 15

# print(api.get_bars(new_symb, TimeFrame.Minute, limit=5))

def recalc_loop():
  global new_symb
  while True:
    time.sleep(60*30)
    calculation = analyzer.recalculate()
    if new_symb != calculation and len(api.get_bars(calculation, TimeFrame.Minute, limit=5))>0:
      # print("New symbol found! "+calculation)
      while pos_held == True:
          time.sleep(1)
      print("Successfully changed symbol to "+calculation)
      new_symb = calculation

loop = threading.Thread(target=recalc_loop)
loop.daemon = True
loop.start()

# api.submit_order(
#     symbol=new_symb,
#     qty=.5,
#     side='buy',
#     type='market',
#     time_in_force='day'
# )

while True:
  symb = new_symb
#   print("")
#   print("Checking Price on "+symb)
  
  market_data = None # Get one bar object for each of the past 5 minutes
  with RESTClient(polykey) as r:
        from_ = datetime.today().strftime('%Y-%m-%d')
        to = datetime.today().strftime('%Y-%m-%d')
        resp = r.stocks_equities_aggregates(new_symb, 5, "minute", from_, to, adjusted=True, limit=5000, sort="asc")
        market_data = resp.results

  close_list = [] # This array will store all the closing prices from the last 5 minutes
  for bar in market_data:
      close_list.append(bar.c) # bar.c is the closing price of that bar's time interval

  close_list = np.array(close_list, dtype=np.float64) # Convert to numpy array
  ma = np.mean(close_list)
  last_price = close_list[4] # Most recent closing price

  print("Moving Average for "+new_symb+": " + str(ma))
  print("Last Price for "+new_symb+": " + str(last_price))

  
  if ma + 0.1 < last_price and not pos_held: # If MA is more than 10cents under price, and we haven't already bought
    if api.get_asset(new_symb).fractionable == True:
        pos_held = buy_power/last_price
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
    print("Bought "+str(pos_held)+" "+new_symb)
  elif ma - 0.1 > last_price and pos_held: # If MA is more than 10cents above price, and we already bought
      api.submit_order(
          symbol=new_symb,
          qty=pos_held,
          side='sell',
          type='market',
          time_in_force='day'
      )
      print("Sold "+str(pos_held)+" "+new_symb)
      pos_held = None
  api.get_bars("SPY", TimeFrame.Minute, limit=10)
  time.sleep(60)