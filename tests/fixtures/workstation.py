from configparser import ConfigParser

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
