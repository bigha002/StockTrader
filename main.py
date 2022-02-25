import math
import alpaca_trade_api as tradeapi
import numpy as np
import time
import csv
import analyzer
import threading

SEC_KEY = 'CFD5PRwmZTADhdwDmuNNOu5RkKRWMtx0bVAp5Cnp' # Enter Your Secret Key Here
PUB_KEY = 'PKOXDHJKGY1QHE0QRYBO' # Enter Your Public Key Here
BASE_URL = 'https://paper-api.alpaca.markets' # This is the base URL for paper trading
api = tradeapi.REST(key_id= PUB_KEY, secret_key=SEC_KEY, base_url=BASE_URL) # For real trading, don't enter a base_url

new_symb = "ISPO"
pos_held = False

def recalc_loop():
  while True:
    calculation = analyzer.recalculate()
    if new_symb != calculation:
      print("New symbol found! "+calculation)
    new_symb = calculation
    time.sleep(60*30)

loop = threading.Thread(target=recalc_loop)
loop.daemon = True
loop.start()

while True:
  symb = new_symb
  print("")
  print("Checking Price on "+symb)
  
  market_data = api.get_barset(symb, 'minute', limit=5) # Get one bar object for each of the past 5 minutes

  close_list = [] # This array will store all the closing prices from the last 5 minutes
  for bar in market_data[symb]:
      close_list.append(bar.c) # bar.c is the closing price of that bar's time interval

  close_list = np.array(close_list, dtype=np.float64) # Convert to numpy array
  ma = np.mean(close_list)
  last_price = close_list[4] # Most recent closing price

  print("Moving Average: " + str(ma))
  print("Last Price: " + str(last_price))

  
  if ma + 0.1 < last_price and not pos_held: # If MA is more than 10cents under price, and we haven't already bought
      print("Buying "+symb)
      api.submit_order(
          symbol=symb,
          qty=1,
          side='buy',
          type='market',
          time_in_force='gtc'
      )
      pos_held = True
  elif ma - 0.1 > last_price and pos_held: # If MA is more than 10cents above price, and we already bought
      print("Selling"+symb)
      api.submit_order(
          symbol=symb,
          qty=1,
          side='sell',
          type='market',
          time_in_force='gtc'
      )
      pos_held = False
    
  time.sleep(10)