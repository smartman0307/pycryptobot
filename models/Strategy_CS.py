from models.PyCryptoBot import PyCryptoBot
from models.PyCryptoBot import truncate as _truncate
from models.helper.LogHelper import Logger
from models.AppState import AppState

class Strategy_CS:
    def __init__(self, app: PyCryptoBot = None, state: AppState = AppState) -> None:
        self.app = app
        self.state = state

        if state.pandas_ta_enabled is False:
            raise ImportError("This Custom Strategy requires pandas_ta, but pandas_ta module is not loaded. Are requirements-advanced.txt modules installed?")

    def tradeSignals(self, data, _df):

        """ 
        #############################################################################################
        If customizing this file it is recommended to make a copy of and name it Strategy_myCS.py
        It will be loaded automatically if pandas-ta is enabled in configuration and it will not
        be overwritten by future updates.
        #############################################################################################
        """

        # buy indicators - using non-traditional settings
        # *** currently requires pandas-ta module and optional talib 

        # will output indicator values in log and telgram when True
        debug = True

        # max possible points - if sell_trigger_override setting is True, this value is used
        self.max_pts = 11
        # total points required to buy
        self.pts_to_buy = 8 # more points requires more signals to activate and less risky
        # total points to trigger immediate buy pcnt if configured, if not, this is ignored
        self.immed_buy_pts = 10

        # total points required to sell
        self.pts_to_sell = 3 # only requiring a couple pts will get sell signal quicker
        # total points to trigger immediate sell pcnt if configured, if not, this is ignored
        self.immed_sell_pts = 6

        # Required signals.
        # Specify how many have to be triggered
        # Buys - currently, RSI, OBV, MACDL - add self.pts_sig_required_buy += 1 to each one
        self.sig_required_buy = 3
        # Sells - currently EMA/WMA, MACDLead - self.pts_sig_required_sell += 1
        self.sig_required_sell = 0 # set to 0 for default

        # start at 0
        self.buy_pts = 0
        self.sell_pts = 0
        self.pts_sig_required_buy = 0
        self.pts_sig_required_sell = 0

        # RSI with VWMA, percent RSI is above MA for strength
        if ( # Buy when RSI is increasing and above MA by 10%
            data["rsi_ma_pcnt"].values[0] > 10
            and data["rsi14_pc"].values[0] >= 0
        ):
#            self.pts_sig_required_buy += 1
            if ( # Strong when RSI is 20% above MA and RSI > 50
                data["rsi_ma_pcnt"].values[0] > 20
                and data['rsi14'].values[0] > 50
            ):
                self.rsi_action = "strongbuy"
                self.buy_pts += 2
            else: 
                self.rsi_action = "buy"
                self.buy_pts += 1
        elif ( # Sell if RSI if decreasing
            data["rsi14_pc"].values[0] < 0
        ):
#            self.pts_sig_required_sell += 1
            # Strong when RSI is more than 5% below MA
            if data["rsi_ma_pcnt"].values[0] < -10:
                self.rsi_action = "strongsell"
                self.sell_pts += 2
            else:
                self.rsi_action = "sell"
                self.sell_pts += 1
        else:
            self.rsi_action = "wait"

        # ADX with percentage of difference between DI+ & DI- for strength
        if ( # DI+ above DI- and a difference of 20% and +DI increasing
            data["+di14"].values[0] > data["-di14"].values[0]
            and data["di_pcnt"].values[0] > 20
            and data["+di_pc"].values[0] > 0
        ):
            self.pts_sig_required_buy += 1
            if ( # Strong if ADX is > 30, DI difference greater than 50% or DI+ is above ADX
                data["adx14"].values[0 > 30]
                and (data["di_pcnt"].values[0] > 50
                    or  data["+di14"].values[0] > data["adx14"].values[0])
            ):
                self.adx_action = "strongbuy"
                self.buy_pts += 2
            else:
                self.adx_action = "buy"
                self.buy_pts += 1
        elif ( # Sell if +DI decreasing or DI+ is below DI-
            (data["+di_pc"].values[0] < 0
                or data["+di14"].values[0] < data["-di14"].values[0])
        ):
            if ( # Strong if DI difference is below -10% or DI- is above ADX
                (data["di_pcnt"].values[0] < -10
                    or data["-di14"].values[0] > data["adx14"].values[0])
                    # might change DI- below ADX, have to watch charts and values
            ):
                self.adx_action = "strongsell"
                self.sell_pts += 2
            else:
                self.adx_action = "sell"
                self.sell_pts += 1
        else:
            self.adx_action = "wait"

        # MACD signal variation using EMA Oscillator & SMA Signal, also using 8, 21, 5
        # in addition to typical > 0 and crossover indicators
        if ( # buy when MACD is climbing and above Signal by 25% or more
            data["macd_sig_pcnt"].values[0] > 25
            and data["macd_pc"].values[0] > 0
        ):
