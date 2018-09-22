import json
from abc import abstractmethod, ABC
from collections import OrderedDict
from csv import DictReader
from datetime import datetime, timedelta
from functools import wraps
from itertools import chain
from urllib.parse import urljoin, urlencode
import re
from typing import Iterable, Tuple

import mechanicalsoup
import dateutil.parser

from .product import Product
from .customer import Customer
from .util import currency_to_decimal, deprecated
from .consultant import Consultant, ConsultantActivityRecord
from .order import Order, OrderLineItem


def field_data(soup, name) -> (str, str):
    return name, soup.find('input', attrs=dict(name=name)).get('value')


def requires_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        ws = args[0]
        ws.login()
        return f(*args, **kwargs)

    return wrapper


# noinspection PyDunderSlots
def customer_from_row(row) -> Customer:
    c = Customer()
    c.id = row['userId']
    c.name = row['name']
    c.address_line_1 = row['address1']
    c.address_line_2 = row['address2']
    c.address_city = row['city']
    c.address_state = row['state']
    c.address_zip = row['zip']
    c.address_country = row['country']
    c.phone = row['phone']
    c.type = row['customerType']

    first_purchase = row['firstPurchase']
    try:
        c.first_purchase_date = dateutil.parser.parse(first_purchase)
    except ValueError:
        c.first_purchase_date = first_purchase

    last_purchase = row['lastPurchase']
    try:
        c.last_purchase_date = dateutil.parser.parse(last_purchase)
    except ValueError:
        c.last_purchase_date = last_purchase

    c.sponsor_qv = row['sponsorQV']
    c.sponsor_rv = row['sponsorRV']
    c.other_qv = row['allQV']
    c.other_rv = row['allRV']
    c.original_consultant = row['origConsultant']
    return c


def parse_customer_angel_row(row) -> Customer:
    c = Customer()
    c.name = row['nameFirst'] + " " + row['nameLast']
    c.address_line_1 = row['Address1']
    c.address_line_2 = row['Address2']
    c.address_city = row['City']
    c.address_state = row['State']
    c.address_zip = row['Zip']
    c.email = row['Email']
    c.phone = row['phone']
    c.birthdate = datetime.strptime(row['birthdate'], '%m/%d/%Y')
    c.last_purchase_date = dateutil.parser.parse(row['trans1'])
    return c


# noinspection PyDunderSlots
def parse_team_activity_row(row) -> (Consultant, ConsultantActivityRecord):
    """Given a dict-like row (from TAR CSV export), creates a Consultant object and a
    ConsultantActivityRecord object."""
    c = Consultant()
    c.id = row['Contact']
    c.downline_level = int(row['DLL'])
    c.first_name = row['First']
    c.last_name = row['Last']
    c.email = row['Email']
    c.phone = row['Phone']
    c.address_line1 = row['Address']
    c.address_city = row['City']
    c.address_state = row['State']
    c.address_zip = row['ZIP']
    c.address_country = row['Country']
    c.start_date = dateutil.parser.parse(row['Enrollment']) if len(row['Enrollment']) else ''
    c.consultant_type = row['Type']

    a = ConsultantActivityRecord()
    a.timestamp = datetime.now()
    a.generation = row['GEN']
    a.attending_conference = row['Attending Conference']
    a.status = row['Status']
    a.last_login = dateutil.parser.parse(row['Last Login']) if len(row['Last Login']) else ''
    a.title = row['Title']
    a.pay_title = row['Pay Title']
    a.rv = currency_to_decimal(row['RV'])
    a.qv = currency_to_decimal(row['QV'])
    a.cv = currency_to_decimal(row['CV'])
    a.tqv = currency_to_decimal(row['TQV'])
    a.dqv = currency_to_decimal(row['DQV'])
    a.active_legs = row['Active Legs']
    a.new_recruits = row['Recruits']
    a.style_vips = row['SVIPs']
    a.total_downline = row['Organization Total']
    a.trip_points = row['Trip']
    a.team_manager = row['Team Manager']
    a.sponsor_name = row['Sponsor']
    a.sponsor_email = row['Sponsor Email']
    a.highest_title = row['highest']

    return c, a


