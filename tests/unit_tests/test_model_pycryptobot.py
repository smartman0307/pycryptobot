import json, os, pytest, sys

sys.path.append('.')
# pylint: disable=import-error
from models.PyCryptoBot import PyCryptoBot

def test_instantiate_model_without_error():
    if not os.path.exists('config.json'):
        with pytest.raises(ValueError) as execinfo:
            PyCryptoBot()
        assert str(execinfo.value) == "Invalid config.json: [Errno 2] No such file or directory: 'config.json'"

        config = {
            "binance": {
                "api_url": "https://api.binance.com",
                "api_key": "0000000000000000000000000000000000000000000000000000000000000000",
                "api_secret": "0000000000000000000000000000000000000000000000000000000000000000",
            },
            "coinbasepro": {
                "api_url": "https://api.pro.coinbase.com",
                "api_key": "00000000000000000000000000000000",
                "api_secret": "0000/0000000000/0000000000000000000000000000000000000000000000000000000000/00000000000==",
                "api_passphrase": "00000000000"
            }
        }

        try:
            config_json = json.dumps(config, indent=4)
            fh = open('config.json', 'w')
            fh.write(config_json)
            fh.close()
        except Exception as err:
            print (err)

    app = PyCryptoBot()
    assert type(app) is PyCryptoBot

    with open('config.json', 'r') as fh:
        config = fh.read()
        config_json = json.loads(config)

        if 'binance' in config_json:
            app = PyCryptoBot(exchange='binance')
            assert type(app) is PyCryptoBot
            assert app.getExchange() == 'binance'

        if 'coinbasepro' in config_json:
            app = PyCryptoBot(exchange='coinbasepro')
            assert type(app) is PyCryptoBot
            assert app.getExchange() == 'coinbasepro'

        if 'dummy' in config_json:
            app = PyCryptoBot(exchange='dummy')
            assert type(app) is PyCryptoBot
            assert app.getExchange() == 'dummy'

    app = PyCryptoBot(filename='config.json')
    assert type(app) is PyCryptoBot

def test_configjson_binance():
    config = {
        "binance": {
            "api_url": "https://api.binance.com",
            "api_key": "0000000000000000000000000000000000000000000000000000000000000000",
            "api_secret": "0000000000000000000000000000000000000000000000000000000000000000",
        }
    }

    try:
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert type(app) is PyCryptoBot
    assert app.getExchange() == 'binance'

    if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
        os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')

def test_configjson_binance_invalid_api_url():
    config = {
        "binance": {
            "api_url": "ERROR",
            "api_key": "0000000000000000000000000000000000000000000000000000000000000000",
            "api_secret": "0000000000000000000000000000000000000000000000000000000000000000",
        }
    }

    try:
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    with pytest.raises(ValueError) as execinfo:
        PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert str(execinfo.value) == 'Invalid config.json: Binance API URL is invalid'

    if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
        os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')

def test_configjson_binance_invalid_api_key():
    config = {
        "binance": {
            "api_url": "https://api.binance.com",
            "api_key": "ERROR",
            "api_secret": "0000000000000000000000000000000000000000000000000000000000000000",
        }
    }

    try:
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    with pytest.raises(TypeError) as execinfo:
        PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert str(execinfo.value) == 'Binance API key is invalid'

    if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
        os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')

def test_configjson_binance_invalid_api_secret():
    config = {
        "binance": {
            "api_url": "https://api.binance.com",
            "api_key": "0000000000000000000000000000000000000000000000000000000000000000",
            "api_secret": "ERROR",
        }
    }

    try:
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    with pytest.raises(TypeError) as execinfo:
        PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert str(execinfo.value) == 'Binance API secret is invalid'

    if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
        os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')

def test_configjson_coinbasepro():
    config = {
        "coinbasepro": {
            "api_url": "https://api.pro.coinbase.com",
            "api_key": "00000000000000000000000000000000",
            "api_secret": "0000/0000000000/0000000000000000000000000000000000000000000000000000000000/00000000000==",
            "api_passphrase": "00000000000"
        }
    }

    try:
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert type(app) is PyCryptoBot
    assert app.getExchange() == 'coinbasepro'

    if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
        os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')

def test_configjson_coinbasepro_legacy():
    config = {
        "api_url": "https://api.pro.coinbase.com",
        "api_key": "00000000000000000000000000000000",
        "api_secret": "0000/0000000000/0000000000000000000000000000000000000000000000000000000000/00000000000==",
        "api_passphrase": "00000000000"
    }

    try:
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert type(app) is PyCryptoBot
    assert app.getExchange() == 'coinbasepro'

    if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
        os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')

def test_configjson_coinbasepro_invalid_api_url():
    config = {
        "coinbasepro": {
            "api_url": "ERROR",
            "api_key": "00000000000000000000000000000000",
            "api_secret": "0000/0000000000/0000000000000000000000000000000000000000000000000000000000/00000000000==",
            "api_passphrase": "00000000000"
        }
    }

    try:
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    with pytest.raises(ValueError) as execinfo:
        PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert str(execinfo.value) == 'Invalid config.json: Coinbase Pro API URL is invalid'

    if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
        os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')

