"""Python Crypto Bot consuming Coinbase Pro or Binance APIs"""

import functools
import logging
import os
import sched
import sys
import time
import pandas as pd
from datetime import datetime
from models.PyCryptoBot import PyCryptoBot, truncate as _truncate
from models.AppState import AppState
from models.Trading import TechnicalAnalysis
from models.TradingAccount import TradingAccount
from models.helper.MarginHelper import calculate_margin
from views.TradingGraphs import TradingGraphs

# production: disable traceback
# sys.tracebacklimit = 0

app = PyCryptoBot()
state = AppState()

s = sched.scheduler(time.time, time.sleep)

config = {}
account = None
if app.getLastAction() != None:
    state.last_action = app.getLastAction()

    account = TradingAccount(app)
    orders = account.getOrders(app.getMarket(), '', 'done')
    if len(orders) > 0:
        df = orders[orders.action == 'buy']
        df = df[-1:]

        if str(df.action.values[0]) == 'buy':
            state.last_buy_size = float(df[df.action == 'buy']['size'])
            state.last_buy_filled = float(df[df.action == 'buy']['filled'])
            state.last_buy_price = float(df[df.action == 'buy']['price'])
            state.last_buy_fee = float(df[df.action == 'buy']['fees'])

# if live trading is enabled
elif app.isLive():
    # connectivity check
    if app.getTime() is None:
        raise ConnectionError(
            'Unable to start the bot as your connection to the exchange is down. Please check your Internet connectivity!')

    account = TradingAccount(app)

    orders = account.getOrders(app.getMarket(), '', 'done')
    if len(orders) > 0:
        df = orders[-1:]

        if str(df.action.values[0]) == 'buy':
            state.last_action = 'BUY'
            state.last_buy_size = float(df[df.action == 'buy']['size'])
            state.last_buy_filled = float(df[df.action == 'buy']['filled'])
            state.last_buy_price = float(df[df.action == 'buy']['price'])
            state.last_buy_fee = state.last_buy_size * app.getTakerFee()
        else:
            state.last_action = 'SELL'
            state.last_buy_price = 0.0
    else:
        # If we do not have any orders, pick last action based on balance
        if account.getBalance(app.getBaseCurrency()) < account.getBalance(app.getQuoteCurrency()):
            state.last_action = 'SELL'
        elif account.getBalance(app.getBaseCurrency()) > account.getBalance(app.getQuoteCurrency()):
            state.last_action = 'BUY'

    if app.getExchange() == 'binance':
        if state.last_action == 'SELL' and account.getBalance(app.getQuoteCurrency()) < 0.001:
            raise Exception('Insufficient available funds to place buy order: ' + str(account.getBalance(
                app.getQuoteCurrency())) + ' < 0.1 ' + app.getQuoteCurrency() + "\nNote: A manual limit order places a hold on available funds.")
        elif state.last_action == 'BUY' and account.getBalance(app.getBaseCurrency()) < 0.001:
            raise Exception('Insufficient available funds to place sell order: ' + str(account.getBalance(
                app.getBaseCurrency())) + ' < 0.1 ' + app.getBaseCurrency() + "\nNote: A manual limit order places a hold on available funds.")

    elif app.getExchange() == 'coinbasepro':
        if state.last_action == 'SELL' and account.getBalance(app.getQuoteCurrency()) < 50:
            raise Exception('Insufficient available funds to place buy order: ' + str(account.getBalance(
                app.getQuoteCurrency())) + ' < 50 ' + app.getQuoteCurrency() + "\nNote: A manual limit order places a hold on available funds.")
        elif state.last_action == 'BUY' and account.getBalance(app.getBaseCurrency()) < 0.001:
            raise Exception('Insufficient available funds to place sell order: ' + str(account.getBalance(
                app.getBaseCurrency())) + ' < 0.1 ' + app.getBaseCurrency() + "\nNote: A manual limit order places a hold on available funds.")