# noinspection PyDunderSlots
def parse_archive_order_row_soup(row_soup) -> Order:
    cols = row_soup.findAll('td')
    o = Order()
    o.id = cols[0].a.text
    o.customer_name = cols[1].a.text
    o.shipping_name = cols[2].a.text
    o.order_date = datetime.strptime(cols[3].a.text, '%m/%d/%Y') + timedelta(hours=6)
    o.order_details_url = cols[0].a['href']
    o.subtotal = currency_to_decimal(cols[4].text)
    o.shipping_fee = currency_to_decimal(cols[5].text)
    o.tax = currency_to_decimal(cols[6].text)
    o.status = cols[9].text.strip()
    o.retail_bonus = currency_to_decimal(cols[10].text)
    return o


@deprecated('use fetch_order_api instead')
def parse_order_row_soup(row_soup) -> Order:
    o = Order()
    o.customer_name = row_soup.find(text="Placed By:").next.strip()
    if o.customer_name == u'':
        o.customer_name = row_soup.find(text="Placed By:").next.next.next.strip()
        o.customer_url = 'https://workstation.jamberry.com' + row_soup.findAll(['a'])[2]['href']
        o.customer_id = o.customer_url.split('/')[-1]
        try:
            o.customer_contact = row_soup.find(text="Contact: ").next.strip()
        except AttributeError:
            # no contact for this order
            pass
    o.id = row_soup.td.a.text
    o.order_type = row_soup.find(text="Type:").next.strip()
    o.order_date = datetime.strptime(row_soup.td.nextSibling.a.text, '%b %d, %Y') + timedelta(hours=6)
    o.order_details_url = row_soup.td.a['href']
    o.shipping_name = row_soup.find(text="Shipped To:").next.strip()
    o.subtotal = row_soup.find(text="Subtotal:").next.strip()
    o.shipping_fee = row_soup.find(text="Shipping:").next.strip()
    o.tax = row_soup.find(text="Tax:").next.strip()
    o.total = row_soup.find(text="Total:").next.strip()
    o.qv = row_soup.find(text="QV:").next.strip()
    o.status = row_soup.find(text="Status: ").next.strip()
    row_find = row_soup.find(text=re.compile('Hostess:'))
    if row_find:
        o.hostess = row_find.next.strip()
    row_find = row_soup.find(text=re.compile('Party:'))
    if row_find:
        o.party = row_find.next.strip()
    row_find = row_soup.find(text='Shipped On:')
    if row_find:
        ship_date_str = row_find.next.strip()
        o.ship_date = datetime.strptime(ship_date_str, '%m/%d/%Y')
    return o


def extract_line_items(detail_soup) -> Iterable[OrderLineItem]:
    line_items_table = detail_soup.find(id='ctl00_main_dgMain')
    line_items_rows = line_items_table.findAll('tr')[1:]  # skip header row
    line_items = []
    for row in line_items_rows:
        cells = row.findAll('td')

        line_item = OrderLineItem()
        line_item.sku = cells[0].text.strip()
        line_item.name = cells[1].text.strip()
        line_item.price = cells[2].text.strip()
        line_item.quantity = int(cells[3].text.strip())
        line_item.total = currency_to_decimal(cells[4].text.strip().split('\n')[0])

        line_items.append(line_item)
    return line_items


def extract_shipping_address(detail_soup) -> str:
    iter_address_lines = detail_soup.find(text=re.compile('Address')).findNext('dd').stripped_strings
    shipping_address = '\n'.join(iter_address_lines)
    return shipping_address


class Workstation(ABC):
    def __init__(self, *args, **kwargs):
        self.br = Workstation.init_browser()

    @classmethod
    def init_browser(cls):
        br = mechanicalsoup.StatefulBrowser()
        br.session.headers.update({
            'User-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
        })
        return br

    @abstractmethod
    def orders(self) -> Iterable[Order]:
        return iter([])

    @abstractmethod
    def customers(self) -> Iterable[Customer]:
        return iter([])

    @abstractmethod
    def downline_consultants(self) -> Iterable[Tuple[Consultant, ConsultantActivityRecord]]:
        return iter([])

    @abstractmethod
    def catalog_products(self) -> Iterable[Product]:
        return iter([])

# noinspection PyDunderSlots
def parse_customer_angel_csv(customers_angel_csv_data):
    customer_rows = DictReader(customers_angel_csv_data.decode(encoding='utf-8').splitlines())
    yield from (parse_customer_angel_row(row) for row in customer_rows)


