import sys

import pytest

sys.path.append('.')
# pylint: disable=import-error
from models.PyCryptoBot import PyCryptoBot

app = PyCryptoBot()

def test_get_version_from_readme():
    global app
    version = self.get_version_from_readme()
    assert version != 'v0.0.0'
