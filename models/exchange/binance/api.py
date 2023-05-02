"""Remotely control your Binance account via their API : https://binance-docs.github.io/apidocs/spot/en"""

import re
import json
import hmac
import hashlib
import time
import requests
import base64
import sys
import math
import pandas as pd
import numpy as np
from numpy import floor
from datetime import datetime, timedelta
from requests.auth import AuthBase
from requests import Request, Session
from models.helper.LogHelper import Logger
from urllib.parse import urlencode

DEFAULT_MAKER_FEE_RATE = 0.0015  # added 0.0005 to allow for price movements
DEFAULT_TAKER_FEE_RATE = 0.0015  # added 0.0005 to allow for price movements
DEFAULT_TRADE_FEE_RATE = 0.0015  # added 0.0005 to allow for price movements
DEFAULT_GRANULARITY = "1h"
SUPPORTED_GRANULARITY = ["1m", "5m", "15m", "1h", "6h", "1d"]
MULTIPLIER_EQUIVALENTS = [1, 5, 15, 60, 360, 1440]
FREQUENCY_EQUIVALENTS = ["T", "5T", "15T", "H", "6H", "D"]
DEFAULT_MARKET = "BTCGBP"


class AuthAPIBase:
    def _isMarketValid(self, market: str) -> bool:
        p = re.compile(r"^[A-Z0-9]{5,12}$")
        if p.match(market):
            return True
        return False

    def convert_time(self, epoch: int = 0):
        if math.isnan(epoch) is False:
            epoch_str = str(epoch)[0:10]
            return datetime.fromtimestamp(int(epoch_str))


