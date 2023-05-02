"""Live or test trading account"""

import re

import numpy as np
import pandas as pd

from models.PyCryptoBot import truncate
from models.exchange.binance import AuthAPI as BAuthAPI
from models.exchange.coinbase_pro import AuthAPI as CBAuthAPI


class TradingAccount():
    def __init__(self, app=None):
        """Trading account object model

        Parameters
        ----------
        app : object
            PyCryptoBot object
        """

        # config needs to be a dictionary, empty or otherwise
        if app is None:
            raise TypeError('App is not a PyCryptoBot object.')

        # if trading account is for testing it will be instantiated with a balance of 1000
        self.balance = pd.DataFrame([
            [ 'QUOTE', 1000, 0, 1000 ],
            [ 'BASE', 0, 0, 0 ]],
            columns=['currency','balance','hold','available'])

        self.app = app

        if app.isLive():
            self.mode = 'live'
        else:
            self.mode = 'test'

        self.orders = pd.DataFrame()

    def __convertStatus(self, val):
        if val == 'filled':
            return 'done'
        else:
            return val

    def _checkMarketSyntax(self, market):
        """Check that the market is syntactically correct

        Parameters
        ----------
        market : str
            market to check
        """
        if self.app.getExchange() == 'coinbasepro' and market != '':
            p = re.compile(r"^[1-9A-Z]{2,5}\-[1-9A-Z]{2,5}$")
            if not p.match(market):
                raise TypeError('Coinbase Pro market is invalid.')
        elif self.app.getExchange() == 'binance':
            p = re.compile(r"^[A-Z]{6,12}$")
            if not p.match(market):
                raise TypeError('Binance market is invalid.')

    def getOrders(self, market='', action='', status='all'):
        """Retrieves orders either live or simulation

        Parameters
        ----------
        market : str, optional
            Filters orders by market
        action : str, optional
            Filters orders by action
        status : str
            Filters orders by status, defaults to 'all'
        """

        # validate market is syntactically correct
        self._checkMarketSyntax(market)

        if action != '':
            # validate action is either a buy or sell
            if not action in ['buy', 'sell']:
                raise ValueError('Invalid order action.')

        # validate status is open, pending, done, active or all
        if not status in ['open', 'pending', 'done', 'active', 'all', 'filled']:
            raise ValueError('Invalid order status.')

        if self.app.getExchange() == 'binance':
            if self.mode == 'live':
                # if config is provided and live connect to Binance account portfolio
                model = BAuthAPI(self.app.getAPIKey(), self.app.getAPISecret(), self.app.getAPIURL())
                # retrieve orders from live Binance account portfolio
                self.orders = model.getOrders(market, action, status)
                return self.orders
            else:
                # return dummy orders
                if market == '':
                    return self.orders
                else:
                    return self.orders[self.orders['market'] == market]
        if self.app.getExchange() == 'coinbasepro':
            if self.mode == 'live':
                # if config is provided and live connect to Coinbase Pro account portfolio
                model = CBAuthAPI(self.app.getAPIKey(), self.app.getAPISecret(), self.app.getAPIPassphrase(), self.app.getAPIURL())
                # retrieve orders from live Coinbase Pro account portfolio
                self.orders = model.getOrders(market, action, status)
                return self.orders
            else:
                # return dummy orders
                if market == '':
                    return self.orders
                else:
                    return self.orders[self.orders['market'] == market]

    def getBalance(self, currency=''):
        """Retrieves balance either live or simulation

        Parameters
        ----------
        currency: str, optional
            Filters orders by currency
        """

        if self.app.getExchange() == 'binance':
            if self.mode == 'live':
                model = BAuthAPI(self.app.getAPIKey(), self.app.getAPISecret())
                df = model.getAccount()
                if isinstance(df, pd.DataFrame):
                    if currency == '':
                        # retrieve all balances
                        return df
                    else:
                        # retrieve balance of specified currency
                        df_filtered = df[df['currency'] == currency]['available']
                        if len(df_filtered) == 0:
                            # return nil balance if no positive balance was found
                            return 0.0
                        else:
                            # return balance of specified currency (if positive)
                            if currency in ['EUR', 'GBP', 'USD']:
                                return float(truncate(float(df[df['currency'] == currency]['available'].values[0]), 2))
                            else:
                                return float(truncate(float(df[df['currency'] == currency]['available'].values[0]), 4))
                else:
                    return 0.0
            else:
                # return dummy balances
                if currency == '':
                    # retrieve all balances
                    return self.balance
                else:
                    if self.app.getExchange() == 'binance':
                        self.balance = self.balance.replace('QUOTE', currency)
                    else:
                        # replace QUOTE and BASE placeholders
                        if currency in ['EUR','GBP','USD']:
                            self.balance = self.balance.replace('QUOTE', currency)
                        else:
                            self.balance = self.balance.replace('BASE', currency)

                    if self.balance.currency[self.balance.currency.isin([currency])].empty:
                        self.balance.loc[len(self.balance)] = [currency, 0, 0, 0]

                    # retrieve balance of specified currency
                    df = self.balance
                    df_filtered = df[df['currency'] == currency]['available']

                    if len(df_filtered) == 0:
                        # return nil balance if no positive balance was found
                        return 0.0
                    else:
                        # return balance of specified currency (if positive)
                        if currency in ['EUR', 'GBP', 'USD']:
                            return float(truncate(float(df[df['currency'] == currency]['available'].values[0]), 2))
                        else:
                            return float(truncate(float(df[df['currency'] == currency]['available'].values[0]), 4))

        else:
            if self.mode == 'live':
                # if config is provided and live connect to Coinbase Pro account portfolio
                model = CBAuthAPI(self.app.getAPIKey(), self.app.getAPISecret(), self.app.getAPIPassphrase(), self.app.getAPIURL())
                if currency == '':
                    # retrieve all balances
                    return model.getAccounts()[['currency', 'balance', 'hold', 'available']]
                else:
                    df = model.getAccounts()
                    # retrieve balance of specified currency
                    df_filtered = df[df['currency'] == currency]['available']
                    if len(df_filtered) == 0:
                        # return nil balance if no positive balance was found
                        return 0.0
                    else:
                        # return balance of specified currency (if positive)
                        if currency in ['EUR','GBP','USD']:
                            return float(truncate(float(df[df['currency'] == currency]['available'].values[0]), 2))
                        else:
                            return float(truncate(float(df[df['currency'] == currency]['available'].values[0]), 4))

            else:
                # return dummy balances

                if currency == '':
                    # retrieve all balances
                    return self.balance
                else:
                    # replace QUOTE and BASE placeholders
                    if currency in ['EUR','GBP','USD']:
                        self.balance = self.balance.replace('QUOTE', currency)
                    elif currency in ['BCH','BTC','ETH','LTC','XLM']:
                        self.balance = self.balance.replace('BASE', currency)

                    if self.balance.currency[self.balance.currency.isin([currency])].empty == True:
                        self.balance.loc[len(self.balance)] = [currency,0,0,0]

                    # retrieve balance of specified currency
                    df = self.balance
                    df_filtered = df[df['currency'] == currency]['available']

                    if len(df_filtered) == 0:
                        # return nil balance if no positive balance was found
                        return 0.0
                    else:
                        # return balance of specified currency (if positive)
                        if currency in ['EUR','GBP','USD']:
                            return float(truncate(float(df[df['currency'] == currency]['available'].values[0]), 2))
                        else:
                            return float(truncate(float(df[df['currency'] == currency]['available'].values[0]), 4))

    def saveTrackerCSV(self, market='', save_file='tracker.csv'):
        """Saves order tracker to CSV

        Parameters
        ----------
        market : str, optional
            Filters orders by market
        save_file : str
            Output CSV file
        """

        # validate market is syntactically correct
        self._checkMarketSyntax(market)

        if self.mode == 'live':
            if self.app.getExchange() == 'coinbasepro':
                # retrieve orders from live Coinbase Pro account portfolio
                df = self.getOrders(market, '', 'done')
            elif self.app.getExchange() == 'binance':
                # retrieve orders from live Binance account portfolio
                df = self.getOrders(market, '', 'done')
            else:
                df = pd.DataFrame()
        else:
            # return dummy orders
            if market == '':
                df = self.orders
            else:
                if 'market' in self.orders:
                    df = self.orders[self.orders['market'] == market]
                else:
                    df = pd.DataFrame()

        if list(df.keys()) != [ 'created_at', 'market', 'action', 'type', 'size', 'value', 'fees', 'price', 'status' ]:
            # no data, return early
            return False

        df_tracker = pd.DataFrame()

        last_action = ''
        for market in df['market'].sort_values().unique():
            df_market = df[df['market'] == market]

            df_buy = pd.DataFrame()
            df_sell = pd.DataFrame()

            pair = 0
            # pylint: disable=unused-variable
            for index, row in df_market.iterrows():
                if row['action'] == 'buy':
                    pair = 1

                if pair == 1 and (row['action'] != last_action):
                    if row['action'] == 'buy':
                        df_buy = row
                    elif row['action'] == 'sell':
                        df_sell = row

                if row['action'] == 'sell' and len(df_buy) != 0:
                    df_pair = pd.DataFrame([
                        [
                            df_sell['status'],
                            df_buy['market'],
                            df_buy['created_at'],
                            df_buy['type'],
                            df_buy['size'],
                            df_buy['value'],
                            df_buy['fees'],
                            df_buy['price'],
                            df_sell['created_at'],
                            df_sell['type'],
                            df_sell['size'],
                            df_sell['value'],
                            df_sell['fees'],
                            df_sell['price']
                        ]], columns=[ 'status', 'market',
                            'buy_at', 'buy_type', 'buy_size', 'buy_value', 'buy_fees', 'buy_price',
                            'sell_at', 'sell_type', 'sell_size', 'sell_value', 'sell_fees', 'sell_price'
                        ])
                    df_tracker = df_tracker.append(df_pair, ignore_index=True)
                    pair = 0

                last_action = row['action']

        if list(df_tracker.keys()) != [ 'status', 'market',
                            'buy_at', 'buy_type', 'buy_size', 'buy_value', 'buy_fees', 'buy_price',
                            'sell_at', 'sell_type', 'sell_size', 'sell_value', 'sell_fees', 'sell_price' ]:
            # no data, return early
            return False

        df_tracker['profit'] = np.subtract(np.subtract(df_tracker['sell_value'], df_tracker['buy_value']), np.add(df_tracker['buy_fees'], df_tracker['sell_fees']))
        df_tracker['margin'] = np.multiply(np.true_divide(df_tracker['profit'], df_tracker['buy_value']), 100)
        df_sincebot = df_tracker[df_tracker['buy_at'] > '2021-02-1']

        try:
            df_sincebot.to_csv(save_file, index=False)
        except OSError:
            raise SystemExit('Unable to save: ', save_file)