def parse_product(row) -> Product:
    p = Product()
    p.img = row['img']
    p.sku = row['sku']
    p.in_stock = row['inStock']
    p.price = row['price']
    p.retail_price = row['priceRetailFull']
    p.slug = row['slug']
    p.tags = row['tags']
    p.title = row['title']
    p.nas_design = row['nasDesign']
    p.product_type = row['productType']
    p.sized_images = row['sizedImages']
    p.on_sale = row['isOnSale']
    return p


def parse_order_api(item):
    order = Order()
    order.id = item['orderID']
    order.customer_id = item['userId']
    order.customer_name = '{orderedFirstName} {orderedLastName}'.format(**item)
    order.hostess = item['party']['hostName'] if item['party'] else None
    order.party = item['party']['name'] if item['party'] else None
    order.order_date = datetime.strptime(item['orderedDate'], '%Y-%m-%dT%H:%M:%S')
    order.status = item['shippedStatus']['description']
    order.ship_date = item.get('shippedDate', None)
    order.qv = item['qv']
    #order.retail_bonus = item['']
    order.total = item['orderTotal']
    order.shipping_fee = item['shippingTotal']
    order.tax = item['taxTotal']
    order.order_type = item['orderType']['orderTypeDescription']
    order.shipping_name = f"{item['shippingFirstName']} {item['shippingLastName']}"
    order.shipping_address = f"{order.shipping_name}\n" \
                             f"{item['shippingAddress1']}\n" \
                             f"{item['shippingAddress2']}\n" \
                             f"{item['shippingCity']}, {item['shippingState']} {item['shippingPostalCode']}"
    order.subtotal = item['subTotal']
    order.customer_contact = item['orderedEmail']
    order.line_items = []
    for osi in item['orderStatusItems']:
        li = OrderLineItem()
        li.name = osi['name']
        li.total = osi['priceTotal']
        li.price = osi['pricePer']
        li.quantity = osi['quantity']
        li.sku = osi['sku']
        order.line_items.append(li)
    return order


