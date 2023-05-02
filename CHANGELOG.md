# Change Log
All notable changes to this project will be documented in this file.

Upgrade version:
- git checkout main
- git pull

Upgrade library dependencies (if required):
- python3 -m pip install -r requirements.txt -U

## [4.4.0] - 2021-11-01

- Add /scanner to TG Bot to scan marks and start bots
- add multiple market scanning to scanner.py

## [4.3.2] - 2021-11-02

- fix for Kucoin multiple buys on same traded pair when API error occurs

## [4.3.1] - 2021-10-28

- fix for Kucoin margin calculation
- fix for Kucoin getOrders not always returning a response
- fix for SIM smartswitching
- Update for TG bot to show uptime with /showinfo

## [4.3.0] - 2021-10-23

- formatting CHANGELOG.md

## [4.2.1] - 2021-10-19

- fixed TG BOT checking if market/pair already exists before saving
- fixed TG BOT indicator states

## [4.2.0] - 2021-10-17

- Added /deletebot will delete bot from /startbot list
- fixed issue with fast-sample with no date causing exception
- fixed issue when bot throws an exception it does not exit
- fixed issue when exception is raised TG bot still thinks the bot is active
- fixed /startbots will only start bots that are not already running
- fixed when Telegram replaces -- with a long dash
- fixed if folder exists in telegram_data folder
- added validation for exchange and markets when using /addnew
- refactored TG bot code

## [4.1.0] - 2021-10-01

- Fixed issue when websockets are enabled making to many API calls (for those that are still required they will be called once per minute instead of on every iteration).
- Added telegram bot (telegram_bot.py) this has to be run separately to pycryptobot.py
- Added option to enable the telegram bot this does not start it, just enables writing data required for the telegram bot (--enabletelegrambotcontrol)
- Added user_id to telegram section in config, this is used so that only you can control the bot
- Added datafolder to telegram section in config, this is used when running multiple bots from different folders
- Added Telegram Bot Setup instructions text file
- Removed some debug logging left in by mistake
- Fix issue with Kucoin margins not calculating correctly
- Added Kucoin to yaml files

## [4.0.4] - 2021-09-27

- Added Kucoin to --init (auto config)
- Added ability to parse --market in the same format as coinbase (ie ONT-USD)
- Added Websockets webhooks example script
- Added Coinbase Pro webhooks example script
- Telegram output tweaks
- Print currency trading on dryrun simulation summary

## [4.0.3] - 2021-09-23

- fix for binance webhooks granularity

## [4.0.2] - 2021-09-23

- fix for kucoin minimum order function raising an exception

## [4.0.1] - 2021-09-22

- add option to disable insufficient funds exception and log as warning instead (--enableinsufficientfundslogging)

## [4.0.0] - 2021-09-21

### Added

- Kucoin exchange API (websockets not enabled)
- Websockets available for Binance and Coinbase Pro --websocket
- Added websvc.py to Docker

### Changed

- Updated healthcheck to use a basic HTTPS request instead of a getTime() API call
- Disabled Seasonal ARIMA Model ML by default --enableml
- Removed healthcheck to reduce API calls for scaling

## [3.6.1] - 2021-09-13

### Added

- Websockets POC scripts for Coinbase Pro and Binance
- Seasonal ARIMA model predictions are not optional --enableml
- Updating Dockerfile to python:3.9-slim-bullseye
- switching to multistage venv Dockerfile and adding build-essentials in 1st stage to minimize Image size and build dependencies from source like numpy or statsmodels on arm64

## [3.6.0] - 2021-09-06

### Added

- fixed williams %r indicator and added it to the websvc dashboard
- added adx14 indicator and added it to the websvc dashboard
- fix for sim index "IndexError('index 0 is out of bounds for axis 0 with size 0')"
- fix for DF High not tracking the sim date in use, this stopped nobuynearhighpcnt working fully
- moved trades csv file to CSV folder

## [3.5.0] - 2021-09-05

### Added

- added Seasonal ARIMA model predictions to websvc analysis

## [3.4.0] - 2021-09-03

### Changed