def test_configjson_coinbasepro_invalid_api_key():
    config = {
        "coinbasepro": {
            "api_url": "https://api.pro.coinbase.com",
            "api_key": "ERROR",
            "api_secret": "0000/0000000000/0000000000000000000000000000000000000000000000000000000000/00000000000==",
            "api_passphrase": "00000000000"
        }
    }

    try:
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    with pytest.raises(TypeError) as execinfo:
        PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert str(execinfo.value) == 'Coinbase Pro API key is invalid'

    if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
        os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')

def test_configjson_coinbasepro_invalid_api_secret():
    config = {
        "coinbasepro": {
            "api_url": "https://api.pro.coinbase.com",
            "api_key": "00000000000000000000000000000000",
            "api_secret": "ERROR",
            "api_passphrase": "00000000000"
        }
    }

    try:
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    with pytest.raises(TypeError) as execinfo:
        PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert str(execinfo.value) == 'Coinbase Pro API secret is invalid'

    if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
        os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')

def test_configjson_coinbasepro_invalid_api_passphrase():
    config = {
        "coinbasepro": {
            "api_url": "https://api.pro.coinbase.com",
            "api_key": "00000000000000000000000000000000",
            "api_secret": "0000/0000000000/0000000000000000000000000000000000000000000000000000000000/00000000000==",
            "api_passphrase": "ERROR"
        }
    }

    try:
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    with pytest.raises(TypeError) as execinfo:
        PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert str(execinfo.value) == 'Coinbase Pro API passphrase is invalid'

    if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
        os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')

def test_configjson_binance_granularity():
    config = {
       "binance": {
            "api_url": "https://api.binance.com",
            "api_key": "0000000000000000000000000000000000000000000000000000000000000000",
            "api_secret": "0000000000000000000000000000000000000000000000000000000000000000",
            "config": {}
        }
    }

    try:
        granularity = '1m'
        config['binance']['config']['granularity'] = granularity
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()

        app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
        assert type(app) is PyCryptoBot
        assert app.getExchange() == 'binance'
        assert app.getGranularity() == 60

        if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
            os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')
    except Exception as err:
        print (err)

    try:
        granularity = '5m'
        config['binance']['config']['granularity'] = granularity
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()

        app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
        assert type(app) is PyCryptoBot
        assert app.getExchange() == 'binance'
        assert app.getGranularity() == 300

        if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
            os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')
    except Exception as err:
        print (err)

    try:
        granularity = '15m'
        config['binance']['config']['granularity'] = granularity
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()

        app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
        assert type(app) is PyCryptoBot
        assert app.getExchange() == 'binance'
        assert app.getGranularity() == 900

        if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
            os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')
    except Exception as err:
        print (err)

    try:
        granularity = '1h'
        config['binance']['config']['granularity'] = granularity
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()

        app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
        assert type(app) is PyCryptoBot
        assert app.getExchange() == 'binance'
        assert app.getGranularity() == 3600

        if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
            os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')
    except Exception as err:
        print (err)

    try:
        granularity = '6h'
        config['binance']['config']['granularity'] = granularity
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()

        app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
        assert type(app) is PyCryptoBot
        assert app.getExchange() == 'binance'
        assert app.getGranularity() == 21600

        if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
            os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')
    except Exception as err:
        print (err)

    try:
        granularity = '1d'
        config['binance']['config']['granularity'] = granularity
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()

        app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
        assert type(app) is PyCryptoBot
        assert app.getExchange() == 'binance'
        assert app.getGranularity() == 86400

        if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
            os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')
    except Exception as err:
        print (err)

def test_configjson_binance_invalid_granularity():
    config = {
       "binance": {
            "api_url": "https://api.binance.com",
            "api_key": "0000000000000000000000000000000000000000000000000000000000000000",
            "api_secret": "0000000000000000000000000000000000000000000000000000000000000000",
            "config": {}
        }
    }

    try:
        config['binance']['config']['granularity'] = 60
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert type(app) is PyCryptoBot
    assert app.getExchange() == 'binance'
    assert app.getGranularity() == 3600 # default if invalid

    if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
        os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')