class JamberryWorkstation(Workstation):
    def __init__(self, username=None, password=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username = username
        self.password = password
        self._cart_url = None
        self._logged_in = False
        self._consultant_id = None
        self.workstation_url = 'https://workstation.jamberry.com'
        self.urls = self.init_urls()
        if username is None and password is None:
            self.read_config()

    def __del__(self):
        if getattr(self, '_cart_url', None) is not None:
            self.delete_tmp_search_cart_retail()

    def init_urls(self):
        urls = dict(
            JAMBERRY_LOGIN_URL=urljoin(self.workstation_url, ''),
            JAMBERRY_LOGOUT_URL=urljoin(self.workstation_url, 'login/logout.aspx'),
            JAMBERRY_TAR_URL=urljoin(self.workstation_url, 'associate/commissions/Activity.aspx'),
            JAMBERRY_ORDERS_URL=urljoin(self.workstation_url, 'associate/orders/'),
            JAMBERRY_ORDERS_API_URL=urljoin(self.workstation_url, 'api/reporting/v1/order/history'),
            JAMBERRY_ORDERS_ARCHIVE_URL=urljoin(self.workstation_url, 'associate/orders/Archive.aspx'),
            JAMBERRY_CUSTOMER_ANGEL_CSV_URL=urljoin(self.workstation_url,
                                                    'associate/associates/ExportClientAngelForm.aspx'),
            JAMBERRY_VIEW_CARTS_URL=urljoin(self.workstation_url, 'us/en/wscart'),
            JAMBERRY_CREATE_NEW_RETAIL_CART_URL=urljoin(self.workstation_url, 'us/en/wscart/cart/new?cartType=2'),
            JAMBERRY_CREATE_NEW_RETAIL_CART_POST_URL=urljoin(self.workstation_url, 'us/en/wscart/cart/new?cartType=2'),
            JAMBERRY_API_CUSTOMER_VOLUME_URL=urljoin(self.workstation_url,
                                                     'api/reporting/v1/consultant/{}/customers/volume'),
            JAMBERRY_API_TEAM_ACTIVITY_REPORT_URL=urljoin(self.workstation_url, 'api/consultant/{}/team/activity/csv'),
        )
        return urls

    def login(self):
        if self.logged_in:
            return
        br = self.br
        br.open(self.urls['JAMBERRY_LOGIN_URL'])
        br.select_form("form#Form1")
        credentials = {
            'username': self.username,
            'password': self.password,
        }
        for field, value in credentials.items():
            br[field] = value
        resp = br.submit_selected()
        if resp.status_code != 200:
            raise Exception("could not log in")
        if b'entered are invalid' in resp.content:
            raise Exception("could not log in (likely incorrect username or password)")
        resp = self.br.open('https://workstation.jamberry.com/ws/dashboard', allow_redirects=True)
        if '/login' in resp.url:
            raise Exception("login verification failed")
        else:
            id_regex = re.compile(r'\(ID# (\d+)\)')
            id_str = resp.soup.find(text=id_regex)
            self._consultant_id = id_regex.match(id_str).groups()[0]
            self._logged_in = True

    @property
    def logged_in(self):
        return self._logged_in

    def logout(self):
        self.br.get(self.urls['JAMBERRY_LOGOUT_URL'])
        self.br = Workstation.init_browser()
        self._logged_in = False
        self._consultant_id = None

    def downline_consultants(self) -> Iterable[Tuple[Consultant, ConsultantActivityRecord]]:
        data = self.fetch_team_activity_csv()
        tar = DictReader(data.decode(encoding='utf-8').splitlines())
        yield from (parse_team_activity_row(row) for row in tar)

    def customers(self) -> Iterable[Customer]:
        data = self.fetch_customer_volume_json()
        j = json.loads(data)
        yield from (customer_from_row(row) for row in j['rows'])

    def orders(self, start_date=None, end_date=None, include_details=False) -> Iterable[Order]:
        data = self.fetch_orders_api(start_date, end_date)
        order_generator = (parse_order_api(item) for item in data)

        if include_details:
            yield from (self.add_order_details(o) for o in order_generator)
        else:
            yield from order_generator

    def catalog_products(self) -> Iterable[Product]:
        for p in self.fetch_all_products():
            yield parse_product(p)

    def add_order_details(self, order: Order):
        detail_soup = self.fetch_order_detail(order.id)
        order.line_items = extract_line_items(detail_soup)
        order.shipping_address = extract_shipping_address(detail_soup)
        return order

    @requires_login
    def fetch_team_activity_csv(self, year=None, month=None, levels='9999'):
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        filter_data = OrderedDict(
            sort='-start',
            filter='level|between|1|{}'.format(levels),
            period=year * 100 + month,  # YYYYMM
            region='US',
            lang='en',
            start=0,
            trans='CompRank_AdvancedConsultant|Advanced Consultant,CompRank_Consultant|Consultant,CompRank_SeniorConsultant|Senior Consultant,CompRank_LeadConsultant|Lead Consultant,CompRank_TeamManager|Team Manager,CompRank_SeniorTeamManager|Senior Team Manager,CompRank_PremierConsultant|Premier Consultant,CompRank_SeniorLeadConsultant|Senior Lead Consultant,CompRank_Executive|Executive,CompRank_SeniorExecutive|Senior Executive,CompRank_LeadExecutive|Lead Executive,CompRank_EliteExecutive|Elite Executive,ProfessionalConsultant|Professional Consultant,Hobbyist|Hobbyist,FastStart|Fast Start,Active|Active,In Progress|In Progress,generation|GEN,level|DLL,contact|Contact,firstName|First,lastName|Last,email|Email,phone|Phone,address|Address,city|City,state|State,zip|ZIP,country|Country,conference|Attending Conference,start|Enrollment,status|Status,login|Last Login,type|Type,title|Title,pay|Pay Title,prv|RV,qv|QV,pcv|CV,trv|TQV,drv|DQV,active|Active Legs,sponsored|Recruits,svip|SVIPs,downline|Organization Total,tripPts|Trip,manager|Team Manager,sponsor|Sponsor,sponsorEmail|Sponsor Email'
        )
        resp = self.br.get(
            self.urls['JAMBERRY_API_TEAM_ACTIVITY_REPORT_URL'].format(self._consultant_id),
            params=filter_data
        )
        return resp.content

    @deprecated("use fetch_orders_api instead")
    @requires_login
    def fetch_orders(self):
        resp = self.br.open(self.urls['JAMBERRY_ORDERS_URL'])
        return resp.soup.find(id='ctl00_contentMain_dgAllOrders')

    @requires_login
    def fetch_orders_api(self, start_date='2014-01-01', end_date=None):
        date_format = '%Y-%m-%d'
        if end_date is None:
            end_date = datetime.now().strftime(date_format)
        if isinstance(start_date, datetime):
            start_date = start_date.strftime(date_format)
        if isinstance(end_date, datetime):
            end_date = end_date.strftime(date_format)
        more_pages = True
        current_page = 0
        while more_pages:
            resp = self.br.open(
                self.urls['JAMBERRY_ORDERS_API_URL'],
                params=dict(
                    userId=self._consultant_id,
                    startDate=start_date,
                    endDate=end_date,
                    page=current_page,
                    searchType='MINE_AND_SPONSORED_ORDERS',
                    tz='America/New_York',
                )
            )
            current = resp.json()
            current_page += 1
            more_pages = not current['orderHistoryPage']['last']
            yield from current['orderHistoryPage']['content']

    @requires_login
    def fetch_customer_angel_csv(self):
        resp = self.br.open(self.urls['JAMBERRY_CUSTOMER_ANGEL_CSV_URL'])
        return resp.content

    @requires_login
    def fetch_customer_volume_json(self):
        resp = self.br.open(self.urls['JAMBERRY_API_CUSTOMER_VOLUME_URL'].format(self._consultant_id))
        return resp.content

    @deprecated("use fetch_orders_api instead")
    @requires_login
    def fetch_archive_orders(self):
        resp = self.br.open(self.urls['JAMBERRY_ORDERS_ARCHIVE_URL'])
        return resp.soup.find(id='ctl00_main_dgAllOrders')

    @requires_login
    def fetch_order_detail(self, order_id):
        br = self.br
        order_url = f'https://workstation.jamberrynails.net/associate/orders/OrderDetails.aspx?id={order_id}'
        resp = br.open(order_url)
        return resp.soup

    @requires_login
    def create_tmp_search_cart_retail(self):
        self.br.open(self.urls['JAMBERRY_VIEW_CARTS_URL'])  # Shop
        self.br.open(self.urls['JAMBERRY_CREATE_NEW_RETAIL_CART_URL'])  # New Cart (retail)
        form_data = dict(
            cartType='2',
            label='tmpSearchRetail',
            id='',
            firstName='Sherlock',
            lastName='Holmes',
            address1='221B Baker St',
            address2='',
            locality='London',
            region='KY',
            postalCode='40741',
            country='US',
            phoneNumber='4045551212',
        )
        resp = self.br.post(self.urls['JAMBERRY_CREATE_NEW_RETAIL_CART_POST_URL'], data=form_data)
        self._cart_url = resp.url

    @requires_login
    def delete_tmp_search_cart_retail(self):
        delete_cart_post_url = self._cart_url.replace('cart/display', 'cart/RemoveCart')
        payload = {'CartType': 'Retail'}
        self.br.get(delete_cart_post_url, params=payload)
        self._cart_url = None

    def fetch_all_products(self, search_keys='aeiou*'):
        """By default, fetches and combines 5 autocomplete results, to effectively
           get a full catalog. You can provide any iterable to `search_keys`."""
        if self._cart_url is None:
            self.create_tmp_search_cart_retail()
        results = (self.fetch_autocomplete_json(search_key) for search_key in search_keys)
        product_lists = (result['products'] for result in results)
        products = {}
        for p in chain(*product_lists):
            if isinstance(p['sku'], list):
                sku = p['sku'][0]
            else:
                sku = p['sku']
            products[sku] = p
        yield from products.values()

    @requires_login
    def fetch_autocomplete_json(self, search_key):
        search_url = self._cart_url.replace('cart/display', 'search/products')
        defaults = (
            ('cartType', 'Retail'),
            ('catalogType', 'retail'),
            ('take', '9999'),  # there are less than 2,000 items in the catalog, so this gets all results
        )
        payload = dict(defaults + (('q', search_key),))
        resp = self.br.get(search_url, params=payload)
        json_result = json.loads(resp.content, encoding='ISO-8859-1')
        return json_result

    def read_config(self):
        from configparser import ConfigParser, Error
        parser = ConfigParser()
        config_path = 'jamberry.ini'
        found = parser.read(config_path)
        if not found:
            raise IOError('Supply username and password in `jamberry.ini`')
        self.username = parser.get('credentials', 'username')
        self.password = parser.get('credentials', 'password')