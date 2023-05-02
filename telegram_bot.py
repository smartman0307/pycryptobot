#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bot to reply to Telegram messages.

Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the bot.
"""
import argparse
from asyncore import write
import logging
import os
import json
import subprocess
import sys
import re
import urllib.request

from datetime import datetime
from time import sleep, time

# from pandas.core.frame import DataFrame
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.bot import Bot, BotCommand
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    Filters,
    ConversationHandler,
    MessageHandler,
)
from telegram.replykeyboardremove import ReplyKeyboardRemove
from apscheduler.schedulers.background import BackgroundScheduler
from models.chat import Telegram

from models.telegram import (
    TelegramControl,
    TelegramHelper,
    TelegramHandler,
    TelegramActions,
    ConfigEditor,
    SettingsEditor
)

scannerSchedule = BackgroundScheduler(timezone="UTC")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

# TYPING_RESPONSE = 1
CHOOSING, TYPING_REPLY = range(2)
EXCHANGE, MARKET, ANYOVERRIDES, OVERRIDES, SAVE, START = range(6)
EXCEPT_EXCHANGE, EXCEPT_MARKET = range(2)

replykeyboard = [["Coinbase Pro", "Binance", "Kucoin"]]

markup = ReplyKeyboardMarkup(replykeyboard, one_time_keyboard=True)


class TelegramBotBase:
    """
    base level for telegram bot
    """

    userid = ""
    datafolder = os.curdir
    data = {}

    helper = None
    handler = None
    editor = None

    def _check_if_allowed(self, userid, update) -> bool:
        if str(userid) != self.userid:
            update.message.reply_text("<b>Not authorised!</b>", parse_mode="HTML")
            return False

        return True


class TelegramBot(TelegramBotBase):
    """
    main telegram bot class
    """

    def __init__(self):
        self.token = ""
        self.config_file = ""

        self.cl_args = ""
        self.market = ""

        self.exchange = ""
        self.pair = ""
        self.overrides = ""

        parser = argparse.ArgumentParser(description="PyCryptoBot Telegram Bot")
        parser.add_argument(
            "--config",
            type=str,
            dest="config_file",
            help="pycryptobot config file",
            default="config.json",
        )
        parser.add_argument(
            "--datafolder",
            type=str,
            help="Use the datafolder at the given location, useful for multi bots running in different folders",
            default="",
        )

        args = parser.parse_args()

        self.config_file = args.config_file

        with open(os.path.join(self.config_file), "r", encoding="utf8") as json_file:
            self.config = json.load(json_file)

        self.token = self.config["telegram"]["token"]
        self.userid = self.config["telegram"]["user_id"]

        if "datafolder" in self.config["telegram"]:
            self.datafolder = self.config["telegram"]["datafolder"]

        if args.datafolder != "":
            self.datafolder = args.datafolder

        self.helper = TelegramHelper(self.datafolder, self.config, self.config_file)

        if not os.path.exists(os.path.join(self.datafolder, "telegram_data")):
            os.mkdir(os.path.join(self.datafolder, "telegram_data"))

        if os.path.isfile(os.path.join(self.datafolder, "telegram_data", "data.json")):
            write_ok, try_cnt = False, 0
            while not write_ok and try_cnt <= 5:
                try_cnt += 1
                self.helper.read_data("data.json")
                write_ok = True
                if "trades" not in self.helper.data:
                    self.helper.data.update({"trades": {}})
                    write_ok = self.helper.write_data()
                if "markets" not in self.helper.data:
                    self.helper.data.update({"markets": {}})
                    write_ok = self.helper.write_data()
                if "scannerexceptions" not in self.helper.data:
                    self.helper.data.update({"scannerexceptions": {}})
                    write_ok = self.helper.write_data()
                if not write_ok:
                    sleep(1)
        else:
            ds = {"trades": {}, "markets": {}, "scannerexceptions": {}}
            self.helper.data = ds
            self.helper.write_data()

        self.updater = Updater(
            self.token,
            use_context=True,
        )

        self.helper.load_config()

        # self.handler = TelegramHandler(self.datafolder, self.userid, self.helper)
        # self.control = TelegramControl(self.datafolder, self.helper)
        # self.actions = TelegramActions(self.datafolder, self.helper)
        # self.editor = ConfigEditor(self.datafolder, self.helper)
        # self.setting = SettingsEditor(self.datafolder, self.helper)
# 
#     def reload_config(self):
#         # Config section for bot pair scanner
#         self.atr72pcnt = 2.0
#         self.enableleverage = False
#         self.use_default_scanner = 1
#         self.maxbotcount = 0
#         self.autoscandelay = 0
#         self.enable_buy_next = True
#         self.autostart = False
#         if "scanner" in self.config:
#             self.atr72pcnt = (
#                 self.config["scanner"]["atr72_pcnt"]
#                 if "atr72_pcnt" in self.config["scanner"]
#                 else self.atr72pcnt
#             )
#             self.enableleverage = (
#                 self.config["scanner"]["enableleverage"]
#                 if "enableleverage" in self.config["scanner"]
#                 else self.enableleverage
#             )
#             self.use_default_scanner = (
#                 self.config["scanner"]["use_default_scanner"]
#                 if "use_default_scanner" in self.config["scanner"]
#                 else self.use_default_scanner
#             )
#             self.maxbotcount = (
#                 self.config["scanner"]["maxbotcount"]
#                 if "maxbotcount" in self.config["scanner"]
#                 else self.maxbotcount
#             )
#             self.autoscandelay = (
#                 self.config["scanner"]["autoscandelay"]
#                 if "autoscandelay" in self.config["scanner"]
#                 else 0
#             )
#             self.enable_buy_next = (
#                 self.config["scanner"]["enable_buy_next"]
#                 if "enable_buy_next" in self.config["scanner"]
#                 else True
#             )

        self.helper = TelegramHelper(self.datafolder, self.config, self.config_file)

        self.handler = TelegramHandler(self.datafolder, self.userid, self.helper)
        self.control = TelegramControl(self.datafolder, self.helper)
        self.actions = TelegramActions(self.datafolder, self.helper)
        self.editor = ConfigEditor(self.datafolder, self.helper)
        self.setting = SettingsEditor(self.datafolder, self.helper)

    def _question_which_exchange(self, update, context):
        """start new bot ask which exchange"""

        self.exchange = ""
        self.overrides = ""
        self.helper.send_telegram_message(update, "Select the exchange:", markup, context=context)

    def _answer_which_exchange(self, update, context) -> bool:
        """start bot validate exchange and ask which market/pair"""
        if update.message.text.lower() == "cancel":
            update.message.reply_text(
                "Operation Cancelled", reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END

        if (
            update.message.text == "Coinbase Pro"
            or update.message.text == "Kucoin"
            or update.message.text == "Binance"
        ):
            self.exchange = update.message.text.lower()
            if update.message.text == "Coinbase Pro":
                self.exchange = "coinbasepro"
        else:
            if self.exchange == "":
                self.helper.send_telegram_message(update, "Invalid Exchange Entered!.", context=context)
                return False

        return True

    def _question_which_pair(self, update, context):

        self.market = ""
        self.helper.send_telegram_message(update, "Which market/pair is this for?", ReplyKeyboardRemove(), context)

    def _answer_which_pair(self, update, context) -> bool:
        if update.message.text.lower() == "cancel":
            self.helper.send_telegram_message(
                update, "Operation Cancelled", ReplyKeyboardRemove(), context
            )
            return ConversationHandler.END

        if self.exchange in ("coinbasepro", "kucoin"):
            p = re.compile(r"^[0-9A-Z]{1,20}\-[1-9A-Z]{2,5}$")
            if not p.match(update.message.text):
                self.helper.send_telegram_message(
                    update, "Invalid market format", ReplyKeyboardRemove(), context
                )
                return False
        elif self.exchange == "binance":
            p = re.compile(r"^[A-Z0-9]{4,25}$")
            if not p.match(update.message.text):
                self.helper.send_telegram_message(
                    update, "Invalid market format.", ReplyKeyboardRemove(), context
                )
                return False

        self.pair = update.message.text

        return True

    # Define command handlers. These usually take the two arguments update and context.

    def setcommands(self, update, context) -> None:
        command = [
            BotCommand("controlpanel", "show command buttons"),
            BotCommand("cleandata", "clean JSON data files"),
            BotCommand("addexception", "add pair to scanner exception list"),
            BotCommand("removeexception", "remove pair from scanner exception list"),
            BotCommand(
                "startscanner", "start auto scan high volume markets and start bots"
            ),
            BotCommand("stopscanner", "stop auto scan high volume markets"),
            BotCommand("addnew", "add and start a new bot"),
            BotCommand("deletebot", "delete bot from startbot list"),
            BotCommand("margins", "show margins for all open trades"),
            BotCommand("trades", "show closed trades"),
            BotCommand("stats", "show exchange stats for market/pair"),
            BotCommand("help", "show help text")
            # BotCommand("showinfo", "show all running bots status"),
            # BotCommand("showconfig", "show config for selected exchange"),
            # BotCommand("startbots", "start all or selected bot"),
            # BotCommand("stopbots", "stop all or the selected bot"),
            # BotCommand("pausebots", "pause all or selected bot"),
            # BotCommand("resumebots", "resume paused bots"),
            # BotCommand("buy", "manual buy"),
            # BotCommand("sell", "manual sell"),
        ]

        ubot = Bot(self.token)
        ubot.set_my_commands(command)

        self.helper.send_telegram_message(update, "<i>Bot Commands Created</i>", ReplyKeyboardRemove(), context=context)

    def help(self, update, context):
        """Send a message when the command /help is issued."""

        helptext = "<b>Information Command List</b>\n\n"
        helptext += (
            "<b>/setcommands</b> - <i>add all commands to bot for easy access</i>\n"
        )
        helptext += "<b>/margins</b> - <i>show margins for open trade</i>\n"
        helptext += "<b>/trades</b> - <i>show closed trades</i>\n"
        helptext += "<b>/stats</b> - <i>display stats for market</i>\n\n"
        # helptext += "<b>/showinfo</b> - <i>display bot(s) status</i>\n"
        # helptext += "<b>/showconfig</b> - <i>show config for exchange</i>\n\n"
        helptext += "<b>Interactive Command List</b>\n\n"
        helptext += "<b>/controlpanel</b> - <i>show interactive control buttons</i>\n"
        helptext += "<b>/cleandata</b> - <i>check and remove any bad Json files</i>\n"
        helptext += "<b>/addnew</b> - <i>start the requested pair</i>\n\n"
        # helptext += "<b>/pausebots</b> - <i>pause all or the selected bot</i>\n"
        # helptext += "<b>/resumebots</b> - <i>resume paused bots</i>\n"
        # helptext += "<b>/stopbots</b> - <i>stop all or the selected bots</i>\n"
        # helptext += "<b>/startbots</b> - <i>start all or the selected bots</i>\n"
        # helptext += "<b>/sell</b> - <i>sell market pair on next iteration</i>\n"
        # helptext += "<b>/buy</b> - <i>buy market pair on next iteration</i>\n\n"
        helptext += "<b>Market Scanner Commands</b>\n\n"
        helptext += "<b>/startscanner</b> - <i>start auto scan high volume markets and start bots</i>\n"
        helptext += "<b>/stopscanner</b> - <i>stop auto scan high volume markets</i>\n"
        helptext += "<b>/addexception</b> - <i>add pair to scanner exception list</i>\n"
        helptext += (
            "<b>/removeexception</b> - <i>remove pair from scanner exception list</i>\n"
        )

        self.helper.send_telegram_message(update, helptext, context=context)

    def trades(self, update, context):
        """List trades"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return

        self.helper.read_data()

        output = ""
        for dt in self.helper.data["trades"]:
            output = ""
            output = (
                output + f"<b>{self.helper.data['trades'][dt]['pair']}</b>\n{dt}"
            )
            output = (
                output
                + f"\n<i>Sold at: {self.helper.data['trades'][dt]['price']}   Margin: {self.helper.data['trades'][dt]['margin']}</i>\n"
            )

            if output != "":
                self.helper.send_telegram_message(update, output, context=context)

    def statsrequest(self, update: Updater, context):
        """Ask which exchange stats are wanted for"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return None

        self.helper.send_telegram_message(update, "Select the exchange", markup, context=context)

        return CHOOSING

    def stats_exchange_received(self, update, context):
        """Ask which market stats are wanted for"""
        if update.message.text.lower() == "done":
            return None

        if update.message.text.lower() == "cancel":
            self.helper.send_telegram_message(update, "Operation Cancelled", ReplyKeyboardRemove(), context=context)
            return ConversationHandler.END

        if update.message.text in ("Coinbase Pro", "Kucoin", "Binance"):
            self.exchange = update.message.text.lower()
            if update.message.text == "Coinbase Pro":
                self.exchange = "coinbasepro"
        else:
            if self.exchange == "":
                self.helper.send_telegram_message(update, "Invalid Exchange Entered!", context=context)
                self.statsrequest(update, context)
                return None

        self.helper.send_telegram_message(update, "Which market/pair do you want stats for?", ReplyKeyboardRemove(), context=context)

        return TYPING_REPLY

    def stats_pair_received(self, update, context):
        """Show stats for selected exchange and market"""
        if update.message.text.lower() == "done":
            return None

        if update.message.text.lower() == "cancel":
            self.helper.send_telegram_message(update, "Operation Cancelled", ReplyKeyboardRemove(), context=context)
            return ConversationHandler.END

        if self.exchange in ("coinbasepro", "kucoin"):
            p = re.compile(r"^[0-9A-Z]{1,20}\-[1-9A-Z]{2,5}$")
            if not p.match(update.message.text):
                self.helper.send_telegram_message(update, "Invalid market format", ReplyKeyboardRemove(), context=context)
                self.stats_exchange_received(update, context)
                return None
        elif self.exchange == "binance":
            p = re.compile(r"^[A-Z0-9]{4,25}$")
            if not p.match(update.message.text):
                self.helper.send_telegram_message(update, "Invalid market format", ReplyKeyboardRemove(), context=context)
                self.stats_exchange_received(update, context)
                return None

        self.pair = update.message.text

        self.helper.send_telegram_message(update, "<i>Gathering Stats, please wait...</i>", context=context)
        
        output = self.helper.start_process(
            self.pair, self.exchange, "--stats --live 1", "telegram", True
        )
        self.helper.send_telegram_message(update, output, context=context)

        return ConversationHandler.END

    def newbot_request(self, update: Updater, context):
        """start new bot ask which exchange"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return None

        self._question_which_exchange(update, context)

        return EXCHANGE

    def newbot_exchange(self, update, context):
        """start bot validate exchange and ask which market/pair"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return None

        if not self._answer_which_exchange(update, context):
            self.newbot_request(update, context)

        self._question_which_pair(update, context)

        return ANYOVERRIDES

    def newbot_any_overrides(self, update, context) -> None:
        """start bot validate market and ask if overrides required"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return None

        if not self._answer_which_pair(update, context):
            self.newbot_exchange(update, context)
            return None

        r_keyboard = [["Yes", "No"]]

        mark_up = ReplyKeyboardMarkup(r_keyboard, one_time_keyboard=True)

        self.helper.send_telegram_message(
            update, "Do you want to use any commandline overrides?", mark_up, context
        )

        return MARKET

    def newbot_market(self, update, context):
        """start bot - ask for overrides if none required ask to save bot"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return None

        if update.message.text == "No":
            reply_keyboard = [["Yes", "No"]]
            mark_up = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            self.helper.send_telegram_message(update, "Do you want to save this?", mark_up, context)
            return SAVE

        self.helper.send_telegram_message(
            update, "Tell me any other commandline overrides to use?", ReplyKeyboardRemove(), context
        )

        return OVERRIDES

    def newbot_overrides(self, update, context):
        """start bot - ask to save bot"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return None

        # Telegram desktop client can auto replace -- with a single long dash
        # this converts it back to --
        self.overrides = update.message.text.replace(
            b"\xe2\x80\x94".decode("utf-8"), "--"
        )

        reply_keyboard = [["Yes", "No"]]
        mark_up = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        self.helper.send_telegram_message(update, "Do you want to save this?", mark_up, context)

        return SAVE

    def newbot_save(self, update, context):
        """start bot - save if required ask if want to start"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return None
        self.helper.logger.info("called newbot_save")
        if update.message.text == "Yes":
            write_ok, try_cnt = False, 0
            while not write_ok and try_cnt <= 5:
                try_cnt += 1
                try:
                    self.helper.read_data()
                    if "markets" in self.helper.data:
                        if not self.pair in self.helper.data["markets"]:
                            self.helper.data["markets"].update(
                                {
                                    self.pair: {
                                        "overrides": f"--exchange {self.exchange} --market {self.pair} {self.overrides}"
                                    }
                                }
                            )
                            write_ok = self.helper.write_data()
                            if write_ok:
                                self.helper.send_telegram_message(update, f"{self.pair} saved \u2705", context=context)
                            else:
                                sleep(1)
                        else:
                            self.helper.send_telegram_message(update,
                                f"{self.pair} already setup, no changes made.", context=context
                            )
                            write_ok = True
                    else:
                        self.helper.data.update({"markets": {}})
                        self.helper.data["markets"].update(
                            {
                                self.pair: {
                                    "overrides": f"--exchange {self.exchange} --market {self.pair} {self.overrides}"
                                }
                            }
                        )
                        write_ok = self.helper.write_data()
                        if write_ok:
                            self.helper.send_telegram_message(update, f"{self.pair} saved \u2705", context=context)
                        else:
                            sleep(1)
                except Exception as err:
                    print(err)


        reply_keyboard = [["Yes", "No"]]
        mark_up = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        self.helper.send_telegram_message(update, "Do you want to start this bot?", mark_up, context)

        return START

    def newbot_start(self, update, context, startmethod: str = "telegram") -> None:
        """start bot - start bot if want"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return None

        if update.message.text == "No":
            self.helper.send_telegram_message(update,
                "Command Complete, have a nice day.", ReplyKeyboardRemove(), context
            )
            return ConversationHandler.END

        if (
            self.helper.start_process(
                self.pair, self.exchange, self.overrides, startmethod
            )
            is False
        ):
            self.helper.send_telegram_message(update,
                f"{self.pair} is already running, no action taken.",
                ReplyKeyboardRemove(), context
            )
        else:
            if startmethod != "scanner":
                self.helper.send_telegram_message(update,
                    f"{self.pair} crypto bot Starting",
                    ReplyKeyboardRemove(), context
                )

        self.helper.send_telegram_message(update,
            "Command Complete, have a nice day.", ReplyKeyboardRemove(), context
        )

        return ConversationHandler.END

    def error(self, update, context):
        """Log Errors"""
        self.helper.logger.error(msg="Exception while handling an update:", exc_info=context.error)
        try:
            if "HTTPError" in context.error.args[0]:
                while self.checkconnection() == False:
                    self.helper.logger.warning("No internet connection found")
                    self.updater.start_polling(poll_interval=30)
                    sleep(30)
                self.updater.start_polling()
                return
            # else:
            # logger.error(msg="Exception while handling an update:", exc_info=context.error)
        except:
            pass

    def done(self, update, context):
        """added for conversations to end"""
        return ConversationHandler.END

    def checkconnection(self) -> bool:
        """internet connection check"""
        try:
            urllib.request.urlopen("https://api.telegram.org")
            return True
        except:
            print("No internet connection")
            return False

    def _cleandata(self):
        jsonfiles = self.helper.get_active_bot_list()
        for i in range(len(jsonfiles), 0, -1):
            jfile = jsonfiles[i - 1]

            self.helper.logger.info("checking %s", jfile)

            while self.helper.read_data(jfile) == False:
                sleep(0.2)

            last_modified = datetime.now() - datetime.fromtimestamp(
                os.path.getmtime(
                    os.path.join(self.datafolder, "telegram_data", f"{jfile}.json")
                )
            )
            if "margin" not in self.helper.data:
                self.helper.logger.info("deleting %s", jfile)
                os.remove(os.path.join(self.datafolder, "telegram_data", f"{jfile}.json"))
                continue
            if (
                self.helper.data["botcontrol"]["status"] == "active"
                and last_modified.seconds > 120
                and (last_modified.seconds != 86399 and last_modified.days != -1)
            ):
                logger.info("deleting %s %s", jfile, str(last_modified))
                os.remove(
                    os.path.join(self.datafolder, "telegram_data", f"{jfile}.json")
                )
                continue
            elif (
                self.helper.data["botcontrol"]["status"] == "exit"
                and last_modified.seconds > 120
                and last_modified.seconds != 86399
            ):
                self.helper.logger.info("deleting %s %s", jfile, str(last_modified.seconds))
                os.remove(os.path.join(self.datafolder, "telegram_data", f"{jfile}.json"))

    def ExceptionExchange(self, update, context):
        """start new bot ask which exchange"""
        self._question_which_exchange(update, context)

        return EXCEPT_EXCHANGE

    def ExceptionPair(self, update, context):
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return

        self._answer_which_exchange(update, context)

        self._question_which_pair(update, context)

        return EXCEPT_MARKET

    def ExceptionAdd(self, update, context):
        """start bot - save if required ask if want to start"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return None

        self.helper.logger.info("called ExceptionAdd")
        
        self._answer_which_pair(update, context)

        self.helper.read_data()

        if "scannerexceptions" not in self.helper.data:
            self.helper.data.update({"scannerexceptions": {}})

        if not self.pair in self.helper.data["scannerexceptions"]:
            write_ok, try_cnt = False, 0
            while not write_ok and try_cnt <= 5:
                try_cnt += 1
                self.helper.data["scannerexceptions"].update({self.pair: {}})
                write_ok = self.helper.write_data()
                if not write_ok:
                    sleep(1)
            self.helper.send_telegram_message(update,
                f"{self.pair} Added to Scanner Exception List \u2705",
                ReplyKeyboardRemove(), context
            )
        else:
            self.helper.send_telegram_message(update,
                f"{self.pair} Already on exception list",
                ReplyKeyboardRemove(), context
            )

        return ConversationHandler.END

    def ExceptionRemove(self, update, context):
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return

        self.control.ask_exception_bot_list(update, context)
        return

    def marginrequest(self, update, context):
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return

        self.handler.ask_margin_type(update, context)
        return

    def showbotinfo(self, update, context) -> None:
        """Show running bot status"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return

        self.actions.get_bot_info(update, context)
        return

    def sellrequest(self, update, context):
        """Manual sell request (asks which coin to sell)"""
        self.control.ask_sell_bot_list(update)
        return

    def buyrequest(self, update, context):
        """Manual buy request (asks which coin to buy)"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return

        self.control.ask_buy_bot_list(update)
        return

    def showconfigrequest(self, update, context):
        """display config settings (ask which exchange)"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return

        self.handler.ask_config_options(update)
        return

    def pausebotrequest(self, update, context) -> None:
        """Ask which bots to pause"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return

        self.control.ask_pause_bot_list(update)

    def restartbotrequest(self, update, context) -> None:
        """Ask which bot to restart"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return

        self.control.ask_resume_bot_list(update)

    def startallbotsrequest(self, update, context) -> None:
        """Ask which bot to start from start list (or all)"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return

        self.control.ask_start_bot_list(update)
        return

    def stopbotrequest(self, update, context) -> None:
        """ask which active bots to stop (or all)"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return

        self.control.ask_stop_bot_list(update)
        return

    def deleterequest(self, update, context):
        """ask which bot to delete"""
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return

        self.control.ask_delete_bot_list(update, context)

    def StartScanning(self, update, context):
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return

        self.handler._check_scheduled_job(update, context)
        self.helper.logger.info("Start scanning using default scanner? %s", bool(self.helper.use_default_scanner))
        self.helper.send_telegram_message(update, "Operation Started",context=context)
        self.actions.start_market_scan(
            update,
            context,
            True if self.helper.use_default_scanner == 1 else False,
            False if len(context.args) > 0 and context.args[0] == "debug" else True,
            False if len(context.args) > 0 and context.args[0] == "noscan" else True
        )

    def StopScanning(self, update, context):
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return
        self.handler._remove_scheduled_job(update, context)

    def cleandata(self, update, context) -> None:
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return

        self._cleandata()

        self.actions.get_bot_info(update, context)
        self.helper.send_telegram_message(update, "Operation Complete", context=context)

    def RestartBots(self, update, context):
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return None

        self.control.ask_restart_bot_list(update)

    def StartOpenOrderBots(self, update, context):
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return None

        self.actions.start_open_orders(update, context)

    def statstwo(self, update, context):
        jsonfiles = os.listdir(os.path.join(self.datafolder, "telegram_data"))
        for file in jsonfiles:
            exchange = "coinbasepro"
            if file.__contains__("output.json"):
                if file.__contains__("coinbasepro"):
                    exchange = "coinbasepro"
                if file.__contains__("binance"):
                    exchange = "binance"
                if file.__contains__("kucoin"):
                    exchange = "kucoin"

                self.helper.send_telegram_message(update,
                    "<i>Gathering Stats, please wait...</i>", context=context
                )

                with open(
                    os.path.join(self.datafolder, "telegram_data", file),
                    "r",
                    encoding="utf8",
                ) as json_file:
                    data = json.load(json_file)

                pairs = ""
                for pair in data:
                    if pair.__contains__("DOWN") or pair.__contains__("UP"):
                        continue

                    # count += 1
                    pairs = pairs + pair + " "

                output = subprocess.getoutput(
                    f"python3 pycryptobot.py --stats --exchange {exchange}  --statgroup {pairs}  "
                )
                self.helper.send_telegram_message(update, output, context=context)
                sleep(30)
                self.helper.send_telegram_message(update, "Pausing before next set", context=context)

    def getBotList(self, update, context):
        if not self._check_if_allowed(context._user_id_and_data[0], update):
            return None

        # query = update.callback_query
        # try:
        #     query.answer()
        # except:
        #     pass

        buttons = []

        for market in self.helper.get_active_bot_list("active"):
            while self.helper.read_data(market) == False:
                sleep(0.2)

            if "botcontrol" in self.helper.data:
                buttons.append(InlineKeyboardButton(market, callback_data=f"bot_{market}"))

        if len(buttons) > 0:
            self.helper.send_telegram_message(update, "<b>Select a market</b>", self.control.sort_inline_buttons(buttons, "bot"), context=context)
        else:
            self.helper.send_telegram_message(update, "<b>No bots found.</b>", context=context)

    def Request(self, update, context):

        userid = context._user_id_and_data[0]

        if self._check_if_allowed(userid, update):
            self.helper.load_config()
            key_markup = self.handler.get_request()
            self.helper.send_telegram_message(update,
                "<b>PyCryptoBot Command Panel.</b>",
                key_markup,
                context
            )

