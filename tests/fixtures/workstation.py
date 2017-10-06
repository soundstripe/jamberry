from configparser import ConfigParser
from pathlib import Path
import os
import pytest

from src.jamberry.workstation import JamberryWorkstation


@pytest.fixture(scope='module')
def ws():
    config = ConfigParser()
    config.read('dev_config.ini')
    username, password = config.get('credentials', 'username'), config.get('credentials', 'password')
    return JamberryWorkstation(username, password)


@pytest.fixture()
def order_detail_html():
    p = Path('fixtures', 'data', 'order_details.html')
    with open(p, 'r') as f:
        html = f.read()
    return html


@pytest.fixture()
def order_row_html():
    p = Path('fixtures', 'data', 'order_row.html')
    with open(p, 'r') as f:
        html = f.read()
    return html