class AuthAPI(AuthAPIBase):
    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        api_url: str = "https://api.binance.com",
        order_history: list = [],
        recv_window: int = 5000,
    ) -> None:
        """Binance API object model

        Parameters
        ----------
        api_key : str
            Your Binance account portfolio API key
        api_secret : str
            Your Binance account portfolio API secret
        api_url
            Binance API URL
        """

        # options
        self.debug = False
        self.die_on_api_error = False

        valid_urls = [
            "https://api.binance.com",
            "https://api.binance.us",
            "https://testnet.binance.vision",
        ]

        # validate Binance API
        if api_url not in valid_urls:
            raise ValueError("Binance API URL is invalid")

        # validates the api key is syntactically correct
        p = re.compile(r"^[A-z0-9]{64,64}$")
        if not p.match(api_key):
            self.handle_init_error("Binance API key is invalid")

        # validates the api secret is syntactically correct
        p = re.compile(r"^[A-z0-9]{64,64}$")
        if not p.match(api_secret):
            self.handle_init_error("Binance API secret is invalid")

        self._api_key = api_key
        self._api_secret = api_secret
        self._api_url = api_url

        # order history
        self.order_history = order_history

        # api recvWindow
        self.recv_window = recv_window

    def handle_init_error(self, err: str) -> None:
        if self.debug:
            raise TypeError(err)
        else:
            raise SystemExit(err)

    def _dispatch_request(self, method: str):
        session = Session()
        session.headers.update(
            {
                "Content-Type": "application/json; charset=utf-8",
                "X-MBX-APIKEY": self._api_key,
            }
        )
        return {
            "GET": session.get,
            "DELETE": session.delete,
            "PUT": session.put,
            "POST": session.post,
        }.get(method, "GET")

    def createHash(self, uri: str = ""):
        return hmac.new(
            self._api_secret.encode("utf-8"), uri.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def getTimestamp(self):
        return int(time.time() * 1000)

    def getAccounts(self) -> pd.DataFrame:
        """Retrieves your list of accounts"""

        # GET /api/v3/account
        resp = self.authAPI("GET", "/api/v3/account")

        if "balances" in resp:
            balances = resp["balances"]

            if isinstance(balances, list):
                df = pd.DataFrame.from_dict(balances)
            else:
                df = pd.DataFrame(balances, index=[0])
        else:
            return pd.DataFrame()

        # if df is empty, then return
        if len(df) == 0:
            return pd.DataFrame()

        # exclude accounts that are locked
        df = df[df.locked != 0.0]
        df["locked"] = df["locked"].astype(bool)

        # reset the dataframe index to start from 0
        df = df.reset_index()

        df["id"] = df["index"]
        df["hold"] = 0.0
        df["profile_id"] = None
        df["available"] = df["free"]

        df["id"] = df["id"].astype(object)
        df["hold"] = df["hold"].astype(object)

        # exclude accounts with a nil balance
        df = df[df.available != "0.00000000"]
        df = df[df.available != "0.00"]

        # if df is empty after filtering, then return
        if len(df) == 0:
            return pd.DataFrame()

        # rename columns
        df.columns = [
            "index",
            "currency",
            "balance",
            "trading_enabled",
            "id",
            "hold",
            "profile_id",
            "available",
        ]

        return df[
            [
                "index",
                "id",
                "currency",
                "balance",
                "hold",
                "available",
                "profile_id",
                "trading_enabled",
            ]
        ]

    def getAccount(self) -> pd.DataFrame:
        """Retrieves all accounts for Binance as there is no specific account id"""

        return self.getAccounts()

    def getFees(self, market: str = "") -> pd.DataFrame:
        """Retrieves a account fees"""

        # GET /api/v3/account
        resp = self.authAPI("GET", "/api/v3/account", {"recvWindow": self.recv_window})

        if "makerCommission" in resp and "takerCommission" in resp:
            maker_fee_rate = resp["makerCommission"] / 10000
            taker_fee_rate = resp["takerCommission"] / 10000
        else:
            maker_fee_rate = 0.001
            taker_fee_rate = 0.001

        return pd.DataFrame(
            [
                {
                    "maker_fee_rate": maker_fee_rate,
                    "taker_fee_rate": taker_fee_rate,
                    "usd_volume": 0,
                    "market": "",
                }
            ]
        )

    def getMakerFee(self, market: str = "") -> float:
        """Retrieves the maker fee"""

        if len(market):
            fees = self.getFees(market)
        else:
            fees = self.getFees()

        if len(fees) == 0 or "maker_fee_rate" not in fees:
            Logger.error(
                f"error: 'maker_fee_rate' not in fees (using {DEFAULT_MAKER_FEE_RATE} as a fallback)"
            )
            return DEFAULT_MAKER_FEE_RATE

        return float(fees["maker_fee_rate"].to_string(index=False).strip())

    def getTakerFee(self, market: str = "") -> float:
        """Retrieves the taker fee"""

        if len(market) != None:
            fees = self.getFees(market)
        else:
            fees = self.getFees()

        if len(fees) == 0 or "taker_fee_rate" not in fees:
            Logger.error(
                f"error: 'taker_fee_rate' not in fees (using {DEFAULT_TAKER_FEE_RATE} as a fallback)"
            )
            return DEFAULT_TAKER_FEE_RATE

        return float(fees["taker_fee_rate"].to_string(index=False).strip())

    def getUSDVolume(self) -> float:
        """Retrieves the USD volume"""

        fees = self.getFees()
        return float(fees["usd_volume"].to_string(index=False).strip())

    def getMarkets(self) -> list:
        """Retrieves a list of markets on the exchange"""

        # GET /api/v3/allOrders
        resp = self.authAPI("GET", "/api/v3/exchangeInfo")

        if "symbols" in resp:
            if isinstance(resp["symbols"], list):
                df = pd.DataFrame.from_dict(resp["symbols"])
            else:
                df = pd.DataFrame(resp["symbols"], index=[0])
        else:
            df = pd.DataFrame()

        return df[df["isSpotTradingAllowed"] == True][["symbol"]].squeeze().tolist()

    def getOrders(
        self,
        market: str = "",
        action: str = "",
        status: str = "done",
        order_history: list = [],
    ) -> pd.DataFrame:
        """Retrieves your list of orders with optional filtering"""

        # if market provided
        markets = None
        if market != "":
            # validates the market is syntactically correct
            if not self._isMarketValid(market):
                raise ValueError("Binance market is invalid.")
        else:
            if len(order_history) > 0 or status != "all":
                full_scan = False
                self.order_history = order_history
                if len(self.order_history) > 0:
                    if self._isMarketValid(market) and market not in self.order_history:
                        self.order_history.append(market)
                    markets = self.order_history
            else:
                full_scan = True
                markets = self.getMarkets()

        # if action provided
        if action != "":
            # validates action is either a buy or sell
            if not action in ["buy", "sell"]:
                raise ValueError("Invalid order action.")

        # validates status is either open, canceled, pending, done, active, or all
        if not status in ["open", "canceled", "pending", "done", "active", "all"]:
            raise ValueError("Invalid order status.")

        if markets is not None:
            df = pd.DataFrame()
            for market in markets:
                if full_scan is True:
                    print(f"scanning {market} order history.")

                # GET /api/v3/allOrders
                resp = self.authAPI(
                    "GET",
                    "/api/v3/allOrders",
                    {"symbol": market, "recvWindow": self.recv_window},
                )

                if full_scan is True:
                    time.sleep(0.25)

                if isinstance(resp, list):
                    df_tmp = pd.DataFrame.from_dict(resp)
                else:
                    df_tmp = pd.DataFrame(resp, index=[0])

                if full_scan is True and len(df_tmp) > 0:
                    self.order_history.append(market)

                if len(df_tmp) > 0:
                    df = pd.concat([df, df_tmp])

            if full_scan is True:
                print("add to order history to prevent full scan:", self.order_history)
        else:
            # GET /api/v3/allOrders
            resp = self.authAPI(
                "GET",
                "/api/v3/allOrders",
                {"symbol": market, "recvWindow": self.recv_window},
            )

            if isinstance(resp, list):
                df = pd.DataFrame.from_dict(resp)
            else:
                df = pd.DataFrame(resp, index=[0])

        if len(df) == 0 or "time" not in df:
            return pd.DataFrame()

        # feature engineering

        df.time = df["time"].map(self.convert_time)
        df["time"] = pd.to_datetime(df["time"]).dt.tz_localize("UTC")

        df["size"] = np.where(
            df["side"] == "BUY",
            df["cummulativeQuoteQty"],
            np.where(df["side"] == "SELL", df["executedQty"], 222),
        )
        df["fees"] = df["size"].astype(float) * 0.001
        df["fees"] = df["fees"].astype(object)

        df["side"] = df["side"].str.lower()

        df.rename(
            columns={
                "time": "created_at",
                "symbol": "market",
                "side": "action",
                "executedQty": "filled",
            },
            errors="raise",
            inplace=True,
        )

        def convert_status(status: str = ""):
            if status == "FILLED":
                return "done"
            elif status == "NEW":
                return "open"
            elif status == "PARTIALLY_FILLED":
                return "pending"
            else:
                return status

        df.status = df.status.map(convert_status)
        df["status"] = df["status"].str.lower()

        def calculate_price(row):
            print (row)
            if row.type == 'LIMIT' and float(row.price) > 0:
                return row.price
            elif row.action == 'buy':
                return float(row.cummulativeQuoteQty) / float(row.filled)
            elif row.action == 'sell':
                return float(row.cummulativeQuoteQty) / float(row.size)
            else:
                return row.price

        df["price"] = df.copy().apply(calculate_price, axis=1)

        # select columns
        df = df[
            [
                "created_at",
                "market",
                "action",
                "type",
                "size",
                "filled",
                "fees",
                "price",
                "status",
            ]
        ]

        # filtering
        if action != "":
            df = df[df["action"] == action]
        if status != "all":
            df = df[df["status"] == status]

        return df

    def getTime(self) -> datetime:
        """Retrieves the exchange time"""

        try:
            # GET /api/v3/time
            resp = self.authAPI("GET", "/api/v3/time")
            return self.convert_time(int(resp["serverTime"]))
        except:
            return None

    def getMarketInfoFilters(self, market: str) -> pd.DataFrame:
        """Retrieves markets exchange info"""

        # GET /api/v3/allOrders
        resp = self.authAPI("GET", "/api/v3/exchangeInfo", {"symbol": market})
        df = pd.DataFrame()

        if "symbols" in resp:
            if isinstance(resp["symbols"], list):
                if "filters" in resp["symbols"][0]:
                    df = pd.DataFrame.from_dict(resp["symbols"][0]["filters"])
            else:
                if "filers" in resp["symbols"][0]:
                    df = pd.DataFrame(resp["symbols"][0]["filters"], index=[0])

        return df

    def getTradeFee(self, market: str) -> float:
        """Retrieves the trade fees"""

        # GET /sapi/v1/asset/tradeFee
        resp = self.authAPI(
            "GET",
            "/sapi/v1/asset/tradeFee",
            {"symbol": market, "recvWindow": self.recv_window},
        )

        if len(resp) == 1 and "takerCommission" in resp[0]:
            return float(resp[0]["takerCommission"])
        else:
            return DEFAULT_TRADE_FEE_RATE

    def getTicker(self, market: str = DEFAULT_MARKET) -> tuple:
        """Retrieves the market ticker"""

        # validates the market is syntactically correct
        if not self._isMarketValid(market):
            raise TypeError("Binance market required.")

        # GET /api/v3/ticker/price
        resp = self.authAPI("GET", "/api/v3/ticker/price", {"symbol": market})

        now = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

        if "price" in resp:
            return (str(self.getTime()), float(resp["price"]))
        else:
            return (now, 0.0)

    def marketBuy(
        self, market: str = "", quote_quantity: float = 0, test: bool = False
    ) -> list:
        """Executes a market buy providing a funding amount"""

        # validates the market is syntactically correct
        if not self._isMarketValid(market):
            raise ValueError("Binance market is invalid.")

        # validates quote_quantity is either an integer or float
        if not isinstance(quote_quantity, int) and not isinstance(
            quote_quantity, float
        ):
            raise TypeError("The funding amount is not numeric.")

        try:
            current_price = self.getTicker(market)[1]

            base_quantity = np.divide(quote_quantity, current_price)

            df_filters = self.getMarketInfoFilters(market)
            step_size = float(
                df_filters.loc[df_filters["filterType"] == "LOT_SIZE"]["stepSize"]
            )
            precision = int(round(-math.log(step_size, 10), 0))

            # remove fees
            base_quantity = base_quantity - (base_quantity * self.getTradeFee(market))

            # execute market buy
            stepper = 10.0 ** precision
            truncated = math.trunc(stepper * base_quantity) / stepper

            order = {
                "symbol": market,
                "side": "BUY",
                "type": "MARKET",
                "quantity": truncated,
                "recvWindow": self.recv_window,
            }

            Logger.debug(order)

            # POST /api/v3/order/test
            if test is True:
                resp = self.authAPI("POST", "/api/v3/order/test", order)
            else:
                resp = self.authAPI("POST", "/api/v3/order", order)

            return resp
        except Exception as err:
            ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            Logger.error(ts + " Binance " + " marketBuy " + str(err))
            return []

    def marketSell(
        self, market: str = "", base_quantity: float = 0, test: bool = False
    ) -> list:
        """Executes a market sell providing a crypto amount"""

        # validates the market is syntactically correct
        if not self._isMarketValid(market):
            raise ValueError("Binance market is invalid.")

        if not isinstance(base_quantity, int) and not isinstance(base_quantity, float):
            raise TypeError("The crypto amount is not numeric.")

        try:
            df_filters = self.getMarketInfoFilters(market)
            step_size = float(
                df_filters.loc[df_filters["filterType"] == "LOT_SIZE"]["stepSize"]
            )
            precision = int(round(-math.log(step_size, 10), 0))

            # remove fees
            base_quantity = base_quantity - (base_quantity * self.getTradeFee(market))

            # execute market sell
            stepper = 10.0 ** precision
            truncated = math.trunc(stepper * base_quantity) / stepper

            order = {
                "symbol": market,
                "side": "SELL",
                "type": "MARKET",
                "quantity": truncated,
                "recvWindow": self.recv_window,
            }

            Logger.debug(order)

            # POST /api/v3/order/test
            if test is True:
                resp = self.authAPI("POST", "/api/v3/order/test", order)
            else:
                resp = self.authAPI("POST", "/api/v3/order", order)

            return resp
        except Exception as err:
            ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            Logger.error(ts + " Binance " + " marketSell " + str(err))
            return []

    def authAPI(self, method: str, uri: str, payload: str = {}) -> dict:
        """Initiates a REST API call to the exchange"""

        if not isinstance(method, str):
            raise TypeError("Method is not a string.")

        if not method in ["GET", "POST"]:
            raise TypeError("Method not GET or POST.")

        if not isinstance(uri, str):
            raise TypeError("URI is not a string.")

        signed_uri = [
            "/api/v3/account",
            "/api/v3/allOrders",
            "/api/v3/order",
            "/api/v3/order/test",
            "/sapi/v1/asset/tradeFee",
        ]

        query_string = urlencode(payload, True)
        if uri in signed_uri and query_string:
            query_string = "{}&timestamp={}".format(query_string, self.getTimestamp())
        elif uri in signed_uri:
            query_string = "timestamp={}".format(self.getTimestamp())

        if uri in signed_uri:
            url = (
                self._api_url
                + uri
                + "?"
                + query_string
                + "&signature="
                + self.createHash(query_string)
            )
        else:
            url = self._api_url + uri + "?" + query_string

        params = {"url": url, "params": {}}

        try:
            resp = self._dispatch_request(method)(**params)

            if resp.status_code != 200:
                json = resp.json()
                if "msg" in json:
                    resp_message = resp.json()["msg"]
                elif "message" in json:
                    resp_message = resp.json()["message"]
                else:
                    resp_message = "undefined error"

                message = f"{method} ({resp.status_code}) {self._api_url}{uri} - {resp_message}"
                if self.die_on_api_error:
                    raise Exception(message)
                else:
                    Logger.error(f"Error: {message}")
                    return {}

            resp.raise_for_status()
            return resp.json()

        except requests.ConnectionError as err:
            return self.handle_api_error(err, "ConnectionError")

        except requests.exceptions.HTTPError as err:
            return self.handle_api_error(err, "HTTPError")

        except requests.Timeout as err:
            return self.handle_api_error(err, "Timeout")

        except json.decoder.JSONDecodeError as err:
            return self.handle_api_error(err, "JSONDecodeError")

    def handle_api_error(self, err: str, reason: str) -> dict:
        """Handler for API errors"""

        if self.debug:
            if self.die_on_api_error:
                raise SystemExit(err)
            else:
                Logger.debug(err)
                return {}
        else:
            if self.die_on_api_error:
                raise SystemExit(f"{reason}: {self._api_url}")
            else:
                Logger.info(f"{reason}: {self._api_url}")
                return {}


class PublicAPI(AuthAPIBase):
    def __init__(self, api_url="https://api.binance.com") -> None:
        """Binance API object model

        Parameters
        ----------
        api_url
            Binance API URL
        """

        # options
        self.debug = False
        self.die_on_api_error = False

        valid_urls = [
            "https://api.binance.com",
            "https://api.binance.us",
            "https://testnet.binance.vision",
        ]

        # validate Binance API
        if api_url not in valid_urls:
            raise ValueError("Binance API URL is invalid")

        self._api_url = api_url

    def getTime(self) -> datetime:
        """Retrieves the exchange time"""

        try:
            # GET /api/v3/time
            resp = self.authAPI("GET", "/api/v3/time")
            return self.convert_time(int(resp["serverTime"]))
        except:
            return None

    def getTicker(self, market: str = DEFAULT_MARKET) -> tuple:
        """Retrives the market ticker"""

        # validates the market is syntactically correct
        if not self._isMarketValid(market):
            raise TypeError("Binance market required.")

        # GET /api/v3/ticker/price
        resp = self.authAPI("GET", "/api/v3/ticker/price", {"symbol": market})

        now = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

        if "price" in resp:
            return (str(self.getTime()), float(resp["price"]))
        else:
            return (now, 0.0)

    def getHistoricalData(
        self,
        market: str = DEFAULT_MARKET,
        granularity: str = DEFAULT_GRANULARITY,
        iso8601start: str = "",
        iso8601end: str = "",
    ) -> pd.DataFrame:
        """Retrieves historical market data"""

        # validates the market is syntactically correct
        if not self._isMarketValid(market):
            raise TypeError("Binance market required.")

        # validates granularity is a string
        if not isinstance(granularity, str):
            raise TypeError("Granularity string required.")

        # validates the granularity is supported by Binance
        if not granularity in SUPPORTED_GRANULARITY:
            raise TypeError(
                "Granularity options: " + ", ".join(map(str, SUPPORTED_GRANULARITY))
            )

        # validates the ISO 8601 end date is a string (if provided)
        if not isinstance(iso8601end, str):
            raise TypeError("ISO8601 end integer as string required.")

        if iso8601start != "" and iso8601end == "":
            startTime = int(
                datetime.timestamp(datetime.strptime(iso8601start, "%Y-%m-%dT%H:%M:%S"))
                * 1000
            )

            # GET /api/v3/klines
            resp = self.authAPI(
                "GET",
                "/api/v3/klines",
                {
                    "symbol": market,
                    "interval": granularity,
                    "startTime": startTime,
                    "limit": 300,
                },
            )
        elif iso8601start != "" and iso8601end != "":
            startTime = int(
                datetime.timestamp(datetime.strptime(iso8601start, "%Y-%m-%dT%H:%M:%S"))
                * 1000
            )

            # GET /api/v3/klines
            resp = self.authAPI(
                "GET",
                "/api/v3/klines",
                {
                    "symbol": market,
                    "interval": granularity,
                    "startTime": startTime,
                    "limit": 300,
                },
            )
        else:
            # GET /api/v3/klines
            resp = self.authAPI(
                "GET",
                "/api/v3/klines",
                {"symbol": market, "interval": granularity, "limit": 300},
            )

        # convert the API response into a Pandas DataFrame
        df = pd.DataFrame(
            resp,
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_asset_volume",
                "traker_buy_quote_asset_volume",
                "ignore",
            ],
        )

        df["market"] = market
        df["granularity"] = granularity

        # binance epoch is too long
        df["open_time"] = df["open_time"] + 1
        df["open_time"] = df["open_time"].astype(str)
        df["open_time"] = df["open_time"].str.replace(r"\d{3}$", "", regex=True)

        try:
            freq = FREQUENCY_EQUIVALENTS[SUPPORTED_GRANULARITY.index(granularity)]
        except:
            freq = "D"

        # convert the DataFrame into a time series with the date as the index/key
        try:
            tsidx = pd.DatetimeIndex(
                pd.to_datetime(df["open_time"], unit="s"),
                dtype="datetime64[ns]",
                freq=freq,
            )
            df.set_index(tsidx, inplace=True)
            df = df.drop(columns=["open_time"])
            df.index.names = ["ts"]
            df["date"] = tsidx
        except ValueError:
            tsidx = pd.DatetimeIndex(
                pd.to_datetime(df["open_time"], unit="s"), dtype="datetime64[ns]"
            )
            df.set_index(tsidx, inplace=True)
            df = df.drop(columns=["open_time"])
            df.index.names = ["ts"]
            df["date"] = tsidx

        # if specified, fix end time
        if iso8601end != "":
            df = df[df["date"] <= iso8601end]

        # re-order columns
        df = df[
            ["date", "market", "granularity", "low", "high", "open", "close", "volume"]
        ]

        # correct column types
        df["low"] = df["low"].astype(float)
        df["high"] = df["high"].astype(float)
        df["open"] = df["open"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)

        # reset pandas dataframe index
        df.reset_index()

        return df

    def authAPI(self, method: str, uri: str, payload: str = {}) -> dict:
        """Initiates a REST API call to exchange"""

        if not isinstance(method, str):
            raise TypeError("Method is not a string.")

        if not method in ["GET", "POST"]:
            raise TypeError("Method not GET or POST.")

        if not isinstance(uri, str):
            raise TypeError("URI is not a string.")

        try:
            resp = requests.get(f"{self._api_url}{uri}", params=payload)

            if resp.status_code != 200:
                resp_message = resp.json()["msg"]
                message = f"{method} ({resp.status_code}) {self._api_url}{uri} - {resp_message}"
                if self.die_on_api_error:
                    raise Exception(message)
                else:
                    Logger.error(f"Error: {message}")
                    return {}

            resp.raise_for_status()
            return resp.json()

        except requests.ConnectionError as err:
            return self.handle_api_error(err, "ConnectionError")

        except requests.exceptions.HTTPError as err:
            return self.handle_api_error(err, "HTTPError")

        except requests.Timeout as err:
            return self.handle_api_error(err, "Timeout")

        except json.decoder.JSONDecodeError as err:
            return self.handle_api_error(err, "JSONDecodeError")

    def handle_api_error(self, err: str, reason: str) -> dict:
        """Handler for API errors"""

        if self.debug:
            if self.die_on_api_error:
                raise SystemExit(err)
            else:
                Logger.debug(err)
                return {}
        else:
            if self.die_on_api_error:
                raise SystemExit(f"{reason}: {self._api_url}")
            else:
                Logger.info(f"{reason}: {self._api_url}")
                return {}