def test_configjson_coinbasepro_granularity():
    config = {
        "coinbasepro": {
            "api_url": "https://api.pro.coinbase.com",
            "api_key": "00000000000000000000000000000000",
            "api_secret": "0000/0000000000/0000000000000000000000000000000000000000000000000000000000/00000000000==",
            "api_passphrase": "00000000000",
            "config": {}
        }
    }

    try:
        granularity = 60
        config['coinbasepro']['config']['granularity'] = granularity
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()

        app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
        assert type(app) is PyCryptoBot
        assert app.getExchange() == 'coinbasepro'
        assert app.getGranularity() == granularity

        if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
            os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')
    except Exception as err:
        print (err)

    try:
        granularity = 300
        config['coinbasepro']['config']['granularity'] = granularity
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()

        app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
        assert type(app) is PyCryptoBot
        assert app.getExchange() == 'coinbasepro'
        assert app.getGranularity() == granularity

        if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
            os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')
    except Exception as err:
        print (err)

    try:
        granularity = 900
        config['coinbasepro']['config']['granularity'] = granularity
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()

        app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
        assert type(app) is PyCryptoBot
        assert app.getExchange() == 'coinbasepro'
        assert app.getGranularity() == granularity

        if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
            os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')
    except Exception as err:
        print (err)

    try:
        granularity = 3600
        config['coinbasepro']['config']['granularity'] = granularity
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()

        app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
        assert type(app) is PyCryptoBot
        assert app.getExchange() == 'coinbasepro'
        assert app.getGranularity() == granularity

        if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
            os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')
    except Exception as err:
        print (err)

    try:
        granularity = 21600
        config['coinbasepro']['config']['granularity'] = granularity
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()

        app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
        assert type(app) is PyCryptoBot
        assert app.getExchange() == 'coinbasepro'
        assert app.getGranularity() == granularity

        if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
            os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')
    except Exception as err:
        print (err)

    try:
        granularity = 86400
        config['coinbasepro']['config']['granularity'] = granularity
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()

        app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
        assert type(app) is PyCryptoBot
        assert app.getExchange() == 'coinbasepro'
        assert app.getGranularity() == granularity

        if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
            os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')
    except Exception as err:
        print (err)

def test_configjson_coinbasepro_invalid_granularity():
    config = {
        "coinbasepro": {
            "api_url": "https://api.pro.coinbase.com",
            "api_key": "00000000000000000000000000000000",
            "api_secret": "0000/0000000000/0000000000000000000000000000000000000000000000000000000000/00000000000==",
            "api_passphrase": "00000000000",
            "config": {}
        }
    }

    try:
        config['coinbasepro']['config']['granularity'] = '1m'
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert type(app) is PyCryptoBot
    assert app.getExchange() == 'coinbasepro'
    assert app.getGranularity() == 3600 # default if invalid

    if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
        os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')

def test_configjson_islive():
    config = {
        "coinbasepro": {
            "api_url": "https://api.pro.coinbase.com",
            "api_key": "00000000000000000000000000000000",
            "api_secret": "0000/0000000000/0000000000000000000000000000000000000000000000000000000000/00000000000==",
            "api_passphrase": "00000000000",
            "config": {}
        }
    }

    try:
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert type(app) is PyCryptoBot
    assert app.getExchange() == 'coinbasepro'
    assert not app.isLive()

    try:
        config['coinbasepro']['config']['live'] = 1
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert type(app) is PyCryptoBot
    assert app.isLive()

    app.setLive(0)
    assert not app.isLive()

    if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
        os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')

def test_configjson_graphs():
    config = {
        "coinbasepro": {
            "api_url": "https://api.pro.coinbase.com",
            "api_key": "00000000000000000000000000000000",
            "api_secret": "0000/0000000000/0000000000000000000000000000000000000000000000000000000000/00000000000==",
            "api_passphrase": "00000000000",
            "config": {}
        }
    }

    try:
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert type(app) is PyCryptoBot
    assert app.getExchange() == 'coinbasepro'
    assert not app.shouldSaveGraphs()

    try:
        config['coinbasepro']['config']['graphs'] = 1
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert type(app) is PyCryptoBot
    assert app.getExchange() == 'coinbasepro'
    assert app.shouldSaveGraphs()

    if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
        os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')

def test_configjson_isverbose():
    config = {
        "coinbasepro": {
            "api_url": "https://api.pro.coinbase.com",
            "api_key": "00000000000000000000000000000000",
            "api_secret": "0000/0000000000/0000000000000000000000000000000000000000000000000000000000/00000000000==",
            "api_passphrase": "00000000000",
            "config": {}
        }
    }

    try:
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert type(app) is PyCryptoBot
    assert app.getExchange() == 'coinbasepro'
    assert not app.isVerbose()

    try:
        config['coinbasepro']['config']['verbose'] = 1
        config_json = json.dumps(config, indent=4)
        fh = open('tests/unit_tests/data/pycryptobot_pytest_config.json', 'w')
        fh.write(config_json)
        fh.close()
    except Exception as err:
        print (err)

    app = PyCryptoBot(filename='tests/unit_tests/data/pycryptobot_pytest_config.json')
    assert type(app) is PyCryptoBot
    assert app.getExchange() == 'coinbasepro'
    assert app.isVerbose()

    if os.path.exists('tests/unit_tests/data/pycryptobot_pytest_config.json'):
        os.remove('tests/unit_tests/data/pycryptobot_pytest_config.json')