- update to smartswitch sim processing speed.
- update to sim summary to include total margin and profit/loss.
- fixed timestamp bug when using simstartdate.
- fixed graphs in sim mode.
- remove limit for sims using specific granularity.
- fix for profit and loss summary for simulations
- added trade history in simulation summary in verbose mode will also export to CSV '({market}{daterange}_trades.csv)'
- added trade history export to csv 'trades.csv'
- added web portal ./websvc.py

## [3.3.1] - 2021-08-29

### Changed

- added additional error handling for Coinbase Pro getTime()

## [3.3.0] - 2021-08-28

### Changed

- added "nobuynearhighpcnt" to specify the percentage from high that the bot should not buy if "disablebuynearhigh" is not specified.
- added a catch and display of exception message for getTime()

## [3.2.15] - 2021-08-24

### Changed

- add proper shebang and exec permissions to pycryptobot.py (run from CLI, etc.)

## [3.2.14] - 2021-08-24

### Changed

- Found and fixed 'currency' key exception
- Fixed simulation summary

## [3.2.13] - 2021-08-23

### Changed

- Binance US is missing 'tradeFee' API endpoint, now returns default fee for this url

## [3.2.12] - 2021-08-23

### Added

- Verbose debug option to isSellTrigger and isWaitTrigger

### Changed

- Logic in isSellTrigger and isWaitTrigger

## [3.2.11] - 2021-08-22

### Changed

- Adjustment to isWaitTrigger
- Tidying up repo
- Fixed version

## [3.2.10] - 2021-08-20

### Changed

- 'stats' for binance was retuning incorrect percentage gains.
- 'statdetail' was not working for binance as some values were string instead of float

## [3.2.9] - 2021-08-16

### Added

- 'nosellminpcnt' to specify minimum margin to not sell
- 'nosellmaxpcnt' to specify maximum margin to not sell
- fixed Stats.py issue on smaller datasets
- fixed recvWindow issue
- binance.us is now working

### Changed

- Various small bug fixes

## [3.2.8] - 2021-08-12

### Changed

- Surrounded API calls for both Binance and Coinbase Pro within a try except

## [3.2.7] - 2021-08-11

### Changed

- Surrounded signed Binance API calls within a try except

## [3.2.6] - 2021-08-09

### Changed

- Fixed custom logging bug
- Add a try/catch to resolve "currency" key issue with recvWindow
- Removed previous failsafe check for "currency" in getAccounts

## [3.2.5] - 2021-08-09

### Changed

- Added failsafe check for "currency" in getAccounts

## [3.2.4] - 2021-08-09

### Changed

- Updated authAPI to return an empty JSON response on recvWindow

## [3.2.3] - 2021-08-09

### Changed

- Config file bugfix

## [3.2.2] - 2021-08-08

### Add

- Drafted new release

## [3.2.1] - 2021-08-08

### Changed

- Removed log rotation from the bot as it shouldn't be there
- Removed debug code which was left in

## [3.2.0] - 2021-08-08

### Changed

- Binance code improvements
- Updated Stochastic RSI

## [3.1.1] - 2021-08-07

### Changed

- Updated Binance price calculation

## [3.1.0] - 2021-08-07

### Changed

- Refactor text boxes in logs

## [3.0.1] - 2021-08-07

### Changed

- Fix recvWindow for binance

## [3.0.0] - 2021-08-03

### Changed

- Replaced python-binance library with in-built code
- Loads of enhancements and improvements
- Unit tests added and improved

## [2.49.1] - 2021-08-1

### Changed

## [2.51.0] - 2021-08-06

### Changed

- Add section about code style to CONTRIBUTING.md

## [2.50.0] - 2021-08-06

### Changed

- Upgrade pip to latest version before using it to install packages

## [2.49.1] - 2021-08-01

### Changed

- The gitignore pattern excluded the configmap.yaml for the helm chart.

## [2.49.0] - 2021-08-01

## Added

- Added Kubernetes helm charts

## [2.48.2] - 2021-08-01

## Changed

- Fixed misaligned text on initial bot info table

## [2.48.1] - 2021-08-01

### Changed

- Fixed output formatting

## [2.48.0] - 2021-08-01

### Changed

- Fixed fast-sample smartswitching for coinbase

## [2.47.1] - 2021-07-13