def main():
    """Start the bot."""
    # Create telegram bot configuration
    botconfig = TelegramBot()

    # Get the dispatcher to register handlers
    dp = botconfig.updater.dispatcher

    # Information commands
    dp.add_handler(CommandHandler("help", botconfig.help))
    dp.add_handler(CommandHandler("margins", botconfig.marginrequest, Filters.all))
    dp.add_handler(CommandHandler("trades", botconfig.trades, Filters.text))
    dp.add_handler(
        CommandHandler("showconfig", botconfig.showconfigrequest, Filters.text)
    )
    # dp.add_handler(CommandHandler("showinfo", botconfig.showbotinfo, Filters.text))

    # General Action Command
    dp.add_handler(CommandHandler("setcommands", botconfig.setcommands))
    dp.add_handler(CommandHandler("buy", botconfig.buyrequest, Filters.text))
    dp.add_handler(CommandHandler("sell", botconfig.sellrequest, Filters.text))
    dp.add_handler(CommandHandler("pausebots", botconfig.pausebotrequest, Filters.text))
    dp.add_handler(
        CommandHandler("resumebots", botconfig.restartbotrequest, Filters.text)
    )
    dp.add_handler(CommandHandler("startbots", botconfig.startallbotsrequest))
    dp.add_handler(CommandHandler("stopbots", botconfig.stopbotrequest))
    dp.add_handler(CommandHandler("deletebot", botconfig.deleterequest, Filters.text))

    dp.add_handler(
        CommandHandler("startscanner", botconfig.StartScanning, Filters.text)
    )
    dp.add_handler(CommandHandler("stopscanner", botconfig.StopScanning, Filters.text))

    dp.add_handler(CommandHandler("cleandata", botconfig.cleandata, Filters.text))

    dp.add_handler(
        CommandHandler("removeexception", botconfig.ExceptionRemove, Filters.text)
    )

    dp.add_handler(CommandHandler("restart", botconfig.RestartBots))

    dp.add_handler(CommandHandler("reopen", botconfig.StartOpenOrderBots))

    dp.add_handler(CommandHandler("ex", botconfig.getBotList))

    dp.add_handler(CommandHandler("statsgroup", botconfig.statstwo))
    # Response to Question handler
    dp.add_handler(CallbackQueryHandler(botconfig.handler.get_response))

    dp.add_handler(CommandHandler("controlPanel", botconfig.Request))

    conversation_exception = ConversationHandler(
        entry_points=[CommandHandler("addexception", botconfig.ExceptionExchange)],
        states={
            EXCEPT_EXCHANGE: [
                MessageHandler(
                    Filters.text, botconfig.ExceptionPair, pass_user_data=True
                )
            ],
            EXCEPT_MARKET: [
                MessageHandler(
                    Filters.text, botconfig.ExceptionAdd, pass_user_data=True
                )
            ],
        },
        fallbacks=[("Done", botconfig.done)],
    )

    conversation_stats = ConversationHandler(
        entry_points=[CommandHandler("stats", botconfig.statsrequest)],
        states={
            CHOOSING: [
                MessageHandler(
                    Filters.text, botconfig.stats_exchange_received, pass_user_data=True
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    Filters.text, botconfig.stats_pair_received, pass_user_data=True
                )
            ],
        },
        fallbacks=[("Done", botconfig.done)],
    )

    conversation_newbot = ConversationHandler(
        entry_points=[CommandHandler("addnew", botconfig.newbot_request)],
        states={
            EXCHANGE: [MessageHandler(Filters.text, botconfig.newbot_exchange)],
            MARKET: [MessageHandler(Filters.text, botconfig.newbot_market)],
            ANYOVERRIDES: [
                MessageHandler(Filters.text, botconfig.newbot_any_overrides)
            ],
            OVERRIDES: [MessageHandler(Filters.text, botconfig.newbot_overrides)],
            SAVE: [MessageHandler(Filters.text, botconfig.newbot_save)],
            START: [MessageHandler(Filters.text, botconfig.newbot_start)],
        },
        fallbacks=[("Done", botconfig.done)],
    )


    dp.add_handler(conversation_stats)
    dp.add_handler(conversation_newbot)
    dp.add_handler(conversation_exception)
    # log all errors
    dp.add_error_handler(botconfig.error)

    botconfig._cleandata()

    # Start the Bot
    botconfig.updater.start_polling()

    # Run the bot until you press Ctrl-C
    # since start_polling() is non-blocking and will stop the bot gracefully.
    botconfig.updater.idle()


if __name__ == "__main__":
    main()
