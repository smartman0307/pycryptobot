"""Python Crypto Bot consuming Coinbase Pro API

DISCLAIMER -- PLEASE READ!

I developed this crypto trading bot for myself. I'm happy to share the project and code with others
but I don't take responsibility for how it performs for you or any potential losses incurred due to
market conditions or even bugs. I'm using this bot myself and will keep improving it so please make
sure you are pulling the repo often for updates and bug fixes ("git pull"). 

USAGE

You are free to use this app and code however you wish. I know others who are using some of my code
in their personal projects and I'm fine with that. I do however have a polite request and that is
if you improve on my code to share it with me. You may have found this project via Medium where I am
a writer (https://whittle.medium.com). I would really appreciate it if you follow me and read and 
"clap" for my articles (especially related to this project). I get paid by Medium for my articles
so that is one way you can reward me for my efforts without actually spending anything. If you 
would like to share and promote my articles I would also really appreciate it.

IMPORTANT

In order to limit exposure by the trading bot, in your Coinbase Pro profile I suggest you create
another "Portfolio" dedicted for this trading bot. Create your API keys associated with the
"Trading Bot" portfolio and only keep funds you want to give the bot access to in the portfolio.
That way if anything goes wrong only what is within this portfolio is at risk!
"""

import pandas as pd
from datetime import datetime
import argparse, json, logging, math, os, re, sched, sys, time
from models.Trading import TechnicalAnalysis
from models.TradingAccount import TradingAccount
from models.CoinbasePro import AuthAPI, PublicAPI

# instantiate the arguments parser
parser = argparse.ArgumentParser(description='Python Crypto Bot using the Coinbase Pro API')

# optional arguments
parser.add_argument('--granularity', type=int, help='Optionally provide granularity via arguments')
parser.add_argument('--live', type=int, help='Optionally provide live status via arguments')
parser.add_argument('--market', type=str, help='Optionally provide market via arguments')
parser.add_argument('--sim', type=str, help='Optionally provide simulation status via arguments ("fast", "slow")')
parser.add_argument('--verbose', type=int, help='Optionally provide verbose status via arguments')

# parse arguments
args = parser.parse_args()

"""Settings"""

if args.live == None:
    # default live status

    # 0 is test/demo, 1 is live
    is_live = 0
else:
    # live status set via --live argument

    if args.live == 1:
        is_live = 1
    else:
        is_live = 0

if args.sim == None:
    # default simulation status

    # 0 is normal, 1 is simulation
    is_sim = 0
    sim_speed = ''
else:
    # sim status set via --sim argument

    if args.sim == 'fast':
        is_sim = 1
        sim_speed = 'fast'
        is_live = 0
    elif args.sim == 'slow':
        is_sim = 1
        sim_speed = 'slow'
        is_live = 0
    else:
        is_sim = 0
        sim_speed = ''

if args.market == None:
    # default market

    # the crypto market you wish you trade
    cryptoMarket = 'BTC'

    # the source of funds for your trading
    fiatMarket = 'GBP'
else:
    # market set via --market argument

    # validates the market is syntactically correct
    p = re.compile(r"^[A-Z]{3,4}\-[A-Z]{3,4}$")
    if not p.match(args.market):
        raise TypeError('Coinbase Pro market required.')

    cryptoMarket, fiatMarket = args.market.split('-',2)

if args.granularity == None:
    # default granularity

    # supported granularity (recommended 3600 for 1 hour interval for day trading)
    granularity = 3600  # 1 hour
else:
    # granularity set via --granularity argument

    # validates granularity is an integer
    if not isinstance(args.granularity, int):
        raise TypeError('Granularity integer required.')

    # validates the granularity is supported by Coinbase Pro
    if not args.granularity in [60, 300, 900, 3600, 21600, 86400]:
        raise TypeError('Granularity options: 60, 300, 900, 3600, 21600, 86400.')
        
    granularity = args.granularity

if args.verbose == None:
    # default verbose status

    # 0 is minimal, 1 is verbose
    is_verbose = 1
else:
    # verbose status set via --verbose argument

    if args.verbose == 1:
        is_verbose = 1
    else:
        is_verbose = 0

"""Highly advisable not to change any code below this point!"""

# validation of crypto market inputs
if cryptoMarket not in ['BCH', 'BTC', 'ETH', 'LTC']:
    raise Exception('Invalid crypto market: BCH, BTC, ETH, LTC or ETH')