### Changed

- Fixed simulation date issues

## [2.47.0] - 2021-07-13

### Changed

- Fixed smartwitch for coinbase historic data limit
- Fixed smartswitching date sync

## [2.46.2] - 2021-07-13

### Changed

- Added --disablebuyema argument

- Updated README.md

## [2.46.1] - 2021-07-12

### Changed

- use `granularity` instead of `self.getGranularity`

- use `granularity` instead of `self.getGranularity()`  in `getHistoricalDateRange()` call

* Update README.md

## [2.46.0] - 2021-07-09

### Changed

- Increased number of attempts at retrieving previous orders in binance api

## [2.45.2] - 2021-07-08

### Changed

- Improved ADX technical indicator

### Added

- Added ATR technical indicator

## [2.45.1] - 2021-07-06

### Changed

- Fixed ARIMA bug in coinbase pro when frequency not set in dataframe

## [2.45.0] - 2021-07-06

### Added

- Added ADX technical indicator
- Added auto migrate API keys to coinbasepro.key and/or binance.key

## [2.44.1] - 2021-07-05

### Changed

- Updated README.md

## [2.44.0] - 2021-07-05

### Added

- Added log file rotation

## [2.43.1] - 2021-07-05

### Changed

- Filter on filled orders only in Binance dataframe

## [2.42.0] - 2021-07-03

### Changed

- Fixed smartswitch for binance simulation mode and live
- Fixed smartswitch timings to use sim date instead of just defaulting to current date
- Update goldencross using the actual sim date in sim mode only
- Update to check when your last order is buy but your coin balance in 0 switch to buy instead
    - Possible bug if you transfer or convert coins on the exchange instead of selling them
- Update to use correct market data in sim mode + smartswitching

## [2.41.0] - 2021-07-03

### Added

- statdetail flag which gives a detailed list of transactions (works with --statstartdate and --statgroup)

## [2.40.0] - 2021-07-03

### Changed

- Updated validation for Telegram keys

## [2.39.0] - 2021-06-27

### Changed

- Added "api_key_file" to config to keep credentials out of config files for safety

## [2.38.0] - 2021-06-23

### Changed

- Added statstartdate flag to ignore trades before a given date in stats function
- Added statgroup flag to merge stats of multiple currency pairs
- Fixed stats for coinbase pro

## [2.37.3] - 2021-06-22

### Changed

- Fixed smart switch back bug

## [2.37.2] - 2021-06-21

### Changed

- Fixed "simstart" bug

## [2.37.1] - 2021-06-18

### Changed

- Fixed issue from previous release

## [2.37.0] - 2021-06-18

### Changed

- Refactored the new stats feature into it's own Stats class
- Fixed a bug with getOrders() for Coinbase Pro
- Fixed the rounding issue with precision greater than 4
- Fixed the dummy account which has been broken with a previous PR
- Updated unit tests

## [2.31.1] - 2021-06-13

### Changed

- Create default config if missing, avoid creating empty config

## [2.31.0] - 2021-06-13

### Changed

- Separated strategy into Strategy model for custom strategies

## [2.30.2] - 2021-06-12

### Changed

- Minor changes in quote currency extraction (binance.py)

## [2.30.1] - 2021-06-12

### Changed

- Suppressed ARIMA model warning

## [2.30.0] - 2021-06-12

### Changed

- Improved ARIMA model output to console
- Reduced polling from 2 minutes to 1 minute

## [2.29.0] - 2021-06-11

### Added

- Added the Seasonal ARIMA machine learning model for price predictions

## [2.28.0] - 2021-06-11

### Added

- Added Stochastic RSI and Williams %R technical indicators

## [2.27.0] - 2021-06-08

### Changed

- Optimised simulations, they run a lot faster now

### Added

- Added app.getHistoricalDataChained

## [2.26.0] - 2021-06-07

### Changed

- Updated validation to allow for custom Coinbase Pro passphrases

## [2.25.0] - 2021-06-06

### Added

- Added CHANGELOG.md

### Changed

- Removed check for 'fees' on Binance orders which doesn't exist

### Fixed

- Pandas 'SettingWithCopyWarning' in models/exchange/coinbase_pro/api.py