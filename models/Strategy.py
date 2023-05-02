from datetime import datetime
from pandas import DataFrame
from utils.PyCryptoBot import truncate as _truncate
from models.AppState import AppState
from models.helper.LogHelper import Logger
from os.path import exists as file_exists

try:
    # pyright: reportMissingImports=false
    from models.Strategy_myCS import Strategy_CS as myCS

    strategy_myCS = True
    myCS_error = None
except ModuleNotFoundError as err:
    strategy_myCS = False
    myCS_error = err
except ImportError as err:
    strategy_myCS = False
    myCS_error = err
if strategy_myCS is False:
    from models.Strategy_CS import Strategy_CS as CS


class Strategy:
    def __init__(
        self,
        app,
        state: AppState = AppState,
        df: DataFrame = DataFrame,
        iterations: int = 0,
    ) -> None:
        if not isinstance(df, DataFrame):
            raise TypeError("'df' not a Pandas dataframe")

        if len(df) == 0:
            raise ValueError("'df' is empty")

        self.app = app
        self.state = state
        self._df = df

        if app.enable_custom_strategy:
            if strategy_myCS is False and file_exists("models/Strategy_myCS.py"):
                raise ImportError(f"Custom Strategy Error: {myCS_error}")
            else:
                if strategy_myCS is True:
                    self.CS = myCS(self.app, self.state)
                else:
                    self.CS = CS(self.app, self.state)
                self.CS_ready = True
        else:
            self.CS_ready = False

        if self.app.is_sim:
            self._df_last = self.app.get_interval(df, iterations)
        else:
            self._df_last = self.app.get_interval(df)

    def is_buy_signal(
        self,
        state,
        price,
        now: datetime = datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
    ) -> bool:
        self.state = state
        # set to true for verbose debugging
        debug = False

        # buy signal exclusion (if disabled, do not buy within 3% of the dataframe close high)
        if (
            self.state.last_action == "SELL"
            and self.app.disablebuynearhigh is True
            and (
                price
                > (self._df["close"].max() * (1 - self.app.nobuynearhighpcnt / 100))
            )
        ):
            if not self.app.is_sim or (self.app.is_sim and not self.app.simresultonly):
                log_text = (
                    str(now)
                    + " | "
                    + self.app.market
                    + " | "
                    + self.app.print_granularity()
                    + " | Ignoring Buy Signal (price "
                    + str(price)
                    + " within "
                    + str(self.app.nobuynearhighpcnt)
                    + "% of high "
                    + str(self._df["close"].max())
                    + ")"
                )
                Logger.warning(log_text)

            return False

        # initial funds check
        if self.app.enableinsufficientfundslogging and self.app.insufficientfunds:
            Logger.warning(f"{str(now)} | Insufficient funds, ignoring buy signal.")
            return False

        # if Bull Only is set and no goldencross, return False
        if (
            self.app.disablebullonly is False
            and bool(self._df_last["goldencross"].values[0]) is False
        ):
            return False

        # Custom Strategy options
        if self.CS_ready:
            if self.CS.buySignal():
                return True
            else:
                # If Custom Strategy active, don't process standard signals, return False
                return False

        # if standard EMA and MACD are disabled, do not run below tests
        if self.app.disablebuyema and self.app.disablebuymacd:
            log_text = f"{str(now)} | {self.app.market} | {self.app.print_granularity()} | EMA, MACD indicators are disabled"
            Logger.warning(log_text)

            return False

        # required technical indicators for buy signal strategy
        required_indicators = ["ema12gtema26co", "macdgtsignal"]

        for indicator in required_indicators:
            if indicator not in self._df_last:
                raise AttributeError(f"'{indicator}' not in Pandas dataframe")

        # criteria for a buy signal 1
        if (
            (
                bool(self._df_last["ema12gtema26co"].values[0]) is True
                or self.app.disablebuyema
            )
            and (
                bool(self._df_last["macdgtsignal"].values[0]) is True
                or self.app.disablebuymacd
            )
            and (
                float(self._df_last["obv_pc"].values[0])
                > -5  # TODO: why is this hard coded?
                or self.app.disablebuyobv
            )
            and (
                bool(self._df_last["eri_buy"].values[0]) is True
                or self.app.disablebuyelderray
            )
            and self.state.last_action != "BUY"
        ):  # required for all strategies

            if debug:
                Logger.debug("*** Buy Signal ***")
                for indicator in required_indicators:
                    Logger.debug(f"{indicator}: {self._df_last[indicator].values[0]}")
                Logger.debug(f"last_action: {self.state.last_action}")

            return True

        # criteria for buy signal 2 (optionally add additional buy signals)
        elif (
            (
                bool(self._df_last["ema12gtema26co"].values[0]) is True
                or self.app.disablebuyema
            )
            and bool(self._df_last["macdgtsignalco"].values[0]) is True
            and (
                float(self._df_last["obv_pc"].values[0])
                > -5  # TODO: why is this hard coded?
                or self.app.disablebuyobv
            )
            and (
                bool(self._df_last["eri_buy"].values[0]) is True
                or self.app.disablebuyelderray
            )
            and self.state.last_action != "BUY"
        ):  # required for all strategies

            if debug:
                Logger.debug("*** Buy Signal ***")
                for indicator in required_indicators:
                    Logger.debug(f"{indicator}: {self._df_last[indicator].values[0]}")
                Logger.debug(f"last_action: {self.state.last_action}")

            return True

        return False

    def is_sell_signal(self) -> bool:
        # set to true for verbose debugging
        debug = False

        # additional sell signals - add additional functions and calls as necessary
        if self.CS_ready:
            if self.CS.sellSignal():
                return True
            else:
                # If Custom Strategy active, don't process standard signals, return False
                return False

        # if standard EMA and MACD are disabled, do not run below tests
        if self.app.disablebuyema and self.app.disablebuymacd:
            # if custom trade signals is enabled, don't alert, just return False
            if self.CS_ready is False:
                log_text = f"{str(datetime.now())} | {self.app.market} | {self.app.print_granularity()} | "
                log_text += " EMA, MACD indicators are needed for standard signals and they are disabled."
                Logger.warning(log_text)

            return False

        # required technical indicators or candle sticks for standard sell signal strategy
        required_indicators = ["ema12ltema26co", "macdltsignal"]

        for indicator in required_indicators:
            if indicator not in self._df_last:
                raise AttributeError(f"'{indicator}' not in Pandas dataframe")

        # criteria for a sell signal 1
        if bool(self._df_last["ema12ltema26co"].values[0]) is True and (
            bool(self._df_last["macdltsignal"].values[0]) is True
            or self.app.disablebuymacd
        ):
            if debug:
                Logger.debug("*** Sell Signal ***")
                for indicator in required_indicators:
                    Logger.debug(f"{indicator}: {self._df_last[indicator].values[0]}")
                Logger.debug(f"last_action: {self.state.last_action}")

            return True

        return False

    def is_sell_trigger(
        self,
        app,
        state,
        price: float = 0.0,
        price_exit: float = 0.0,
        margin: float = 0.0,
        change_pcnt_high: float = 0.0,
        obv_pc: float = 0.0,
        macdltsignal: bool = False,
    ) -> bool:
        self.state = state
        # set to true for verbose debugging
        debug = False

        # if ALL CUSTOM signals are still buy and strength is strong don't trigger a sell yet
        if (  # Custom Strategy loaded
            self.CS_ready
            and self.app.selltriggeroverride is True
            and self.CS.buy_pts >= self.CS.sell_override_pts
        ):
            return False

        # preventloss - attempt selling before margin drops below 0%
        if self.app.preventloss:
            if (
                self.state.prevent_loss is False
                and margin > self.app.preventlosstrigger
            ):
                self.state.prevent_loss = True
                Logger.warning(
                    f"{self.app.market} - reached prevent loss trigger of {self.app.preventlosstrigger}%.  Watch margin ({self.app.preventlossmargin}%) to prevent loss."
                )
            elif (
                self.state.prevent_loss is True and margin <= self.app.preventlossmargin
            ) or (  # trigger of 0 disables trigger check and only checks margin set point
                self.app.preventlosstrigger == 0
                and margin <= self.app.preventlossmargin
            ):
                Logger.warning(
                    f"{self.app.market} - time to sell before losing funds! Prevent Loss Activated!"
                )
                if not self.app.disabletelegram:
                    self.app.notifyTelegram(
                        f"{self.app.market} - time to sell before losing funds! Prevent Loss Activated!"
                    )
                return True

        # check sellatloss and nosell bounds before continuing
        if not self.app.sellatloss and margin <= 0:
            return False
        elif (
            (self.app.nosellminpcnt is not None) and (margin >= self.app.nosellminpcnt)
        ) and (
            (self.app.nosellmaxpcnt is not None) and (margin <= self.app.nosellmaxpcnt)
        ):
            return False

        if debug:
            Logger.debug(f"Trailing Stop Loss Enabled {self.app.trailing_stop_loss}")
            Logger.debug(
                f"Change Percentage {change_pcnt_high} < Stop Loss Percent {self.state.tsl_pcnt} = {change_pcnt_high < self.state.tsl_pcnt}"
            )
            Logger.debug(
                f"Margin {margin} > Stop Loss Trigger  {self.state.tsl_trigger} = {margin > self.state.tsl_trigger}"
            )

        if self.state.tsl_pcnt is not None:
            # dynamic trailing_stop_loss
            if self.app.dynamic_tsl:
                if (
                    self.app.tsl_trigger_multiplier is not None
                    and margin
                    > round(self.state.tsl_trigger * self.app.tsl_trigger_multiplier)
                    and self.state.tsl_max is False
                ):
                    # price increased, so check margin and reset trailingsellpcnt
                    self.state.tsl_triggered = False

                if self.state.tsl_triggered is False:
                    # check margin and set the trailingsellpcnt dynamically if enabled
                    if self.app.tsl_trigger_multiplier is not None and margin > round(
                        self.state.tsl_trigger * self.app.tsl_trigger_multiplier
                    ):
                        self.state.tsl_triggered = True
                        self.state.tsl_trigger = round(
                            self.state.tsl_trigger * self.app.tsl_trigger_multiplier
                        )
                        self.state.tsl_pcnt = float(
                            round(self.state.tsl_pcnt * self.app.tsl_multiplier, 1)
                        )
                        if (
                            self.state.tsl_pcnt <= self.app.tsl_max_pcnt
                        ):  # has tsl reached it's max setting
                            self.state.tsl_max = True
                    # tsl is triggered if margin is high enough
                    elif margin > self.state.tsl_trigger:
                        self.state.tsl_triggered = True

            # default, fixed trailingstoploss and trigger
            else:
                # loss failsafe sell at trailing_stop_loss
                if margin > self.state.tsl_trigger:
                    self.state.tsl_triggered = 1

            if debug:
                debugtext = f"TSL Triggered: {self.state.tsl_triggered} TSL Pcnt: {self.state.tsl_pcnt}% TSL Trigger: {self.state.tsl_trigger}%"
                debugtext += (
                    f" TSL Next Trigger: {round(self.state.tsl_trigger * self.app.tsl_trigger_multiplier)}%\n"
                    if self.app.dynamic_tsl
                    else "\n"
                )
                debugtext += f"Change Percentage {change_pcnt_high} < Stop Loss Percent {self.app.trailing_stop_loss} = {change_pcnt_high < self.app.trailing_stop_loss}"
                debugtext += f"Margin {margin} > Stop Loss Trigger  {self.app.trailing_stop_loss_trigger} = {margin > self.app.trailing_stop_loss_trigger}"
                Logger.debug(debugtext)

                # Telgram debug output
                if not self.app.disabletelegram:
                    self.app.notifyTelegram(
                        f"{self.app.market} ({self.app.print_granularity()})\n{debugtext}"
                    )

            if (
                self.state.tsl_triggered is True
                and change_pcnt_high < self.state.tsl_pcnt
            ):
                log_text = f"! Trailing Stop Loss Triggered (Margin: {_truncate(margin,2)}% Stoploss: {str(self.state.tsl_pcnt)}%)"
                if not self.app.is_sim or (
                    self.app.is_sim and not self.app.simresultonly
                ):
                    Logger.warning(log_text)

                if not self.app.disabletelegram:
                    self.app.notifyTelegram(
                        f"{self.app.market} ({self.app.print_granularity()}) {log_text}"
                    )

                return True

        if debug:
            Logger.debug("-- loss failsafe sell at sell_lower_pcnt --")
            Logger.debug(
                f"self.app.disablefailsafelowerpcnt is False (actual: {self.app.disablefailsafelowerpcnt})"
            )
            Logger.debug(
                f"and self.app.sellatloss is True (actual: {self.app.sellatloss})"
            )
            Logger.debug(
                f"and self.app.sell_lower_pcnt is not None (actual: {self.app.sell_lower_pcnt})"
            )
            Logger.debug(
                f"and margin ({margin}) < self.app.sell_lower_pcnt ({self.app.sell_lower_pcnt})"
            )
            Logger.debug(
                f"(self.app.sellatloss is True (actual: {self.app.sellatloss}) or margin ({margin}) > 0)"
            )
            Logger.debug("\n")

        # loss failsafe sell at sell_lower_pcnt
        if (
            self.app.disablefailsafelowerpcnt is False
            and self.app.sellatloss
            and self.app.sell_lower_pcnt is not None
            and margin < self.app.sell_lower_pcnt
        ):
            log_text = (
                "! Loss Failsafe Triggered (< " + str(self.app.sell_lower_pcnt) + "%)"
            )
            Logger.warning(log_text)
            if not self.app.disabletelegram:
                self.app.notifyTelegram(
                    f"{self.app.market} ({self.app.print_granularity()}) {log_text}"
                )
            return True

        if debug:
            Logger.debug("\n*** isSellTrigger ***\n")
            Logger.debug("-- ignoring sell signal --")
            Logger.debug(
                f"self.app.nosellminpcnt is None (nosellminpcnt: {self.app.nosellminpcnt})"
            )
            Logger.debug(f"margin >= self.app.nosellminpcnt (margin: {margin})")
            Logger.debug(
                f"margin <= self.app.nosellmaxpcnt (nosellmaxpcnt: {self.app.nosellmaxpcnt})"
            )
            Logger.debug("\n")

        if debug:
            Logger.debug("\n*** isSellTrigger ***\n")
            Logger.debug("-- loss failsafe sell at fibonacci band --")
            Logger.debug(
                f"self.app.disablefailsafefibonaccilow is False (actual: {self.app.disablefailsafefibonaccilow})"
            )
            Logger.debug(
                f"self.app.sellatloss is True (actual: {self.app.sellatloss})"
            )
            Logger.debug(
                f"self.app.sell_lower_pcnt is None (actual: {self.app.sell_lower_pcnt})"
            )
            Logger.debug(f"self.state.fib_low {self.state.fib_low} > 0")
            Logger.debug(f"self.state.fib_low {self.state.fib_low} >= {float(price)}")
            Logger.debug(
                f"(self.app.sellatloss is True (actual: {self.app.sellatloss}) or margin ({margin}) > 0)"
            )
            Logger.debug("\n")

        # loss failsafe sell at fibonacci band
        if (
            self.app.disablefailsafefibonaccilow is False
            and self.app.sellatloss
            and self.app.sell_lower_pcnt is None
            and self.state.fib_low > 0
            and self.state.fib_low >= float(price)
        ):
            log_text = (
                f"! Loss Failsafe Triggered (Fibonacci Band: {str(self.state.fib_low)})"
            )
            Logger.warning(log_text)
            self.app.notifyTelegram(
                f"{self.app.market} ({self.app.print_granularity()}) {log_text}"
            )
            return True

        if debug:
            Logger.debug("-- loss failsafe sell at trailing_stop_loss --")
            Logger.debug(
                f"self.app.trailing_stop_loss is not None (actual: {self.app.trailing_stop_loss})"
            )
            Logger.debug(
                f"change_pcnt_high ({change_pcnt_high}) < self.app.trailing_stop_loss ({self.app.trailing_stop_loss})"
            )
            Logger.debug(
                f"margin ({margin}) > self.app.trailing_stop_loss_trigger ({self.app.trailing_stop_loss_trigger})"
            )
            Logger.debug(
                f"(self.app.sellatloss is True (actual: {self.app.sellatloss}) or margin ({margin}) > 0)"
            )
            Logger.debug("\n")

        if debug:
            Logger.debug("-- profit bank at sell_upper_pcnt --")
            Logger.debug(
                f"self.app.disableprofitbankupperpcnt is False (actual: {self.app.disableprofitbankupperpcnt})"
            )
            Logger.debug(
                f"and self.app.sell_upper_pcnt is not None (actual: {self.app.sell_upper_pcnt})"
            )
            Logger.debug(
                f"and margin ({margin}) > self.app.sell_upper_pcnt ({self.app.sell_upper_pcnt})"
            )
            Logger.debug(
                f"(self.app.sellatloss is True (actual: {self.app.sellatloss}) or margin ({margin}) > 0)"
            )
            Logger.debug("\n")

        # profit bank at sell_upper_pcnt
        if (
            self.app.disableprofitbankupperpcnt is False
            and self.app.sell_upper_pcnt is not None
            and margin > self.app.sell_upper_pcnt
        ):
            log_text = f"! Profit Bank Triggered (> {str(self.app.sell_upper_pcnt)}%)"
            if not self.app.is_sim or (self.app.is_sim and not self.app.simresultonly):
                Logger.warning(log_text)
            if not self.app.disabletelegram:
                self.app.notifyTelegram(
                    f"{self.app.market} ({self.app.print_granularity()}) {log_text}"
                )
            return True

        if debug:
            Logger.debug("-- profit bank when strong reversal detected --")
            Logger.debug(
                f"self.app.sellatresistance is True (actual {self.app.sellatresistance})"
            )
            Logger.debug(f"and price ({price}) > 0")
            Logger.debug(f"and price ({price}) >= price_exit ({price_exit})")
            Logger.debug(
                f"(self.app.sellatloss is True (actual: {self.app.sellatloss}) or margin ({margin}) > 0)"
            )
            Logger.debug("\n")

        # profit bank when strong reversal detected
        if (
            self.app.sellatresistance is True
            and margin >= 2
            and price > 0
            and price >= price_exit
            and (self.app.sellatloss or margin > 0)
        ):
            log_text = "! Profit Bank Triggered (Selling At Resistance)"
            if not self.app.is_sim or (self.app.is_sim and not self.app.simresultonly):
                Logger.warning(log_text)
            if not (not self.app.sellatloss and margin <= 0):
                if not self.app.disabletelegram:
                    self.app.notifyTelegram(
                        f"{self.app.market} ({self.app.print_granularity()}) {log_text}"
                    )
            return True

        return False

    def is_wait_trigger(self, margin: float = 0.0, goldencross: bool = False):
        # set to true for verbose debugging
        debug = False

        # if prevent_loss is enabled and activated, don't WAIT
        if (
            self.state.prevent_loss is True and margin <= self.app.preventlossmargin
        ) or (  # trigger of 0 disables trigger check and only checks margin set point
            self.app.preventlosstrigger == 0 and margin <= self.app.preventlossmargin
        ):
            return False

        if debug and self.state.action != "WAIT":
            Logger.debug("\n*** isWaitTrigger ***\n")

        if debug and self.state.action == "BUY":
            Logger.debug("-- if bear market and bull only return true to abort buy --")
            Logger.debug(f"self.state.action == 'BUY' (actual: {self.state.action})")
            Logger.debug(
                f"and self.app.disablebullonly is True (actual: {self.app.disablebullonly})"
            )
            Logger.debug(f"and goldencross is False (actual: {goldencross})")
            Logger.debug("\n")

        # if bear market and bull only return true to abort buy
        if (
            self.state.action == "BUY"
            and not self.app.disablebullonly
            and not goldencross
        ):
            log_text = "! Ignore Buy Signal (Bear Buy In Bull Only)"
            Logger.warning(log_text)
            return True

        if debug and self.state.action == "SELL":
            Logger.debug("-- configuration specifies to not sell at a loss --")
            Logger.debug(f"self.state.action == 'SELL' (actual: {self.state.action})")
            Logger.debug(
                f"and self.app.sellatloss is False (actual: {self.app.sellatloss})"
            )
            Logger.debug(f"and margin ({margin}) <= 0")
            Logger.debug("\n")

        # configuration specifies to not sell at a loss
        if self.state.action == "SELL" and not self.app.sellatloss and margin <= 0:
            if not self.app.is_sim or (self.app.is_sim and not self.app.simresultonly):
                log_text = "! Ignore Sell Signal (No Sell At Loss)"
                Logger.warning(log_text)
            return True

        if debug and self.state.action == "SELL":
            Logger.debug(
                "-- configuration specifies not to sell within min and max margin percent bounds --"
            )
            Logger.debug(f"self.state.action == 'SELL' (actual: {self.state.action})")
            Logger.debug(
                f"(self.app.nosellminpcnt is not None (actual: {self.app.nosellminpcnt})) and (margin ({margin}) >= self.app.nosellminpcnt ({self.app.nosellminpcnt}))"
            )
            Logger.debug(
                f"(self.app.nosellmaxpcnt is not None (actual: {self.app.nosellmaxpcnt})) and (margin ({margin}) <= self.app.nosellmaxpcnt ({self.app.nosellmaxpcnt}))"
            )
            Logger.debug("\n")

        # configuration specifies not to sell within min and max margin percent bounds
        if (
            self.state.action == "SELL"
            and (
                (self.app.nosellminpcnt is not None)
                and (margin >= self.app.nosellminpcnt)
            )
            and (
                (self.app.nosellmaxpcnt is not None)
                and (margin <= self.app.nosellmaxpcnt)
            )
        ):
            if not self.app.is_sim or (self.app.is_sim and not self.app.simresultonly):
                Logger.warning("! Ignore Sell Signal (Within No-Sell Bounds)")
            return True

        return False

    def check_trailing_buy(self, state, price):
        self.state = state
        # If buy signal, save the price and check if it decreases before buying.
        immediate_action = False
        trailingbuypcnt = (
            self.app.trailingbuypcnt
        )  # get pcnt from config, if not, use 0%
        if self.state.trailing_buy is True and self.state.waiting_buy_price > 0:
            pricechange = float(
                _truncate(
                    (self.state.waiting_buy_price - price)
                    / self.state.waiting_buy_price
                    * -100,
                    2,
                )
            )
        else:
            self.state.waiting_buy_price = price
            pricechange = 0
            self.state.trailing_buy = True

        waitpcnttext = f"** {self.app.market} ({self.app.print_granularity()}) - "
        if price < self.state.waiting_buy_price:
            self.state.waiting_buy_price = price
            self.state.action = "WAIT"
            trailing_action_logtext = f" - Wait Chg: Dec {str(pricechange)}%"
            waitpcnttext += "Price decreased - resetting wait price. "
        elif (
            self.app.trailingbuyimmediatepcnt is not None
            and (
                self.state.trailing_buy_immediate is True
                or self.app.trailingimmediatebuy is True
            )
            and pricechange > self.app.trailingbuyimmediatepcnt
        ):  # If price increases by more than trailingbuyimmediatepcnt, do an immediate buy
            self.state.action = "BUY"
            immediate_action = True
            trailing_action_logtext = f" - Immediate Buy - Chg: {str(pricechange)}%/{self.app.trailingbuyimmediatepcnt}%"
            waitpcnttext += f"Ready for immediate buy. {self.state.waiting_buy_price} change of {str(pricechange)}% is above setting of {self.app.trailingbuyimmediatepcnt}%"
            self.app.notifyTelegram(waitpcnttext)
        # added 10% fluctuation to prevent holding another full candle for 0.025%
        elif pricechange < (trailingbuypcnt * 0.9):
            self.state.action = "WAIT"
            trailing_action_logtext = f" - Wait Chg: {str(pricechange)}%"
            trailing_action_logtext += (
                f"/{trailingbuypcnt}%" if trailingbuypcnt > 0 else ""
            )
            waitpcnttext += f"Waiting to buy until price of {self.state.waiting_buy_price} increases {trailingbuypcnt}% (+/- 10%) - change {str(pricechange)}%"
        else:
            self.state.action = "BUY"
            trailing_action_logtext = (
                f" - Buy Chg: {str(pricechange)}%/{trailingbuypcnt}%"
            )
            waitpcnttext += f"Ready to buy at close. Price of {self.state.waiting_buy_price}, change of {str(pricechange)}%, is greater than setting of {trailingbuypcnt}%  (+/- 10%)"

        if self.app.is_verbose and (
            not self.app.is_sim or (self.app.is_sim and not self.app.simresultonly)
        ):
            Logger.info(waitpcnttext)

        return (
            self.state.action,
            self.state.trailing_buy,
            trailing_action_logtext,
            immediate_action,
        )

    def check_trailing_sell(self, state, price):
        debug = False

        # return early if trailing sell is not enabled
        if state.trailing_sell is False:
            return (
                state.action,
                False,
                "",
                False,
            )

        self.state = state
        # If sell signal, save the price and check if it increases before selling.
        immediate_action = False
        if (
            self.state.trailing_sell is True
            and self.state.waiting_sell_price is not None
        ):
            pricechange = float(
                _truncate(
                    (self.state.waiting_sell_price - price)
                    / self.state.waiting_sell_price
                    * -100,
                    2,
                )
            )
        else:
            self.state.waiting_sell_price = price
            pricechange = 0
            self.state.trailing_sell = True

        waitpcnttext = f"** {self.app.market} ({self.app.print_granularity()}) - "
        if price >= self.state.waiting_sell_price:
            self.state.waiting_sell_price = price
            self.state.action = "WAIT"
            trailing_action_logtext = f" - Wait Chg: Inc {str(pricechange)}%"
            waitpcnttext += "Price increased - resetting wait price."
        # bailout setting.  If price drops x%, sell immediately.
        elif (
            self.app.trailingsellbailoutpcnt is not None
            and pricechange < self.app.trailingsellbailoutpcnt
        ):
            self.state.action = "SELL"
            immediate_action = True
            trailing_action_logtext = f" - Bailout Immediately - Chg: {str(pricechange)}%/{self.app.trailingsellbailoutpcnt}%"
            waitpcnttext += f"Bailout Immediately. Price {self.state.waiting_sell_price}, change of {str(pricechange)}%, is lower than setting of {self.app.trailingsellbailoutpcnt}%"
            self.app.notifyTelegram(waitpcnttext)
        # When all indicators signal strong sell and price decreases more than "self.app.trailingsellimmediatepcnt", immediate sell
        elif (  # This resets after a sell occurs
            self.app.trailingsellimmediatepcnt is not None
            and (
                self.state.trailing_sell_immediate is True
                or self.app.trailingimmediatesell is True
            )
            and pricechange < self.app.trailingsellimmediatepcnt
        ):
            self.state.action = "SELL"
            immediate_action = True
            trailing_action_logtext = f" - Immediate Sell - Chg: {str(pricechange)}%/{self.app.trailingsellimmediatepcnt}%"
            waitpcnttext += f"Sell Immediately. Price {self.state.waiting_sell_price}, change of {str(pricechange)}%, is lower than setting of {self.app.trailingsellimmediatepcnt}%"
            self.app.notifyTelegram(waitpcnttext)
        # added 10% fluctuation to prevent holding another full candle for 0.025%
        elif pricechange > (self.app.trailingsellpcnt * 0.9):
            self.state.action = "WAIT"
            if self.app.trailingsellpcnt == 0:
                trailing_action_logtext = f" - Wait Chg: {str(pricechange)}%"
                waitpcnttext += f"Waiting to sell until {self.state.waiting_sell_price} stops increasing - change {str(pricechange)}%"
            else:
                trailing_action_logtext = (
                    f" - Wait Chg: {str(pricechange)}%/{self.app.trailingsellpcnt}%"
                )
                waitpcnttext += f"Waiting to sell until price of {self.state.waiting_sell_price} decreases {self.app.trailingsellpcnt}% (+/- 10%) - change {str(pricechange)}%"
        else:
            self.state.action = "SELL"
            trailing_action_logtext = (
                f" - Sell Chg: {str(pricechange)}%/{self.app.trailingsellpcnt}%"
            )
            waitpcnttext += f"Sell at Close. Price of {self.state.waiting_sell_price}, change of {str(pricechange)}%, is lower than setting of {str(self.app.trailingsellpcnt)}% (+/- 10%)"

        if self.app.is_verbose and (
            not self.app.is_sim or (self.app.is_sim and not self.app.simresultonly)
        ):
            Logger.info(waitpcnttext)

        if debug:
            Logger.debug(waitpcnttext)
            Logger.debug(
                f"Trailing Sell Triggered: {self.state.trailing_sell}  Wait Price: {self.state.waiting_sell_price} Current Price: {price} Price Chg: {_truncate(pricechange,2)} Immed Sell Pcnt: -{str(self.app.trailingsellimmediatepcnt)}%"
            )

        return (
            self.state.action,
            self.state.trailing_sell,
            trailing_action_logtext,
            immediate_action,
        )

    def get_action(self, state, price, current_sim_date, websocket):
        self.state = state
        # if Custom Strategy requirements are met, run tradeSignals function and report any errors.
        if self.CS_ready is True:
            # use try/except since this is a customizable file
            try:
                # indicatorvalues displays indicators in log and telegram if debug is True in CS.tradeSignals
                indicatorvalues = self.CS.tradeSignals(
                    self._df_last, self._df, current_sim_date, websocket
                )
            except Exception as err:
                self.CS_ready = False
                Logger.warning(f"Custom Strategy Error: {err}")
        else:  # strategy not enabled or an error occurred.
            indicatorvalues = ""

        if self.state.last_action != "BUY" and self.is_buy_signal(
            self.state, price, current_sim_date
        ):
            return "BUY", indicatorvalues
        elif self.state.last_action not in ["", "SELL"] and self.is_sell_signal():
            return "SELL", indicatorvalues
        else:
            return "WAIT", indicatorvalues
