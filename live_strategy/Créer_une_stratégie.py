import sys
sys.path.append('cBot-Project/utilities')
from custom_indicators import CustomIndocators as ci
from spot_ftx import SpotFtx
import pandas as pd
import ta
import ccxt
from datetime import datetime
import time

now = datetime.now()
print(now.strftime("%d-%m %H:%M:%S"))

ftx = SpotFtx(
        apiKey='',
        secret='',
        subAccountName=''
    )

pairList = [
    'BTC/USDT',
    'ETH/USDT'
]

timeframe = '1h'

# -- Hyper parameters --
maxOpenPosition = 3
TpPct = 0.15
SlPct = 0.015

dfList = {}
for pair in pairList:
    # print(pair)
    df = ftx.get_last_historical(pair, timeframe, 210)
    dfList[pair.replace('/USDT','')] = df

for coin in dfList:
    # -- Drop all columns we do not need --
    dfList[coin].drop(columns=dfList[coin].columns.difference(['open','high','low','close','volume']), inplace=True)

    # -- Indicators, you can edit every value --
    dfList[coin]['AO']= ta.momentum.awesome_oscillator(dfList[coin]['high'],dfList[coin]['low'],window1=6,window2=22)
    dfList[coin]['STOCH_RSI'] = ta.momentum.stochrsi(close=dfList[coin]['close'], window=14)
    dfList[coin]['WillR'] = ta.momentum.williams_r(high=dfList[coin]['high'], low=dfList[coin]['low'], close=dfList[coin]['close'], lbp=14)
    dfList[coin]['EMA100'] =ta.trend.ema_indicator(close=dfList[coin]['close'], window=100)
    dfList[coin]['EMA200'] =ta.trend.ema_indicator(close=dfList[coin]['close'], window=200)
        
print("Data and Indicators loaded 100%")

# -- Condition to BUY market --
def buyCondition(row, previousRow=None):
    if (
        row['AO'] >= 0
        and previousRow['AO'] > row['AO']
        and row['WillR'] < -85
        and row['EMA100'] > row['EMA200']
    ):
        return True
    else:
        return False

# -- Condition to SELL market --
def sellCondition(row, previousRow=None):
    if (
        (row['AO'] < 0
        and row['STOCH_RSI'] > 0.2)
        or row['WillR'] > -10
    ):
        return True
    else:
        return False
    
coinBalance = ftx.get_all_balance()
coinInUsd = ftx.get_all_balance_in_usd()
usdBalance = coinBalance['USDT']
del coinBalance['USDT']
del coinInUsd['USDT']
totalBalanceInUsd = usdBalance + sum(coinInUsd.values())
coinPositionList = []
for coin in coinInUsd:
    if coinInUsd[coin] > 0.05 * totalBalanceInUsd:
        coinPositionList.append(coin)
openPositions = len(coinPositionList)

#Sell
for coin in coinPositionList:
        if sellCondition(dfList[coin].iloc[-2], dfList[coin].iloc[-3]) == True:
            openPositions -= 1
            symbol = coin+'/USDT'
            cancel = ftx.cancel_all_open_order(symbol)
            time.sleep(1)
            sell = ftx.place_market_order(symbol,'sell',coinBalance[coin])
            print(cancel)
            print("Sell", coinBalance[coin], coin, sell)
        else:
            print("Keep",coin)

#Buy
if openPositions < maxOpenPosition:
    for coin in dfList:
        if coin not in coinPositionList:
            if buyCondition(dfList[coin].iloc[-2], dfList[coin].iloc[-3]) == True and openPositions < maxOpenPosition:
                time.sleep(1)
                usdBalance = ftx.get_balance_of_one_coin('USDT')
                symbol = coin+'/USDT'

                buyPrice = float(ftx.convert_price_to_precision(symbol, ftx.get_bid_ask_price(symbol)['ask'])) 
                slPrice = float(ftx.convert_price_to_precision(symbol, buyPrice - SlPct * buyPrice))
                tpPrice = float(ftx.convert_price_to_precision(symbol, buyPrice + TpPct * buyPrice))
                buyQuantityInUsd = usdBalance * 1/(maxOpenPosition-openPositions)

                if openPositions == maxOpenPosition - 1:
                    buyQuantityInUsd = 0.95 * buyQuantityInUsd

                buyAmount = ftx.convert_amount_to_precision(symbol, buyQuantityInUsd/buyPrice)

                buy = ftx.place_market_order(symbol,'buy',buyAmount)
                time.sleep(2)
                sl = ftx.place_market_stop_loss(symbol,'sell',buyAmount,slPrice)
                tp = ftx.place_limit_order(symbol,'sell',buyAmount,tpPrice)
                try:
                    tp["id"]
                except:
                    time.sleep(2)
                    sl = ftx.place_market_stop_loss(symbol,'sell',buyAmount,slPrice)
                    tp = ftx.place_limit_order(symbol,'sell',buyAmount,tpPrice)
                    pass
                print("Buy",buyAmount,coin,'at',buyPrice,buy)
                print("Place",buyAmount,coin,"TP at",tpPrice, tp)
                print("Place",buyAmount,coin,"SL at",slPrice, sl)
                openPositions += 1