# validation of fiat market inputs
if fiatMarket not in ['EUR', 'GBP', 'USD']:
    raise Exception('Invalid FIAT market: EUR, GBP, USD')

# reconstruct the market based on the crypto and fiat inputs
market = cryptoMarket + '-' + fiatMarket

# initial state is to wait
action = 'WAIT'
last_action = ''
last_df_index = ''
iterations = 0
x_since_buy = 0
x_since_sell = 0

config = {}
account = None
# if live trading is enabled
if is_live == 1:
    # open the config.json file
    with open('config.json') as config_file:
        # store the configuration in dictionary
        config = json.load(config_file)
    # connect your Coinbase Pro live account
    account = TradingAccount(config)

    # if the bot is restarted between a buy and sell it will sell first
    if (account.getBalance(fiatMarket) == 0 and account.getBalance(cryptoMarket) > 0):
        last_action = 'BUY'

def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n

def compare(val1, val2, label=''):
    if val1 > val2:
        if label == '':
            return str(truncate(val1, 2)) + ' > ' + str(truncate(val2, 2))
        else:
            return label + ': ' + str(truncate(val1, 2)) + ' > ' + str(truncate(val2, 2))
    if val1 < val2:
        if label == '':
            return str(truncate(val1, 2)) + ' < ' + str(truncate(val2, 2))
        else:
            return label + ': ' + str(truncate(val1, 2)) + ' < ' + str(truncate(val2, 2))
    else:
        if label == '':
            return str(truncate(val1, 2)) + ' = ' + str(truncate(val2, 2))
        else:
            return label + ': ' + str(truncate(val1, 2)) + ' = ' + str(truncate(val2, 2))      