def getAction(now: datetime = datetime.today().strftime('%Y-%m-%d %H:%M:%S'), app: PyCryptoBot = None, price: float = 0,
              df: pd.DataFrame = pd.DataFrame(), df_last: pd.DataFrame = pd.DataFrame(), last_action: str = 'WAIT',
              debug: bool = False) -> str:
    ema12gtema26co = bool(df_last['ema12gtema26co'].values[0])
    macdgtsignal = bool(df_last['macdgtsignal'].values[0])
    goldencross = bool(df_last['goldencross'].values[0])
    obv_pc = float(df_last['obv_pc'].values[0])
    elder_ray_buy = bool(df_last['eri_buy'].values[0])
    ema12gtema26 = bool(df_last['ema12gtema26'].values[0])
    macdgtsignalco = bool(df_last['macdgtsignalco'].values[0])
    ema12ltema26co = bool(df_last['ema12ltema26co'].values[0])
    macdltsignal = bool(df_last['macdltsignal'].values[0])

    # criteria for a buy signal
    if ema12gtema26co is True \
            and (macdgtsignal is True or app.disableBuyMACD()) \
            and (goldencross is True or app.disableBullOnly()) \
            and (obv_pc > -5 or app.disableBuyOBV()) \
            and (elder_ray_buy is True or app.disableBuyElderRay()) \
            and last_action != 'BUY':

        if debug is True:
            print('*** Buy Signal ***')
            print(f'ema12gtema26co: {ema12gtema26co}')
            if not app.disableBuyMACD():
                print(f'macdgtsignal: {macdgtsignal}')
            if not app.disableBullOnly():
                print(f'goldencross: {goldencross}')
            if not app.disableBuyOBV():
                print(f'obv_pc: {obv_pc} > -5')
            if not app.disableBuyElderRay():
                print(f'elder_ray_buy: {elder_ray_buy}')
            print(f'last_action: {last_action}')

        # if disabled, do not buy within 3% of the dataframe close high
        if app.disableBuyNearHigh() is True and (price > (df['close'].max() * 0.97)):
            state.action = 'WAIT'

            log_text = str(now) + ' | ' + app.getMarket() + ' | ' + \
                app.printGranularity() + ' | Ignoring Buy Signal (price ' + str(price) + ' within 3% of high ' + str(
                df['close'].max()) + ')'
            print(log_text, "\n")
            logging.warning(log_text)

        return 'BUY'

    elif ema12gtema26 is True \
            and macdgtsignalco is True \
            and (goldencross is True or app.disableBullOnly()) \
            and (obv_pc > -5 or app.disableBuyOBV()) \
            and (elder_ray_buy is True or app.disableBuyElderRay()) \
            and last_action != 'BUY':

        if debug is True:
            print('*** Buy Signal ***')
            print(f'ema12gtema26: {ema12gtema26}')
            print(f'macdgtsignalco: {macdgtsignalco}')
            if not app.disableBullOnly():
                print(f'goldencross: {goldencross}')
            if not app.disableBuyOBV():
                print(f'obv_pc: {obv_pc} > -5')
            if not app.disableBuyElderRay():
                print(f'elder_ray_buy: {elder_ray_buy}')
            print(f'last_action: {last_action}')

        # if disabled, do not buy within 3% of the dataframe close high
        if app.disableBuyNearHigh() is True and (price > (df['close'].max() * 0.97)):
            state.action = 'WAIT'

            log_text = str(now) + ' | ' + app.getMarket() + ' | ' + \
                app.printGranularity() + ' | Ignoring Buy Signal (price ' + str(price) + ' within 3% of high ' + str(
                df['close'].max()) + ')'
            print(log_text, "\n")
            logging.warning(log_text)

        return 'BUY'

    # criteria for a sell signal
    elif ema12ltema26co is True \
            and (macdltsignal is True or app.disableBuyMACD()) \
            and last_action not in ['', 'SELL']:

        if debug is True:
            print('*** Sell Signal ***')
            print(f'ema12ltema26co: {ema12ltema26co}')
            print(f'macdltsignal: {macdltsignal}')
            print(f'last_action: {last_action}')

        return 'SELL'

    return 'WAIT'


def getInterval(df: pd.DataFrame = pd.DataFrame(), app: PyCryptoBot = None, iterations: int = 0) -> pd.DataFrame:
    if len(df) == 0:
        return df

    if app.isSimulation() and iterations > 0:
        # with a simulation iterate through data
        return df.iloc[iterations - 1:iterations]
    else:
        # most recent entry
        return df.tail(1)

