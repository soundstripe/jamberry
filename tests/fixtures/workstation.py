from configparser import ConfigParser
from pathlib import Path
import os
import pytest

from src.jamberry.workstation import JamberryWorkstation


@pytest.fixture(scope='module')
def ws():
    config = ConfigParser()
    config['credentials'] = {
        'username': '',
        'password': '',
    }
    credentials = config['credentials']
    with open('dev_config.ini') as config_file:
        config.read_file(config_file)
    username, password = credentials.get('username'), credentials.get('password')
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