def executeJob(sc, market, granularity, tradingData=pd.DataFrame()):
    """Trading bot job which runs at a scheduled interval"""
    global action, iterations, x_since_buy, x_since_sell, last_action, last_df_index

    # increment iterations
    iterations = iterations + 1

    if is_sim == 0:
        # retrieve the market data
        api = PublicAPI()
        tradingData = api.getHistoricalData(market, granularity)

    # analyse the market data
    tradingDataCopy = tradingData.copy()
    technicalAnalysis = TechnicalAnalysis(tradingDataCopy)
    technicalAnalysis.addAll()
    df = technicalAnalysis.getDataFrame()

    if len(df) != 300:
        # data frame should have 300 rows, if not retry
        print('error: data frame length is < 300 (' + str(len(df)) + ')')
        logging.error('error: data frame length is < 300 (' + str(len(df)) + ')')
        s.enter(300, 1, executeJob, (sc, market, granularity))

    if is_sim == 1:
        # with a simulation df_last will iterate through data
        df_last = df.iloc[iterations-1:iterations]
    else:
        # df_last contains the most recent entry
        df_last = df.tail(1)
 
    ema12gtema26 = bool(df_last['ema12gtema26'].values[0])
    ema12gtema26co = bool(df_last['ema12gtema26co'].values[0])
    macdgtsignal = bool(df_last['macdgtsignal'].values[0])
    macdgtsignalco = bool(df_last['macdgtsignalco'].values[0])
    ema12ltema26 = bool(df_last['ema12ltema26'].values[0])
    ema12ltema26co = bool(df_last['ema12ltema26co'].values[0])
    macdltsignal = bool(df_last['macdltsignal'].values[0])
    macdltsignalco = bool(df_last['macdltsignalco'].values[0])
    obv = float(df_last['obv'].values[0])
    obv_pc = float(df_last['obv_pc'].values[0])

    # criteria for a buy signal
    if ((ema12gtema26co == True and macdgtsignal == True and obv_pc > 0.1) or (ema12gtema26 == True and macdgtsignal == True and obv_pc > 0.1 and x_since_buy > 0 and x_since_buy <= 2)) and last_action != 'BUY':
        action = 'BUY'
    # criteria for a sell signal
    elif (ema12ltema26co == True and macdltsignal == True) and last_action not in ['','SELL']:
        action = 'SELL'
    # anything other than a buy or sell, just wait
    else:
        action = 'WAIT'

    # polling is every 5 minutes (even for hourly intervals), but only process once per interval
    if (last_df_index != df_last.index.format()):
        ts_text = str(df_last.index.format()[0])
        price_text = 'Price: ' + str(truncate(float(df_last['close'].values[0]), 2))
        ema_text = compare(df_last['ema12'].values[0], df_last['ema26'].values[0], 'EMA12/26')
        macd_text = compare(df_last['macd'].values[0], df_last['signal'].values[0], 'MACD')
        obv_text = compare(df_last['obv_pc'].values[0], 0, 'OBV %')
        counter_text = '[I:' + str(iterations) + ',B:' + str(x_since_buy) + ',S:' + str(x_since_sell) + ']'
 
        ema_co_prefix = ''
        ema_co_suffix = ''
        if ema12gtema26co == True or ema12ltema26co == True:
            ema_co_prefix = '* '
            ema_co_suffix = ' *'

        macd_co_prefix = ''
        macd_co_suffix = ''
        if macdgtsignalco == True or macdltsignalco == True:
            macd_co_prefix = '* '
            macd_co_suffix = ' *'

        if is_verbose == 0:
            output_text = ts_text + ' | ' + price_text + ' | ' + ema_co_prefix + ema_text + ema_co_suffix + ' | ' + macd_co_prefix + macd_text + macd_co_suffix + ' | ' + obv_text + ' | ' + action + ' ' + counter_text
            logging.debug(output_text)
            print (output_text)
        else:
            logging.debug('-- Iteration: ' + str(iterations) + ' --')
            logging.debug('-- Since Last Buy: ' + str(x_since_buy) + ' --')
            logging.debug('-- Since Last Sell: ' + str(x_since_sell) + ' --')
            
            logging.debug('price: ' + str(truncate(float(df_last['close'].values[0]), 2)))
            logging.debug('ema12: ' + str(truncate(float(df_last['ema12'].values[0]), 2)))
            logging.debug('ema26: ' + str(truncate(float(df_last['ema26'].values[0]), 2)))
            logging.debug('ema12gtema26co: ' + str(ema12gtema26co))
            logging.debug('ema12gtema26: ' + str(ema12gtema26))
            logging.debug('ema12ltema26co: ' + str(ema12ltema26co))
            logging.debug('ema12ltema26: ' + str(ema12ltema26))
            logging.debug('macd: ' + str(truncate(float(df_last['macd'].values[0]), 2)))
            logging.debug('signal: ' + str(truncate(float(df_last['signal'].values[0]), 2)))
            logging.debug('macdgtsignal: ' + str(macdgtsignal))
            logging.debug('macdltsignal: ' + str(macdltsignal))
            logging.debug('obv: ' + str(obv))
            logging.debug('obv_pc: ' + str(obv_pc) + '%')
            logging.debug('action: ' + action)

            # informational output on the most recent entry  
            print('')
            print('================================================================================')
            txt = '        Iteration : ' + str(iterations)
            print('|', txt, (' ' * (75 - len(txt))), '|')
            txt = '   Since Last Buy : ' + str(x_since_buy)
            print('|', txt, (' ' * (75 - len(txt))), '|')
            txt = '  Since Last Sell : ' + str(x_since_sell)
            print('|', txt, (' ' * (75 - len(txt))), '|')
            txt = '        Timestamp : ' + str(df_last.index.format()[0])
            print('|', txt, (' ' * (75 - len(txt))), '|')
            print('--------------------------------------------------------------------------------')
            txt = '            EMA12 : ' + str(truncate(float(df_last['ema12'].values[0]), 2))
            print('|', txt, (' ' * (75 - len(txt))), '|')
            txt = '            EMA26 : ' + str(truncate(float(df_last['ema26'].values[0]), 2))
            print('|', txt, (' ' * (75 - len(txt))), '|')
            txt = '   Crossing Above : ' + str(ema12gtema26co)
            print('|', txt, (' ' * (75 - len(txt))), '|')
            txt = '  Currently Above : ' + str(ema12gtema26)
            print('|', txt, (' ' * (75 - len(txt))), '|')
            txt = '   Crossing Below : ' + str(ema12ltema26co)
            print('|', txt, (' ' * (75 - len(txt))), '|')
            txt = '  Currently Below : ' + str(ema12ltema26)
            print('|', txt, (' ' * (75 - len(txt))), '|')

            if (ema12gtema26 == True and ema12gtema26co == True):
                txt = '        Condition : EMA12 is currently crossing above EMA26'
            elif (ema12gtema26 == True and ema12gtema26co == False):
                txt = '        Condition : EMA12 is currently above EMA26 and has crossed over'
            elif (ema12ltema26 == True and ema12ltema26co == True):
                txt = '        Condition : EMA12 is currently crossing below EMA26'
            elif (ema12ltema26 == True and ema12ltema26co == False):
                txt = '        Condition : EMA12 is currently below EMA26 and has crossed over'
            else:
                txt = '        Condition : -'
            print('|', txt, (' ' * (75 - len(txt))), '|')

            print('--------------------------------------------------------------------------------')
            txt = '             MACD : ' + str(truncate(float(df_last['macd'].values[0]), 2))
            print('|', txt, (' ' * (75 - len(txt))), '|')
            txt = '           Signal : ' + str(truncate(float(df_last['signal'].values[0]), 2))
            print('|', txt, (' ' * (75 - len(txt))), '|')
            txt = '  Currently Above : ' + str(macdgtsignal)
            print('|', txt, (' ' * (75 - len(txt))), '|')
            txt = '  Currently Below : ' + str(macdltsignal)
            print('|', txt, (' ' * (75 - len(txt))), '|')

            if (macdgtsignal == True and macdgtsignalco == True):
                txt = '        Condition : MACD is currently crossing above Signal'
            elif (macdgtsignal == True and macdgtsignalco == False):
                txt = '        Condition : MACD is currently above Signal and has crossed over'
            elif (macdltsignal == True and macdltsignalco == True):
                txt = '        Condition : MACD is currently crossing below Signal'
            elif (macdltsignal == True and macdltsignalco == False):
                txt = '        Condition : MACD is currently below Signal and has crossed over'
            else:
                txt = '        Condition : -'
            print('|', txt, (' ' * (75 - len(txt))), '|')

            print('--------------------------------------------------------------------------------')
            txt = '              OBV : ' + str(truncate(obv, 4))
            print('|', txt, (' ' * (75 - len(txt))), '|')
            txt = '       OBV Change : ' + str(obv_pc) + '%'
            print('|', txt, (' ' * (75 - len(txt))), '|')

            if (obv_pc >= 2):
                txt = '        Condition : Large positive volume changes'
            elif (obv_pc < 2 and obv_pc >= 0):
                txt = '        Condition : Positive volume changes'
            else:
                txt = '        Condition : Negative volume changes'
            print('|', txt, (' ' * (75 - len(txt))), '|')

            print('--------------------------------------------------------------------------------')
            txt = '           Action : ' + action
            print('|', txt, (' ' * (75 - len(txt))), '|')
            print('================================================================================')

        if last_action == 'BUY':
            x_since_buy = x_since_buy + 1
        elif last_action == 'SELL':
            x_since_sell = x_since_sell + 1

        # if a buy signal
        if action == 'BUY':
            # increment x since buy
            x_since_buy = x_since_buy + 1

            # reset x since sell
            x_since_sell = 0

            # if live
            if is_live == 1:
                if is_verbose == 0:
                    logging.info(ts_text + ' | ' + market + ' ' + str(granularity) + ' | ' + price_text + ' | BUY')
                    print (ts_text, '|', market, granularity, '|', price_text, '| BUY')                    
                else:
                    print('--------------------------------------------------------------------------------')
                    print('|                      *** Executing LIVE Buy Order ***                        |')
                    print('--------------------------------------------------------------------------------')
                # connect to coinbase pro api (authenticated)
                model = AuthAPI(config['api_key'], config['api_secret'], config['api_pass'], config['api_url'])
                # execute a live market buy
                resp = model.marketBuy(market, float(account.getBalance(fiatMarket)))
                logging.info(resp)
                #logging.info('attempt to buy ' + resp['specified_funds'] + ' (' + resp['funds'] + ' after fees) of ' + resp['product_id'])
            # if not live
            else:
                if is_verbose == 0:
                    logging.info(ts_text + ' | ' + market + ' ' + str(granularity) + ' | ' + price_text + ' | BUY')
                    print (ts_text, '|', market, granularity, '|', price_text, '| BUY')                    
                else:
                    print('--------------------------------------------------------------------------------')
                    print('|                      *** Executing TEST Buy Order ***                        |')
                    print('--------------------------------------------------------------------------------')
            #print(df_last[['close','ema12','ema26','ema12gtema26','ema12gtema26co','macd','signal','macdgtsignal','obv','obv_pc']])

        # if a sell signal
        elif action == 'SELL':
            # increment x since buy
            x_since_sell = x_since_sell + 1

            # reset x since buy
            x_since_buy = 0

            # if live
            if is_live == 1:
                if is_verbose == 0:
                    logging.info(ts_text + ' | ' + market + ' ' + str(granularity) + ' | ' + price_text + ' | SELL')
                    print (ts_text, '|', market, granularity, '|', price_text, '| SELL')                    
                else:
                    print('--------------------------------------------------------------------------------')
                    print('|                      *** Executing LIVE Sell Order ***                        |')
                    print('--------------------------------------------------------------------------------')
                # connect to Coinbase Pro API live
                model = AuthAPI(config['api_key'], config['api_secret'], config['api_pass'], config['api_url'])
                # execute a live market sell
                resp = model.marketSell(market, float(account.getBalance(cryptoMarket)))
                logging.info(resp)
                #logging.info('attempt to sell ' + resp['size'] + ' of ' + resp['product_id'])
            # if not live
            else:
                if is_verbose == 0:
                    logging.info(ts_text + ' | ' + market + ' ' + str(granularity) + ' | ' + price_text + ' | SELL')
                    print (ts_text, '|', market, granularity, '|', price_text, '| SELL')                    
                else:
                    print('--------------------------------------------------------------------------------')
                    print('|                      *** Executing TEST Sell Order ***                        |')
                    print('--------------------------------------------------------------------------------')
            #print(df_last[['close','ema12','ema26','ema12ltema26','ema12ltema26co','macd','signal','macdltsignal','obv','obv_pc']])

        # last significant action
        if action in ['BUY','SELL']:
            last_action = action
        
        last_df_index = df_last.index.format()

    # if live
    if is_live == 1:
        # save csv with orders for market that are 'done'
        orders = account.getOrders(market, '', 'done')
        orders.to_csv('orders.csv', index=False)

    if is_sim == 1:
        if iterations < 300:
            if sim_speed == 'fast':
                # fast processing
                executeJob(sc, market, granularity, tradingData)
            else:
                # slow processing
                s.enter(1, 1, executeJob, (sc, market, granularity, tradingData))
    else:
        # poll every 5 minutes
        s.enter(300, 1, executeJob, (sc, market, granularity))

