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
    tar = ws.fetch_tar(t.year, t.month)
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
def test_fetch_orders(ws):
    orders = ws.fetch_orders()
    assert ws.logged_in
    assert orders.find(id=b'ctl00_contentMain_dgAllOrders')


@pytest.mark.usefixtures('ws')
def test_fetch_archive_orders(ws):
    orders = ws.fetch_archive_orders()
    assert ws.logged_in
    assert orders.find(id='ctl00_main_dgAllOrders') is not None


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
def test_fetch_autocomplete(ws):
    pass


@pytest.mark.usefixtures('ws')
def test_parsed_orders(ws):
    parsed_orders = list(ws.parsed_orders())
    assert parsed_orders is not None


@pytest.mark.usefixtures('ws')
def test_parse_order_detail(ws):
    orders_iter = ws.parsed_orders()
    order = next(orders_iter)
    order_id = order['id']
    parsed_details = ws.parse_order_details(order_id)
    assert 'lines' in parsed_details
    assert 'address' in parsed_details




