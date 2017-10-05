import csv
from datetime import datetime, timedelta
import pytest
from bs4 import BeautifulSoup

import logging
logging.basicConfig(level=logging.DEBUG)


@pytest.mark.usefixtures('ws')
def test_fetch_tar(ws):
    # test fetching current TAR
    tar = ws.fetch_tar()
    assert ws.logged_in
    tar_str = str(tar, encoding='utf8')
    i = tar_str.find('\n', 0, 1024)
    # next line will raise an exception if there is a problem
    tar_csv_dialect = csv.Sniffer().sniff(tar_str[:i])
    assert tar_csv_dialect is not None

    # test fetching last months TAR
    t = datetime.now() - timedelta(weeks=35)
    last_month_tar = ws.fetch_tar(year=t.year, month=t.month)
    last_month_tar_str = str(last_month_tar, encoding='utf8')
    i = last_month_tar_str.find('\n', 0, 1024)
    tar_csv_dialect = csv.Sniffer().sniff(last_month_tar_str[:i])
    assert tar_csv_dialect is not None

    # if they match, something is wrong with the date selector
    assert tar_str != last_month_tar_str


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
def test_orders(ws):
    orders = list(ws.orders())
    assert orders is not None


@pytest.mark.usefixtures('ws', 'order_detail_html')
def test_extract_shipping_address(ws, order_detail_html):
    soup = BeautifulSoup(order_detail_html)
    address = ws.extract_shipping_address(soup)
    lines = address.split('\n')
    assert lines[0] == '123 Somewhere St'
    assert lines[1] == 'Somewhere, CA 12345-6789'


@pytest.mark.usefixtures('ws', 'order_detail_html')
def test_extract_line_items(ws, order_detail_html):
    soup = BeautifulSoup(order_detail_html)
    line_items = ws.extract_line_items(soup)
    assert line_items[0].name == 'Crimson Crush'
    assert line_items[0].quantity == 2
    assert line_items[3].total == float(65)


@pytest.mark.usefixtures('ws')
def test_downline_consultants(ws):
    for consultant, activity in ws.downline_consultants():
        assert consultant.id is not None
        assert activity.timestamp is not None

@pytest.mark.usefixtures('ws', 'order_row_html')
def test_parse_order_row(ws, order_row_html):
    soup = BeautifulSoup(order_row_html).tr
    order = ws.parse_order_row(soup)
    assert order.id == '12345678'
    assert order.customer_name == 'Foo Bar'
    assert order.shipping_name == 'Foo Bar'
    assert order.order_date == datetime(2017, 10, 1, 6, 0)
    assert order.subtotal == float(15)
    assert order.shipping_fee == 0
    assert order.tax == 1.09
    assert order.status == 'Shipped'
    assert order.order_type == 'Party'
    assert 'OrderDetails.aspx?id=12345678' in order.order_details_url
    assert order.customer_id == '1234567'
    assert order.total == 16.09
    assert order.qv == 0
    assert order.hostess == 'Foo Manchu'
    assert order.party == 'What a Party!'
    assert order.ship_date == datetime(2017, 10, 1)


@pytest.mark.usefixtures('ws')
def test_customers(ws):
    for customer in ws.customers():
        assert customer.name is not None





