{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "800d0572",
   "metadata": {},
   "outputs": [],
   "source": [
    "import ccxt\n",
    "import pandas as pd\n",
    "import json\n",
    "import time\n",
    "\n",
    "class cBot_perp_ftx():\n",
    "    def __init__(self, apiKey=None, secret=None, subAccountName=None):\n",
    "        ftxAuthObject = {\n",
    "            \"apiKey\": apiKey,\n",
    "            \"secret\": secret,\n",
    "            'headers': {\n",
    "                'FTX-SUBACCOUNT': subAccountName\n",
    "            }\n",
    "        }\n",
    "        if ftxAuthObject['secret'] == None:\n",
    "            self._auth = False\n",
    "            self._session = ccxt.ftx()\n",
    "        else:\n",
    "            self._auth = True\n",
    "            self._session = ccxt.ftx(ftxAuthObject)\n",
    "        self._session.load_markets()\n",
    "\n",
    "    def authentication_required(fn):\n",
    "        \"\"\"Annotation for methods that require auth.\"\"\"\n",
    "        def wrapped(self, *args, **kwargs):\n",
    "            if not self._auth:\n",
    "                print(\"You must be authenticated to use this method\", fn)\n",
    "                exit()\n",
    "            else:\n",
    "                return fn(self, *args, **kwargs)\n",
    "        return wrapped\n",
    "\n",
    "    def get_historical_since(self, symbol, timeframe, startDate):\n",
    "        try:\n",
    "            tempData = self._session.fetch_ohlcv(symbol, timeframe, int(\n",
    "                time.time()*1000)-1209600000, limit=1000)\n",
    "            dtemp = pd.DataFrame(tempData)\n",
    "            timeInter = int(dtemp.iloc[-1][0] - dtemp.iloc[-2][0])\n",
    "        except:\n",
    "            return None\n",
    "\n",
    "        finished = False\n",
    "        start = False\n",
    "        allDf = []\n",
    "        startDate = self._session.parse8601(startDate)\n",
    "        while(start == False):\n",
    "            try:\n",
    "                tempData = self._session.fetch_ohlcv(\n",
    "                    symbol, timeframe, startDate, limit=1000)\n",
    "                dtemp = pd.DataFrame(tempData)\n",
    "                timeInter = int(dtemp.iloc[-1][0] - dtemp.iloc[-2][0])\n",
    "                nextTime = int(dtemp.iloc[-1][0] + timeInter)\n",
    "                allDf.append(dtemp)\n",
    "                start = True\n",
    "            except:\n",
    "                startDate = startDate + 1209600000*2\n",
    "\n",
    "        if dtemp.shape[0] < 1:\n",
    "            finished = True\n",
    "        while(finished == False):\n",
    "            try:\n",
    "                tempData = self._session.fetch_ohlcv(\n",
    "                    symbol, timeframe, nextTime, limit=1000)\n",
    "                dtemp = pd.DataFrame(tempData)\n",
    "                nextTime = int(dtemp.iloc[-1][0] + timeInter)\n",
    "                allDf.append(dtemp)\n",
    "                if dtemp.shape[0] < 1:\n",
    "                    finished = True\n",
    "            except:\n",
    "                finished = True\n",
    "        result = pd.concat(allDf, ignore_index=True, sort=False)\n",
    "        result = result.rename(\n",
    "            columns={0: 'timestamp', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'})\n",
    "        result = result.set_index(result['timestamp'])\n",
    "        result.index = pd.to_datetime(result.index, unit='ms')\n",
    "        del result['timestamp']\n",
    "        return result\n",
    "\n",
    "    def get_last_historical(self, symbol, timeframe, limit):\n",
    "        result = pd.DataFrame(data=self._session.fetch_ohlcv(\n",
    "            symbol, timeframe, None, limit=limit))\n",
    "        result = result.rename(\n",
    "            columns={0: 'timestamp', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'})\n",
    "        result = result.set_index(result['timestamp'])\n",
    "        result.index = pd.to_datetime(result.index, unit='ms')\n",
    "        del result['timestamp']\n",
    "        return result\n",
    "\n",
    "    def get_min_order_amount(self, symbol):\n",
    "        return self._session.markets_by_id[symbol]['limits']['amount']['min']\n",
    "\n",
    "    def convert_amount_to_precision(self, symbol, amount):\n",
    "        return self._session.amount_to_precision(symbol, amount)\n",
    "\n",
    "    def convert_price_to_precision(self, symbol, price):\n",
    "        return self._session.price_to_precision(symbol, price)\n",
    "\n",
    "    @authentication_required\n",
    "    def get_all_balance(self):\n",
    "        try:\n",
    "            allBalance = self._session.fetchBalance()\n",
    "        except BaseException as err:\n",
    "            raise TypeError(\"An error occured in get_all_balance\", err)\n",
    "        return allBalance['total']\n",
    "\n",
    "    @authentication_required\n",
    "    def get_balance_of_one_coin(self, coin):\n",
    "        try:\n",
    "            allBalance = self._session.fetchBalance()\n",
    "        except BaseException as err:\n",
    "            raise TypeError(\"An error occured in get_balance_of_one_coin\", err)\n",
    "        try:\n",
    "            return allBalance['total'][coin]\n",
    "        except:\n",
    "            return 0\n",
    "\n",
    "    @authentication_required\n",
    "    def place_market_order(self, symbol, side, amount, leverage=1):\n",
    "        try:\n",
    "            return self._session.createOrder(\n",
    "                symbol,\n",
    "                'market',\n",
    "                side,\n",
    "                self.convert_amount_to_precision(symbol, amount * leverage),\n",
    "                None\n",
    "            )\n",
    "        except BaseException as err:\n",
    "            raise TypeError(\"An error occured in place_market_order\", err)\n",
    "\n",
    "    @authentication_required\n",
    "    def place_reduce_market_order(self, symbol, side, amount, leverage=1):\n",
    "        params = {\n",
    "            'reduceOnly':True\n",
    "        }\n",
    "        try:\n",
    "            return self._session.createOrder(\n",
    "                symbol,\n",
    "                'market',\n",
    "                side,\n",
    "                self.convert_amount_to_precision(symbol, amount * leverage),\n",
    "                None,\n",
    "                params\n",
    "            )\n",
    "        except BaseException as err:\n",
    "            raise TypeError(\"An error occured in place_reduce_market_order\", err)\n",
    "\n",
    "    @authentication_required\n",
    "    def place_limit_order(self, symbol, side, amount, price, leverage=1):\n",
    "        try:\n",
    "            return self._session.createOrder(\n",
    "                symbol,\n",
    "                'limit',\n",
    "                side,\n",
    "                self.convert_amount_to_precision(symbol, amount * leverage),\n",
    "                self.convert_price_to_precision(symbol, price)\n",
    "                )\n",
    "        except BaseException as err:\n",
    "            raise TypeError(\"An error occured in place_limit_order\", err)\n",
    "\n",
    "    @authentication_required\n",
    "    def place_reduce_limit_order(self, symbol, side, amount, price, leverage=1):\n",
    "        params = {\n",
    "            'reduceOnly':True\n",
    "        }\n",
    "        try:\n",
    "            return self._session.createOrder(\n",
    "                symbol,\n",
    "                'limit',\n",
    "                side,\n",
    "                self.convert_amount_to_precision(symbol, amount * leverage),\n",
    "                self.convert_price_to_precision(symbol, price),\n",
    "                params\n",
    "                )\n",
    "        except BaseException as err:\n",
    "            raise TypeError(\"An error occured in place_reduce_limit_order\", err)\n",
    "\n",
    "    @authentication_required\n",
    "    def place_market_stop_loss(self, symbol, side, amount, price, leverage=1):\n",
    "        params = {\n",
    "        'stopPrice': self.convert_price_to_precision(symbol, price),  # your stop price\n",
    "        'reduceOnly':True\n",
    "        }\n",
    "        try:\n",
    "            return self._session.createOrder(\n",
    "                symbol,\n",
    "                'stop',\n",
    "                side,\n",
    "                self.convert_amount_to_precision(symbol, amount * leverage),\n",
    "                None,\n",
    "                params\n",
    "                )\n",
    "        except BaseException as err:\n",
    "            raise TypeError(\"An error occured in place_market_stop_loss\", err)\n",
    "\n",
    "    @authentication_required\n",
    "    def place_market_take_profit(self, symbol, side, amount, price, leverage=1):\n",
    "        params = {\n",
    "        'stopPrice': self.convert_price_to_precision(symbol, price),  # your stop price\n",
    "        'reduceOnly':True\n",
    "        }\n",
    "        try:\n",
    "            return self._session.createOrder(\n",
    "                symbol,\n",
    "                'takeProfit',\n",
    "                side,\n",
    "                self.convert_amount_to_precision(symbol, amount * leverage),\n",
    "                None,\n",
    "                params\n",
    "                )\n",
    "        except BaseException as err:\n",
    "            raise TypeError(\"An error occured in place_market_take_profit\", err)\n",
    "\n",
    "\n",
    "    @authentication_required\n",
    "    def cancel_all_open_order(self, symbol):\n",
    "        try:\n",
    "            return self._session.cancel_all_orders(symbol)\n",
    "        except BaseException as err:\n",
    "            raise TypeError(\"An error occured in cancel_all_open_order\", err)\n",
    "\n",
    "    @authentication_required\n",
    "    def cancel_order_by_id(self, id):\n",
    "        try:\n",
    "            return self._session.cancel_order(id)\n",
    "        except BaseException as err:\n",
    "            raise TypeError(\"An error occured in cancel_order_by_id\", err)\n",
    "\n",
    "    @authentication_required\n",
    "    def get_open_order(self, symbol=None):\n",
    "        try:\n",
    "            return self._session.fetchOpenOrders(symbol, None, None)\n",
    "        except BaseException as err:\n",
    "            raise TypeError(\"An error occured in get_open_order\", err)\n",
    "\n",
    "    @authentication_required\n",
    "    def get_open_conditionnal_order(self, symbol=None):\n",
    "        params = {\n",
    "            'type':'stop'\n",
    "        }\n",
    "        try:\n",
    "            return self._session.fetchOpenOrders(symbol,None,None,params)\n",
    "        except BaseException as err:\n",
    "            raise TypeError(\"An error occured in get_open_conditionnal_order\", err)\n",
    "\n",
    "    @authentication_required\n",
    "    def get_my_trades(self, symbol=None, since=None, limit=1):\n",
    "        try:\n",
    "            return self._session.fetch_my_trades(symbol, since, limit)\n",
    "        except BaseException as err:\n",
    "            raise TypeError(\"An error occured in get_my_trades\", err)\n",
    "\n",
    "    @authentication_required\n",
    "    def get_open_position(self,symbol=None):\n",
    "        try:\n",
    "            positions = self._session.fetchPositions(symbol)\n",
    "            truePositions = []\n",
    "            for position in positions:\n",
    "                if float(position['contracts']) > 0:\n",
    "                    truePositions.append(position)\n",
    "            return truePositions\n",
    "        except BaseException as err:\n",
    "            raise TypeError(\"An error occured in get_open_position\", err)\n",
    "\n",
    "    @authentication_required\n",
    "    def close_all_open_position(self,symbol=None):\n",
    "        try:\n",
    "            positions = self._session.fetchPositions(symbol)\n",
    "            for position in positions:\n",
    "                if position['side'] == 'long' and position['contracts'] > 0:\n",
    "                    self.place_reduce_market_order(position['symbol'], 'sell', position['contracts'])\n",
    "                elif position['side'] == 'short' and position['contracts'] > 0:\n",
    "                    self.place_reduce_market_order(position['symbol'], 'buy', position['contracts'])\n",
    "            return 'Close all positions done'\n",
    "        except BaseException as err:\n",
    "            raise TypeError(\"An error occured in close_all_open_position\", err)"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.10"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}