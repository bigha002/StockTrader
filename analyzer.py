import math
import alpaca_trade_api as tradeapi
import numpy as np
import time
import csv

SEC_KEY = 'E0EPnAAQ5H78CyAZorw00kW7ULT4FGzzJX8LNUX6' # Enter Your Secret Key Here
PUB_KEY = 'PK0LA4SORMRQHNG8QB4I' # Enter Your Public Key Here
BASE_URL = 'https://paper-api.alpaca.markets' # This is the base URL for paper trading
api = tradeapi.REST(key_id= PUB_KEY, secret_key=SEC_KEY, base_url=BASE_URL) # For real trading, don't enter a base_url

symbs = []
i = 0
with open('nasdaq_screen.csv', 'r') as csvfile:
    datareader = csv.reader(csvfile)
    for row in datareader:
        symbs.append(row[0])
        i += 1
        # if i >= 100:
        #   break

def recalculate():
  print("\n== RUNNING RECALCULATION ==\n")
  hours_to_test = 2
  action_threshold = .5
  starterBalance = 2000

  best_option = None
  best_profit = 0

  for symb in symbs:
    pos_held = False

    # print("Checking Price")
    market_data = api.get_barset(symb, 'minute', limit=(60 * hours_to_test)) # Pull market data from the past 60x minutes

    close_list = []
    for bar in market_data[symb]:
        close_list.append(bar.c)
    if len(close_list) == 0 or len(close_list) < 60 * hours_to_test - 1:
      continue
    # if abs(close_list[0] - close_list[60 * hours_to_test - 1]) <= .5:
    #   continue

    # print("Open for "+symb+": " + str(close_list[0]))
    # print("Close: for "+symb+": " + str(close_list[60 * hours_to_test - 1]))


    close_list = np.array(close_list, dtype=np.float64)
    startBal = starterBalance # Start out with 2000 dollars
    balance = startBal
    buys = 0
    sells = 0



    for i in range(4, 60 * hours_to_test): # Start four minutes in, so that MA can be calculated
        ma = np.mean(close_list[i-4:i+1])
        last_price = close_list[i]

        # print("Moving Average: " + str(ma))
        # print("Last Price: " + str(last_price))

        if ma + action_threshold < last_price and not pos_held:
            # print("Buy")
            balance -= last_price
            pos_held = True
            buys += 1
        elif ma - action_threshold > last_price and pos_held:
            # print("Sell")
            balance += last_price
            pos_held = False
            sells += 1
        # print(balance)

    # print("")
    # print("Buys: " + str(buys))
    # print("Sells: " + str(sells))

    if buys > sells:
        balance += close_list[60 * hours_to_test - 1] # Add back your equity to your balance
        

    # print("Final Balance for "+symb+": " + str(balance))

    # print("Profit if held for "+symb+":  " + str(close_list[60 * hours_to_test - 1] - close_list[0]))
    # print("Profit from algorithm for "+symb+":  " + str(balance - startBal))

    if balance - startBal>best_profit and balance - startBal > close_list[60 * hours_to_test - 1] - close_list[0]:
      if api.get_asset(symb).fractionable == False:
        if close_list[60 * hours_to_test - 1] > 15:
          print(symb+' was found to have an un-fractionable price higher than $15')
          continue
      best_option = symb
      best_profit = balance - startBal

    time.sleep(0.01)

  print("\nBest option: "+best_option)
  print("Profit from best option: "+str(best_profit))
  return best_option