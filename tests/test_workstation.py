import csv
from datetime import datetime
from io import StringIO
import pytest
from bs4 import BeautifulSoup

# import logging
# logging.basicConfig(level=logging.DEBUG)


@pytest.mark.usefixtures('ws')
def test_get_tar(ws):
    t = datetime.now()
    tar = ws.get_tar(t.year, t.month)
    assert ws.logged_in
    tar_buffer = StringIO(str(tar, encoding='utf8'))
    # next line will raise an exception if there is a problem
    tar_csv_dialect = csv.Sniffer().sniff(tar_buffer.read(1024))
    assert tar_csv_dialect is not None


@pytest.mark.usefixtures('ws')
def test_login_logout(ws):
    ws.login()
    assert ws.logged_in
    ws.logout()
    assert not ws.logged_in


@pytest.mark.usefixtures('ws')
def test_get_orders(ws):
    orders = ws.get_orders()
    assert ws.logged_in
    assert b'ctl00_contentMain_dgAllOrders' in orders


@pytest.mark.usefixtures('ws')
def test_get_archive_orders(ws):
    orders = ws.get_archive_orders()
    assert ws.logged_in
    soup = BeautifulSoup(orders)
    assert soup.find(id='ctl00_main_dgAllOrders') is not None


@pytest.mark.usefixtures('ws')
def test_create_and_delete_tmp_search_cart_retail(ws):
    ws.create_tmp_search_cart_retail()
    assert ws._cart_url is not None
    assert 'cart/display' in ws._cart_url
    ws.delete_tmp_search_cart_retail()
    resp = ws.br.get('https://workstation.jamberry.com/us/en/wscart')
    assert b'tmpSearchRetail' not in resp.content
    assert ws._cart_url is None


@pytest.mark.usefixtures('ws')
def test_get_autocomplete(ws):
    pass