def executeJob(sc, app=PyCryptoBot(), state=AppState(), trading_data=pd.DataFrame()):
    """Trading bot job which runs at a scheduled interval"""

    # connectivity check (only when running live)
    if app.isLive() and app.getTime() is None:
        print('Your connection to the exchange has gone down, will retry in 1 minute!')

        # poll every 5 minute
        list(map(s.cancel, s.queue))
        s.enter(300, 1, executeJob, (sc, app, state))
        return

    # increment state.iterations
    state.iterations = state.iterations + 1

    if not app.isSimulation():
        # retrieve the app.getMarket() data
        trading_data = app.getHistoricalData(app.getMarket(), app.getGranularity())
    else:
        if len(trading_data) == 0:
            return None

    # analyse the market data
    trading_dataCopy = trading_data.copy()
    ta = TechnicalAnalysis(trading_dataCopy)
    ta.addAll()
    df = ta.getDataFrame()

    if app.isSimulation():
        df_last = getInterval(df, app, state.iterations)
    else:
        df_last = getInterval(df, app)

    if len(df_last.index.format()) > 0:
        current_df_index = str(df_last.index.format()[0])
    else:
        current_df_index = state.last_df_index

    formatted_current_df_index = f'{current_df_index} 00:00:00' if len(current_df_index) == 10 else current_df_index

    if app.getSmartSwitch() == 1 and app.getGranularity() == 3600 and app.is1hEMA1226Bull() is True and app.is6hEMA1226Bull() is True:
        print('*** smart switch from granularity 3600 (1 hour) to 900 (15 min) ***')

        app.notifyTelegram(app.getMarket() + " smart switch from granularity 3600 (1 hour) to 900 (15 min)")

        app.setGranularity(900)
        list(map(s.cancel, s.queue))
        s.enter(5, 1, executeJob, (sc, app, state))

    if app.getSmartSwitch() == 1 and app.getGranularity() == 900 and app.is1hEMA1226Bull() is False and app.is6hEMA1226Bull() is False:
        print("*** smart switch from granularity 900 (15 min) to 3600 (1 hour) ***")

        app.notifyTelegram(app.getMarket() + " smart switch from granularity 900 (15 min) to 3600 (1 hour)")

        app.setGranularity(3600)
        list(map(s.cancel, s.queue))
        s.enter(5, 1, executeJob, (sc, app, state))

    if app.getExchange() == 'binance' and app.getGranularity() == 86400:
        if len(df) < 250:
            # data frame should have 250 rows, if not retry
            print('error: data frame length is < 250 (' + str(len(df)) + ')')
            logging.error('error: data frame length is < 250 (' + str(len(df)) + ')')
            list(map(s.cancel, s.queue))
            s.enter(300, 1, executeJob, (sc, app, state))
    else:
        if len(df) < 300:
            if not app.isSimulation():
                # data frame should have 300 rows, if not retry
                print('error: data frame length is < 300 (' + str(len(df)) + ')')
                logging.error('error: data frame length is < 300 (' + str(len(df)) + ')')
                list(map(s.cancel, s.queue))
                s.enter(300, 1, executeJob, (sc, app, state))

    if len(df_last) > 0:
        now = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        if not app.isSimulation():
            ticker = app.getTicker(app.getMarket())
            now = ticker[0]
            price = ticker[1]
            if price < df_last['low'].values[0] or price == 0:
                price = float(df_last['close'].values[0])
        else:
            price = float(df_last['close'].values[0])

        if price < 0.0001:
            raise Exception(app.getMarket() + ' is unsuitable for trading, quote price is less than 0.0001!')

        # technical indicators
        ema12gtema26 = bool(df_last['ema12gtema26'].values[0])
        ema12gtema26co = bool(df_last['ema12gtema26co'].values[0])
        goldencross = bool(df_last['goldencross'].values[0])
        macdgtsignal = bool(df_last['macdgtsignal'].values[0])
        macdgtsignalco = bool(df_last['macdgtsignalco'].values[0])
        ema12ltema26 = bool(df_last['ema12ltema26'].values[0])
        ema12ltema26co = bool(df_last['ema12ltema26co'].values[0])
        macdltsignal = bool(df_last['macdltsignal'].values[0])
        macdltsignalco = bool(df_last['macdltsignalco'].values[0])
        obv = float(df_last['obv'].values[0])
        obv_pc = float(df_last['obv_pc'].values[0])
        elder_ray_buy = bool(df_last['eri_buy'].values[0])
        elder_ray_sell = bool(df_last['eri_sell'].values[0])

        # if simulation interations < 200 set goldencross to true
        if app.isSimulation() and state.iterations < 200:
            goldencross = True

        # candlestick detection
        hammer = bool(df_last['hammer'].values[0])
        inverted_hammer = bool(df_last['inverted_hammer'].values[0])
        hanging_man = bool(df_last['hanging_man'].values[0])
        shooting_star = bool(df_last['shooting_star'].values[0])
        three_white_soldiers = bool(df_last['three_white_soldiers'].values[0])
        three_black_crows = bool(df_last['three_black_crows'].values[0])
        morning_star = bool(df_last['morning_star'].values[0])
        evening_star = bool(df_last['evening_star'].values[0])
        three_line_strike = bool(df_last['three_line_strike'].values[0])
        abandoned_baby = bool(df_last['abandoned_baby'].values[0])
        morning_doji_star = bool(df_last['morning_doji_star'].values[0])
        evening_doji_star = bool(df_last['evening_doji_star'].values[0])
        two_black_gapping = bool(df_last['two_black_gapping'].values[0])

        state.action = getAction(now, app, price, df, df_last, state.last_action, False)

        immediate_action = False

        if state.last_buy_size > 0 and state.last_buy_price > 0 and price > 0 and state.last_action == 'BUY':
            # update last buy high
            if price > state.last_buy_high:
                state.last_buy_high = price

            if state.last_buy_high > 1:
                change_pcnt_high = ((price / state.last_buy_high) - 1) * 100
            else:
                change_pcnt_high = 0

            #  buy and sell calculations
            state.last_buy_fee = round(state.last_buy_size * app.getTakerFee(), 8)
            state.last_buy_filled = round(((state.last_buy_size - state.last_buy_fee) / state.last_buy_price), 8)

            margin, profit, sell_fee = calculate_margin(
                buy_size=state.last_buy_size,
                buy_filled=state.last_buy_filled,
                buy_price=state.last_buy_price,
                buy_fee=state.last_buy_fee,
                sell_percent=app.getSellPercent(),
                sell_price=price,
                sell_taker_fee=app.getTakerFee(),
                debug=False)

            # loss failsafe sell at fibonacci band
            if app.disableFailsafeFibonacciLow() is False and app.allowSellAtLoss() and app.sellLowerPcnt() is None and state.fib_low > 0 and state.fib_low >= float(
                    price):
                state.action = 'SELL'
                state.last_action = 'BUY'
                immediate_action = True
                log_text = '! Loss Failsafe Triggered (Fibonacci Band: ' + str(state.fib_low) + ')'
                print(log_text, "\n")
                logging.warning(log_text)

                app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') ' + log_text)

            # loss failsafe sell at trailing_stop_loss
            if margin > 0 and app.trailingStopLoss() != None and change_pcnt_high < app.trailingStopLoss():
                state.action = 'SELL'
                state.last_action = 'BUY'
                immediate_action = True
                log_text = '! Trailing Stop Loss Triggered (< ' + str(app.trailingStopLoss()) + '%)'
                print(log_text, "\n")
                logging.warning(log_text)

                app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') ' + log_text)

            # loss failsafe sell at sell_lower_pcnt
            elif app.disableFailsafeLowerPcnt() is False and app.allowSellAtLoss() and app.sellLowerPcnt() != None and margin < app.sellLowerPcnt():
                state.action = 'SELL'
                state.last_action = 'BUY'
                immediate_action = True
                log_text = '! Loss Failsafe Triggered (< ' + str(app.sellLowerPcnt()) + '%)'
                print(log_text, "\n")
                logging.warning(log_text)

                app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') ' + log_text)

            # profit bank at sell_upper_pcnt
            if app.disableProfitbankUpperPcnt() is False and app.sellUpperPcnt() != None and margin > app.sellUpperPcnt():
                state.action = 'SELL'
                state.last_action = 'BUY'
                immediate_action = True
                log_text = '! Profit Bank Triggered (> ' + str(app.sellUpperPcnt()) + '%)'
                print(log_text, "\n")
                logging.warning(log_text)

                app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') ' + log_text)

            # profit bank when strong reversal detected
            if app.disableProfitbankReversal() is False and margin > 3 and obv_pc < 0 and macdltsignal is True:
                state.action = 'SELL'
                state.last_action = 'BUY'
                immediate_action = True
                log_text = '! Profit Bank Triggered (Strong Reversal Detected)'
                print(log_text, "\n")
                logging.warning(log_text)

                app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') ' + log_text)

            # configuration specifies to not sell at a loss
            if state.action == 'SELL' and not app.allowSellAtLoss() and margin <= 0:
                state.action = 'WAIT'
                state.last_action = 'BUY'
                immediate_action = False
                log_text = '! Ignore Sell Signal (No Sell At Loss)'
                print(log_text, "\n")
                logging.warning(log_text)

            # profit bank when strong reversal detected
            if app.sellAtResistance() is True and margin >= 2 and price > 0 and price != ta.getTradeExit(price):
                state.action = 'SELL'
                state.last_action = 'BUY'
                immediate_action = True
                log_text = '! Profit Bank Triggered (Selling At Resistance)'
                print(log_text, "\n")
                logging.warning(log_text)

                if not (not app.allowSellAtLoss() and margin <= 0):
                    app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') ' + log_text)

        bullbeartext = ''
        if app.disableBullOnly() is True or (df_last['sma50'].values[0] == df_last['sma200'].values[0]):
            bullbeartext = ''
        elif goldencross is True:
            bullbeartext = ' (BULL)'
        elif goldencross is False:
            bullbeartext = ' (BEAR)'

        # polling is every 5 minutes (even for hourly intervals), but only process once per interval
        if (immediate_action is True or state.last_df_index != current_df_index):
            precision = 4

            if (price < 0.01):
                precision = 8

            # Since precision does not change after this point, it is safe to prepare a tailored `truncate()` that would
            # work with this precision. It should save a couple of `precision` uses, one for each `truncate()` call.
            truncate = functools.partial(_truncate, n=precision)

            price_text = 'Close: ' + truncate(price)
            ema_text = app.compare(df_last['ema12'].values[0], df_last['ema26'].values[0], 'EMA12/26', precision)

            macd_text = ''
            if app.disableBuyMACD() is False:
                macd_text = app.compare(df_last['macd'].values[0], df_last['signal'].values[0], 'MACD', precision)

            obv_text = ''
            if app.disableBuyOBV() is False:
                obv_text = 'OBV: ' + truncate(df_last['obv'].values[0]) + ' (' + str(
                    truncate(df_last['obv_pc'].values[0])) + '%)'

            state.eri_text = ''
            if app.disableBuyElderRay() is False:
                if elder_ray_buy is True:
                    state.eri_text = 'ERI: buy | '
                elif elder_ray_sell is True:
                    state.eri_text = 'ERI: sell | '
                else:
                    state.eri_text = 'ERI: | '

            if hammer is True:
                log_text = '* Candlestick Detected: Hammer ("Weak - Reversal - Bullish Signal - Up")'
                print(log_text, "\n")
                logging.debug(log_text)

            if shooting_star is True:
                log_text = '* Candlestick Detected: Shooting Star ("Weak - Reversal - Bearish Pattern - Down")'
                print(log_text, "\n")
                logging.debug(log_text)

            if hanging_man is True:
                log_text = '* Candlestick Detected: Hanging Man ("Weak - Continuation - Bearish Pattern - Down")'
                print(log_text, "\n")
                logging.debug(log_text)

            if inverted_hammer is True:
                log_text = '* Candlestick Detected: Inverted Hammer ("Weak - Continuation - Bullish Pattern - Up")'
                print(log_text, "\n")
                logging.debug(log_text)

            if three_white_soldiers is True:
                log_text = '*** Candlestick Detected: Three White Soldiers ("Strong - Reversal - Bullish Pattern - Up")'
                print(log_text, "\n")
                logging.debug(log_text)

                app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') ' + log_text)

            if three_black_crows is True:
                log_text = '* Candlestick Detected: Three Black Crows ("Strong - Reversal - Bearish Pattern - Down")'
                print(log_text, "\n")
                logging.debug(log_text)

                app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') ' + log_text)

            if morning_star is True:
                log_text = '*** Candlestick Detected: Morning Star ("Strong - Reversal - Bullish Pattern - Up")'
                print(log_text, "\n")
                logging.debug(log_text)

                app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') ' + log_text)

            if evening_star is True:
                log_text = '*** Candlestick Detected: Evening Star ("Strong - Reversal - Bearish Pattern - Down")'
                print(log_text, "\n")
                logging.debug(log_text)

                app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') ' + log_text)

            if three_line_strike is True:
                log_text = '** Candlestick Detected: Three Line Strike ("Reliable - Reversal - Bullish Pattern - Up")'
                print(log_text, "\n")
                logging.debug(log_text)

                app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') ' + log_text)

            if abandoned_baby is True:
                log_text = '** Candlestick Detected: Abandoned Baby ("Reliable - Reversal - Bullish Pattern - Up")'
                print(log_text, "\n")
                logging.debug(log_text)

                app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') ' + log_text)

            if morning_doji_star is True:
                log_text = '** Candlestick Detected: Morning Doji Star ("Reliable - Reversal - Bullish Pattern - Up")'
                print(log_text, "\n")
                logging.debug(log_text)

                app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') ' + log_text)

            if evening_doji_star is True:
                log_text = '** Candlestick Detected: Evening Doji Star ("Reliable - Reversal - Bearish Pattern - Down")'
                print(log_text, "\n")
                logging.debug(log_text)

                app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') ' + log_text)

            if two_black_gapping is True:
                log_text = '*** Candlestick Detected: Two Black Gapping ("Reliable - Reversal - Bearish Pattern - Down")'
                print(log_text, "\n")
                logging.debug(log_text)

                app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') ' + log_text)


            # EMA12 prefix/suffix are aligned to 3 characters
            ema_co_prefix = '   '
            ema_co_suffix = '   '
            if ema12gtema26co is True:
                ema_co_prefix = '*^ '
                ema_co_suffix = ' ^*'
            elif ema12ltema26co is True:
                ema_co_prefix = '*v '
                ema_co_suffix = ' v*'
            elif ema12gtema26 is True:
                ema_co_prefix = ' ^ '
                ema_co_suffix = ' ^ '
            elif ema12ltema26 is True:
                ema_co_prefix = ' v '
                ema_co_suffix = ' v '

            macd_co_prefix = ''
            macd_co_suffix = ''
            if app.disableBuyMACD() is False:
                if macdgtsignalco is True:
                    macd_co_prefix = '*^ '
                    macd_co_suffix = ' ^* | '
                elif macdltsignalco is True:
                    macd_co_prefix = '*v '
                    macd_co_suffix = ' v* | '
                elif macdgtsignal is True:
                    macd_co_prefix = '^ '
                    macd_co_suffix = ' ^ | '
                elif macdltsignal is True:
                    macd_co_prefix = 'v '
                    macd_co_suffix = ' v | '

            obv_prefix = ''
            obv_suffix = ''
            if app.disableBuyOBV() is False:
                if float(obv_pc) > 0:
                    obv_prefix = '^ '
                    obv_suffix = ' ^ | '
                elif float(obv_pc) < 0:
                    obv_prefix = 'v '
                    obv_suffix = ' v | '

            if not app.isVerbose():
                if state.last_action != '':
                    output_text = formatted_current_df_index + ' | ' + app.getMarket() + bullbeartext + ' | ' + \
                                  app.printGranularity() + ' | ' + price_text + ' | ' + ema_co_prefix + \
                                  ema_text + ema_co_suffix + ' | ' + macd_co_prefix + macd_text + macd_co_suffix + \
                                  obv_prefix + obv_text + obv_suffix + state.eri_text + state.action + \
                                  ' | Last Action: ' + state.last_action
                else:
                    output_text = formatted_current_df_index + ' | ' + app.getMarket() + bullbeartext + ' | ' + \
                                  app.printGranularity() + ' | ' + price_text + ' | ' + ema_co_prefix + ema_text + \
                                  ema_co_suffix + ' | ' + macd_co_prefix + macd_text + macd_co_suffix + obv_prefix + \
                                  obv_text + obv_suffix + state.eri_text + state.action + ' '

                if state.last_action == 'BUY':
                    if state.last_buy_size > 0:
                        margin_text = truncate(margin) + '%'
                    else:
                        margin_text = '0%'

                    output_text += ' | ' + margin_text + ' (delta: ' + str(round(price - state.last_buy_price, precision)) + ')'

                logging.debug(output_text)

                if state.last_action == 'BUY':
                    # display support, resistance and fibonacci levels
                    print(ta.printSupportResistanceFibonacciLevels(price))

            else:
                logging.debug('-- Iteration: ' + str(state.iterations) + ' --' + bullbeartext)

                if state.last_action == 'BUY':
                    if state.last_buy_size > 0:
                        margin_text = truncate(margin) + '%'
                    else:
                        margin_text = '0%'

                    logging.debug('-- Margin: ' + margin_text + ' --')

                logging.debug('price: ' + truncate(price))
                logging.debug('ema12: ' + truncate(float(df_last['ema12'].values[0])))
                logging.debug('ema26: ' + truncate(float(df_last['ema26'].values[0])))
                logging.debug('ema12gtema26co: ' + str(ema12gtema26co))
                logging.debug('ema12gtema26: ' + str(ema12gtema26))
                logging.debug('ema12ltema26co: ' + str(ema12ltema26co))
                logging.debug('ema12ltema26: ' + str(ema12ltema26))
                logging.debug('sma50: ' + truncate(float(df_last['sma50'].values[0])))
                logging.debug('sma200: ' + truncate(float(df_last['sma200'].values[0])))
                logging.debug('macd: ' + truncate(float(df_last['macd'].values[0])))
                logging.debug('signal: ' + truncate(float(df_last['signal'].values[0])))
                logging.debug('macdgtsignal: ' + str(macdgtsignal))
                logging.debug('macdltsignal: ' + str(macdltsignal))
                logging.debug('obv: ' + str(obv))
                logging.debug('obv_pc: ' + str(obv_pc))
                logging.debug('action: ' + state.action)

                # informational output on the most recent entry  
                print('')
                print('================================================================================')
                txt = '        Iteration : ' + str(state.iterations) + bullbeartext
                print('|', txt, (' ' * (75 - len(txt))), '|')
                txt = '        Timestamp : ' + str(df_last.index.format()[0])
                print('|', txt, (' ' * (75 - len(txt))), '|')
                print('--------------------------------------------------------------------------------')
                txt = '            Close : ' + truncate(price)
                print('|', txt, (' ' * (75 - len(txt))), '|')
                txt = '            EMA12 : ' + truncate(float(df_last['ema12'].values[0]))
                print('|', txt, (' ' * (75 - len(txt))), '|')
                txt = '            EMA26 : ' + truncate(float(df_last['ema26'].values[0]))
                print('|', txt, (' ' * (75 - len(txt))), '|')
                txt = '   Crossing Above : ' + str(ema12gtema26co)
                print('|', txt, (' ' * (75 - len(txt))), '|')
                txt = '  Currently Above : ' + str(ema12gtema26)
                print('|', txt, (' ' * (75 - len(txt))), '|')
                txt = '   Crossing Below : ' + str(ema12ltema26co)
                print('|', txt, (' ' * (75 - len(txt))), '|')
                txt = '  Currently Below : ' + str(ema12ltema26)
                print('|', txt, (' ' * (75 - len(txt))), '|')

                if (ema12gtema26 is True and ema12gtema26co is True):
                    txt = '        Condition : EMA12 is currently crossing above EMA26'
                elif (ema12gtema26 is True and ema12gtema26co is False):
                    txt = '        Condition : EMA12 is currently above EMA26 and has crossed over'
                elif (ema12ltema26 is True and ema12ltema26co is True):
                    txt = '        Condition : EMA12 is currently crossing below EMA26'
                elif (ema12ltema26 is True and ema12ltema26co is False):
                    txt = '        Condition : EMA12 is currently below EMA26 and has crossed over'
                else:
                    txt = '        Condition : -'
                print('|', txt, (' ' * (75 - len(txt))), '|')

                txt = '            SMA20 : ' + truncate(float(df_last['sma20'].values[0]))
                print('|', txt, (' ' * (75 - len(txt))), '|')
                txt = '           SMA200 : ' + truncate(float(df_last['sma200'].values[0]))
                print('|', txt, (' ' * (75 - len(txt))), '|')

                print('--------------------------------------------------------------------------------')
                txt = '             MACD : ' + truncate(float(df_last['macd'].values[0]))
                print('|', txt, (' ' * (75 - len(txt))), '|')
                txt = '           Signal : ' + truncate(float(df_last['signal'].values[0]))
                print('|', txt, (' ' * (75 - len(txt))), '|')
                txt = '  Currently Above : ' + str(macdgtsignal)
                print('|', txt, (' ' * (75 - len(txt))), '|')
                txt = '  Currently Below : ' + str(macdltsignal)
                print('|', txt, (' ' * (75 - len(txt))), '|')

                if (macdgtsignal is True and macdgtsignalco is True):
                    txt = '        Condition : MACD is currently crossing above Signal'
                elif (macdgtsignal is True and macdgtsignalco is False):
                    txt = '        Condition : MACD is currently above Signal and has crossed over'
                elif (macdltsignal is True and macdltsignalco is True):
                    txt = '        Condition : MACD is currently crossing below Signal'
                elif (macdltsignal is True and macdltsignalco is False):
                    txt = '        Condition : MACD is currently below Signal and has crossed over'
                else:
                    txt = '        Condition : -'
                print('|', txt, (' ' * (75 - len(txt))), '|')

                print('--------------------------------------------------------------------------------')
                txt = '           Action : ' + state.action
                print('|', txt, (' ' * (75 - len(txt))), '|')
                print('================================================================================')
                if state.last_action == 'BUY':
                    txt = '           Margin : ' + margin_text
                    print('|', txt, (' ' * (75 - len(txt))), '|')
                    print('================================================================================')

            # if a buy signal
            if state.action == 'BUY':
                state.last_buy_price = price
                state.last_buy_high = state.last_buy_price

                # if live
                if app.isLive():
                    app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') BUY at ' + price_text)

                    if not app.isVerbose():
                        logging.debug(formatted_current_df_index + ' | ' + app.getMarket() + ' | ' + app.printGranularity() +
                                     ' | ' + price_text + ' | BUY')
                        print("\n", formatted_current_df_index, '|', app.getMarket(), app.printGranularity(), '|', price_text,
                              '| BUY', "\n")
                    else:
                        print('--------------------------------------------------------------------------------')
                        print('|                      *** Executing LIVE Buy Order ***                        |')
                        print('--------------------------------------------------------------------------------')

                    # display balances
                    print(app.getBaseCurrency(), 'balance before order:', account.getBalance(app.getBaseCurrency()))
                    print(app.getQuoteCurrency(), 'balance before order:', account.getBalance(app.getQuoteCurrency()))

                    # execute a live market buy
                    state.last_buy_size = float(account.getBalance(app.getQuoteCurrency()))
                    if app.getBuyMaxSize() and state.last_buy_size > app.getBuyMaxSize():
                        state.last_buy_size = app.getBuyMaxSize()

                    resp = app.marketBuy(app.getMarket(), state.last_buy_size, app.getBuyPercent())
                    logging.debug(resp)

                    # display balances
                    print(app.getBaseCurrency(), 'balance after order:', account.getBalance(app.getBaseCurrency()))
                    print(app.getQuoteCurrency(), 'balance after order:', account.getBalance(app.getQuoteCurrency()))
                # if not live
                else:
                    app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') TEST BUY at ' + price_text)
                    # TODO: Improve simulator calculations by including calculations for buy and sell limit configurations. 
                    if state.last_buy_size == 0 and state.last_buy_filled == 0: 
                        state.last_buy_size = 1000
                        state.first_buy_size = 1000

                    state.buy_count = state.buy_count + 1
                    state.buy_sum = state.buy_sum + state.last_buy_size    

                    if not app.isVerbose():
                        logging.debug(formatted_current_df_index + ' | ' + app.getMarket() + ' | ' + app.printGranularity() +
                                     ' | ' + price_text + ' | BUY')
                        print("\n", formatted_current_df_index, '|', app.getMarket(), app.printGranularity(), '|', price_text, '| BUY')

                        bands = ta.getFibonacciRetracementLevels(float(price))
                        print(' Fibonacci Retracement Levels:', str(bands))
                        ta.printSupportResistanceLevel(float(price))

                        if len(bands) >= 1 and len(bands) <= 2:
                            if len(bands) == 1:
                                first_key = list(bands.keys())[0]
                                if first_key == 'ratio1':
                                    state.fib_low = 0
                                    state.fib_high = bands[first_key]
                                if first_key == 'ratio1_618':
                                    state.fib_low = bands[first_key]
                                    state.fib_high = bands[first_key] * 2
                                else:
                                    state.fib_low = bands[first_key]

                            elif len(bands) == 2:
                                first_key = list(bands.keys())[0]
                                second_key = list(bands.keys())[1]
                                state.fib_low = bands[first_key]
                                state.fib_high = bands[second_key]

                    else:
                        print('--------------------------------------------------------------------------------')
                        print('|                      *** Executing TEST Buy Order ***                        |')
                        print('--------------------------------------------------------------------------------')

                if app.shouldSaveGraphs():
                    tradinggraphs = TradingGraphs(ta)
                    ts = datetime.now().timestamp()
                    filename = app.getMarket() + '_' + app.printGranularity() + '_buy_' + str(ts) + '.png'
                    tradinggraphs.renderEMAandMACD(len(trading_data), 'graphs/' + filename, True)

            # if a sell signal
            elif state.action == 'SELL':
                # if live
                if app.isLive():
                    app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') SELL at ' +
                                      price_text + ' (margin: ' + margin_text + ', (delta: ' +
                                      str(round(price - state.last_buy_price, precision)) + ')')

                    if not app.isVerbose():
                        logging.debug(formatted_current_df_index + ' | ' + app.getMarket() + ' | ' + app.printGranularity() +
                                     ' | ' + price_text + ' | SELL')
                        print("\n", formatted_current_df_index, '|', app.getMarket(), app.printGranularity(), '|', price_text, '| SELL')

                        bands = ta.getFibonacciRetracementLevels(float(price))
                        print(' Fibonacci Retracement Levels:', str(bands), "\n")

                        if len(bands) >= 1 and len(bands) <= 2:
                            if len(bands) == 1:
                                first_key = list(bands.keys())[0]
                                if first_key == 'ratio1':
                                    state.fib_low = 0
                                    state.fib_high = bands[first_key]
                                if first_key == 'ratio1_618':
                                    state.fib_low = bands[first_key]
                                    state.fib_high = bands[first_key] * 2
                                else:
                                    state.fib_low = bands[first_key]

                            elif len(bands) == 2:
                                first_key = list(bands.keys())[0]
                                second_key = list(bands.keys())[1]
                                state.fib_low = bands[first_key]
                                state.fib_high = bands[second_key]

                    else:
                        print('--------------------------------------------------------------------------------')
                        print('|                      *** Executing LIVE Sell Order ***                        |')
                        print('--------------------------------------------------------------------------------')

                    # display balances
                    print(app.getBaseCurrency(), 'balance before order:', account.getBalance(app.getBaseCurrency()))
                    print(app.getQuoteCurrency(), 'balance before order:', account.getBalance(app.getQuoteCurrency()))

                    # execute a live market sell
                    resp = app.marketSell(app.getMarket(), float(account.getBalance(app.getBaseCurrency())),
                                          app.getSellPercent())
                    logging.debug(resp)

                    # display balances
                    print(app.getBaseCurrency(), 'balance after order:', account.getBalance(app.getBaseCurrency()))
                    print(app.getQuoteCurrency(), 'balance after order:', account.getBalance(app.getQuoteCurrency()))

                # if not live
                else:
                    margin, profit, sell_fee = calculate_margin(
                        buy_size=state.last_buy_size, 
                        buy_filled=state.last_buy_filled, 
                        buy_price=state.last_buy_price, 
                        buy_fee=state.last_buy_fee, 
                        sell_percent=app.getSellPercent(), 
                        sell_price=price, 
                        sell_taker_fee=app.getTakerFee(), 
                        debug=False)

                    if state.last_buy_size > 0:
                        margin_text = truncate(margin) + '%'
                    else:
                        margin_text = '0%'
                    app.notifyTelegram(app.getMarket() + ' (' + app.printGranularity() + ') TEST SELL at ' +
                                      price_text + ' (margin: ' + margin_text + ', (delta: ' +
                                      str(round(price - state.last_buy_price, precision)) + ')')

                    # Preserve next buy values for simulator
                    state.sell_count = state.sell_count + 1
                    buy_size = ((app.getSellPercent() / 100) * ((price / state.last_buy_price) * (state.last_buy_size - state.last_buy_fee)))
                    state.last_buy_size = buy_size - sell_fee
                    state.sell_sum = state.sell_sum + state.last_buy_size

                    if not app.isVerbose():
                        if price > 0:
                            margin_text = truncate(margin) + '%'
                        else:
                            margin_text = '0%'

                        logging.debug(formatted_current_df_index + ' | ' + app.getMarket() + ' ' +
                                     app.printGranularity() + ' | SELL | ' + str(price) + ' | BUY | ' +
                                     str(state.last_buy_price) + ' | DIFF | ' + str(price - state.last_buy_price) +
                                     ' | DIFF | ' + str(profit) + ' | MARGIN NO FEES | ' +
                                     margin_text + ' | MARGIN FEES | ' + str(sell_fee))
                        print("\n", formatted_current_df_index, '|', app.getMarket(), app.printGranularity(), '| SELL |',
                              str(price), '| BUY |', str(state.last_buy_price), '| DIFF |', str(price - state.last_buy_price), '| DIFF |', str(profit),
                              '| MARGIN NO FEES |', margin_text, '| MARGIN FEES |', str(round(sell_fee, precision)), "\n")

                    else:
                        print('--------------------------------------------------------------------------------')
                        print('|                      *** Executing TEST Sell Order ***                        |')
                        print('--------------------------------------------------------------------------------')

                if app.shouldSaveGraphs():
                    tradinggraphs = TradingGraphs(ta)
                    ts = datetime.now().timestamp()
                    filename = app.getMarket() + '_' + app.printGranularity() + '_sell_' + str(ts) + '.png'
                    tradinggraphs.renderEMAandMACD(len(trading_data), 'graphs/' + filename, True)

            # last significant action
            if state.action in ['BUY', 'SELL']:
                state.last_action = state.action

            state.last_df_index = str(df_last.index.format()[0])

            if not app.isLive() and state.iterations == len(df):
                print("\nSimulation Summary\n")

                if state.buy_count > state.sell_count and app.allowSellAtLoss():
                    # Calculate last sell size
                    state.last_buy_size = ((app.getSellPercent() / 100) * ((price / state.last_buy_price) * (state.last_buy_size - state.last_buy_fee)))
                    # Reduce sell fee from last sell size
                    state.last_buy_size = state.last_buy_size - state.last_buy_price * app.getTakerFee()
                    state.sell_sum = state.sell_sum + state.last_buy_size
                    state.sell_count = state.sell_count + 1

                elif state.buy_count > state.sell_count and not app.allowSellAtLoss():
                    print('        Note : "sell at loss" is disabled and you have an open trade, if the margin')
                    print('               result below is negative it will assume you sold at the end of the')
                    print('               simulation which may not be ideal. Try setting --sellatloss 1', "\n")


                print ('   Buy Count :', state.buy_count)                
                print ('  Sell Count :', state.sell_count)
                print ('   First Buy :', state.first_buy_size)
                print ('   Last Sell :', state.last_buy_size)

                app.notifyTelegram(f"Simulation Summary\n   Buy Count: {state.buy_count}\n   Sell Count: {state.sell_count}\n   First Buy: {state.first_buy_size}\n   Last Sell: {state.last_buy_size}\n")

                if state.sell_count > 0:
                    print ('      Margin :', _truncate((((state.last_buy_size - state.first_buy_size) / state.first_buy_size) * 100), 4) + '%', "\n")

                    print('  ** non-live simulation, assuming highest fees', "\n")
                    app.notifyTelegram(f"      Margin: {_truncate((((state.last_buy_size - state.first_buy_size) / state.first_buy_size) * 100), 4)}%\n  ** non-live simulation, assuming highest fees\n")


        else:
            print(now, '|', app.getMarket() + bullbeartext, '|', app.printGranularity(), '| Current Price:', price)

            # decrement ignored iteration
            state.iterations = state.iterations - 1

        # if live
        if not app.disableTracker() and app.isLive():
            # update order tracker csv
            if app.getExchange() == 'binance':
                account.saveTrackerCSV(app.getMarket())
            elif app.getExchange() == 'coinbasepro':
                account.saveTrackerCSV()

        if app.isSimulation():
            if state.iterations < 300:
                if app.simuluationSpeed() in ['fast', 'fast-sample']:
                    # fast processing
                    list(map(s.cancel, s.queue))
                    s.enter(0, 1, executeJob, (sc, app, state, trading_data))
                else:
                    # slow processing
                    list(map(s.cancel, s.queue))
                    s.enter(1, 1, executeJob, (sc, app, state, trading_data))

        else:
            # poll every 2 minutes
            list(map(s.cancel, s.queue))
            s.enter(120, 1, executeJob, (sc, app, state))