try:
    logging.basicConfig(filename='pycryptobot.log', format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filemode='a', level=logging.DEBUG)

    print('--------------------------------------------------------------------------------')
    print('|                Python Crypto Bot using the Coinbase Pro API                  |')
    print('--------------------------------------------------------------------------------')   
    txt = '           Market : ' + market
    print('|', txt, (' ' * (75 - len(txt))), '|')
    txt = '      Granularity : ' + str(granularity) + ' minutes'
    print('|', txt, (' ' * (75 - len(txt))), '|')
    print('--------------------------------------------------------------------------------')

    if is_live == 1:
        txt = '         Bot Mode : LIVE - live trades using your funds!'
    else:
        txt = '         Bot Mode : TEST - test trades using dummy funds :)'

    print('|', txt, (' ' * (75 - len(txt))), '|')

    txt = '      Bot Started : ' + str(datetime.now())
    print('|', txt, (' ' * (75 - len(txt))), '|')
    print('================================================================================')

    # if live
    if is_live == 1:
        # if live, ensure sufficient funds to place next buy order
        if last_action == '' and account.getBalance(fiatMarket) == 0:
            raise Exception('Insufficient ' + fiatMarket + ' funds to place next buy order!')
        # if live, ensure sufficient crypto to place next sell order
        elif last_action == 'BUY' and account.getBalance(cryptoMarket) == 0:
            raise Exception('Insufficient ' + cryptoMarket + ' funds to place next sell order!')

    s = sched.scheduler(time.time, time.sleep)
    # run the first job immediately after starting
    if is_sim == 1:
        api = PublicAPI()
        tradingData = api.getHistoricalData(market, granularity)
        executeJob(s, market, granularity, tradingData)
    else: 
        executeJob(s, market, granularity)
    
    s.run()

# catches a keyboard break of app, exits gracefully
except KeyboardInterrupt:
    print(datetime.now(), 'closed')
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)