#            self.pts_sig_required_buy += 1
            if ( # Strong when MACD > 0 and difference > 35%
                data["macd"].values[0] > 0
                and data["macd_sig_pcnt"].values[0] > 35
            ):
                self.macd_action = "strongbuy"
                self.buy_pts += 2
            else:
                self.macd_action = "buy"
                self.buy_pts += 1
        elif ( # Sell when macd is decreasing
            data["macd_pc"].values[0] < 0
        ):
#            self.pts_sig_required_sell += 1
            if ( # Strong if diff between MACD and SIG is < 0
                data["macd_sig_pcnt"].values[0] < 0
            ):
                self.macd_action = "strongsell"
                self.sell_pts += 2
            else:
                self.macd_action = "sell"
                self.sell_pts += 1
        else:
            self.macd_action = "wait"

        # OBV and SMA5 - when OBV is above its SMA, buy and when below, sell
        if ( # Buy when OBV is 1% above SMA and OBV change percent > 2
            data["obv_sm_diff"].values[0] > 1
            and data['obv_pc'].values[0] >= 0
        ):
            self.pts_sig_required_buy += 1
            self.obv_action = "buy"
            self.buy_pts += 1
        elif ( # Sell when OBV below SMA or OBV is decreasing
            (data["obv_sm_diff"].values[0] < 0
                or data['obv_pc'].values[0] < 0)
        ):
            self.pts_sig_required_sell += 1
            self.obv_action = "sell"
            self.sell_pts += 1
        else:
            self.obv_action = "wait"

        # MACD Leader signal.....
        # for short trading in pycryptobot, we check that MacdLeader > Macdl_sig and upward trend
        if ( # MACDL above Signal by 40% and MACDL change > 20%
            data["macdl_sg_diff"].values[0] > 50
            and data["macdlead_pc"].values[0] > 20
            and data["macdlead"].values[0] > 0
        ):
            self.pts_sig_required_buy += 1
            if ( # Strong when MACDL changes 40% or more, MACD is 100% above Signal and MACDL is > 0
            data["macdlead_pc"].values[0] > 40
                and data["macdl_sg_diff"].values[0] > 100
            ):
                self.macdl_action = "strongbuy"
                self.buy_pts += 2
            else:
                self.macdl_action = "buy"
                self.buy_pts += 1
        elif ( # Sell when MACDL Starts decreasing
            data["macdlead_pc"].values[0] < 0
        ):
            self.pts_sig_required_sell += 1
            if ( # Strong when MACDL below Signal or MACDL < 0
                data["macdl_sg_diff"].values[0] < 0
            ):
                self.macdl_action = "strongsell"
                self.sell_pts += 2
            else:
                self.macdl_action = "sell"
                self.sell_pts += 1
        else:
            self.macdl_action = "wait"

        # EMA5/WMA5 crossover signal
        if ( # EMA above WMA
            data["ema5"].values[0] > data["ema5_wma5"].values[0]
            and data["ema5_pc"].values[0] > 0
        ):
            self.pts_sig_required_buy += 1
            if ( # Strong when EMA_pc > 8
                data["ema5_pc"].values[0] > 5
            ):
                self.emawma_action = "strongbuy"
                self.buy_pts += 2
            else:
                self.emawma_action = "buy"
                self.buy_pts += 1
        elif ( # Sell when EMA < WMA
            data["ema5_pc"].values[0] < 0
        ):
            self.pts_sig_required_sell += 1
            if data["ema5"].values[0] < data["ema5_wma5"].values[0]:
                self.emawma_action = "strongsell"
                self.sell_pts += 2
            else:
                self.emawma_action = "sell"
                self.sell_pts += 1
        else:
            self.emawma_action = "wait"

        if debug is True:
            indicatorvalues = (
                # Actions
                f"Macd Action: {self.macd_action} ADX Action: {self.adx_action} RSI Action: {self.rsi_action}"
                f" OBV Action: {self.obv_action} MacdL Action: {self.macdl_action}"
                "\n"
                # RSI
                f"RSI: {_truncate(data['rsi14'].values[0], 2)} RSIpc: {data['rsi14_pc'].values[0]}"
                f"  MA: {_truncate(data['rsima10'].values[0], 2)} MAPcnt: {data['rsi_ma_pcnt'].values[0]}%"
                "\n"
                # OBV
                f"OBV: {_truncate(data['obv'].values[0], 2)} SM: {_truncate(data['obvsm'].values[0], 2)}"
                f" Diff: {data['obv_sm_diff'].values[0]} OBVPC: {data['obv_pc'].values[0]}"
                # ADX
                f" ADX14: {_truncate(data['adx14'].values[0], 2)}"
                f" DI Pcnt: {_truncate(data['di_pcnt'].values[0], 2)}%, +DIpc: {data['+di_pc'].values[0]}"
                f" +DI14 {_truncate(data['+di14'].values[0], 2)} -DI14: {_truncate(data['-di14'].values[0], 2)}"
                "\n"
                # MACD
                f"Macd: {_truncate(data['macd'].values[0],6)}"
                f" Sgnl: {_truncate(data['signal'].values[0],6)} SigPcnt: {data['macd_sig_pcnt'].values[0]}%"
                f" PrvSigPcnt: {_df['macd_sig_pcnt'].iloc[-2]}%"
                f" Macdpc: {data['macd_pc'].values[0]}"
                "\n"
                # MACD_Leader
                f"BuyPts: {self.buy_pts} SellPts: {self.sell_pts} MacdLead: {_truncate(data['macdlead'].values[0],6)} MacdL: {_truncate(data['macdl'].values[0],6)}"
                f" MacdlSig: {_truncate(data['macdl_sig'].values[0],6)} MacdLeadpc: {data['macdlead_pc'].values[0]}% Diff: {data['macdl_sg_diff'].values[0]}%"
                "\n"
                # EMA/WMA
                f"EMAWMA Action: {self.emawma_action} EMA5pc: {data['ema5_pc'].values[0]}"
                f" EMA5: {_truncate(data['ema5'].values[0],2)} EMA5: {_truncate(data['ema5_wma5'].values[0],2)}"
            )
            Logger.info(indicatorvalues)
        else:
            indicatorvalues = ""

        return indicatorvalues

    def buySignal(self) -> bool:

        # non-Traditional buy signal criteria
        # *** currently requires pandas-ta module and optional talib 
        if (
            self.buy_pts >= self.pts_to_buy
            and self.pts_sig_required_buy >= self.sig_required_buy
        ):
            if (
                self.app.getTrailingBuyImmediatePcnt() is not None
                and self.buy_pts >= self.immed_buy_pts
            ):
                self.state.trailing_buy_immediate = True
            else:
                self.state.trailing_buy_immediate = False

            return True
        else:
            return False

    def sellSignal(self) -> bool:

        # non-Traditional sell signal criteria
        # *** currently requires pandas-ta module and optional talib 
        if (
            self.sell_pts >= self.pts_to_sell
            and self.pts_sig_required_sell >= self.sig_required_sell
        ):
            if (
                self.app.getTrailingSellImmediatePcnt() is not None
                and self.sell_pts >= self.immed_sell_pts
            ):
                self.state.trailing_sell_immediate = True
            else:
                self.state.trailing_sell_immediate = False

            return True
        else:
            return False