def main():
    try:
        # initialise logging
        logging.basicConfig(
            #filename=app.getLogFile(),
            #format='%(asctime)s - %(levelname)s: %(message)s',
            format='%(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p',
            filemode='a',
            level=logging.DEBUG,
            force=True
        )

        message = 'Starting '
        if app.getExchange() == 'coinbasepro':
            message += 'Coinbase Pro bot'
        elif app.getExchange() == 'binance':
            message += 'Binance bot'

        message += ' for ' + app.getMarket() + ' using granularity ' + app.printGranularity()
        app.notifyTelegram(message)

        # initialise and start application
        trading_data = app.startApp(account, state.last_action)

        def runApp():
            # run the first job immediately after starting
            if app.isSimulation():
                executeJob(s, app, state, trading_data)
            else:
                executeJob(s, app, state)

            s.run()

        try:
            runApp()
        except KeyboardInterrupt:
            raise
        except:
            if app.autoRestart():
                # Wait 30 second and try to relaunch application
                time.sleep(30)
                print('Restarting application after exception...')

                app.notifyTelegram('Auto restarting bot for ' + app.getMarket() + ' after exception')

                # Cancel the events queue
                map(s.cancel, s.queue)

                # Restart the app
                runApp()
            else:
                raise

    # catches a keyboard break of app, exits gracefully
    except KeyboardInterrupt:
        print(datetime.now(), 'closed')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    except(BaseException, Exception) as e:
        # catch all not managed exceptions and send a Telegram message if configured
        app.notifyTelegram('Bot for ' + app.getMarket() + ' got an exception: ' + repr(e))

        print(repr(e))

        raise


main()