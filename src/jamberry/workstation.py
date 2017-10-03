from abc import abstractmethod, ABC
from csv import DictReader
from datetime import datetime, timedelta
from functools import wraps
from io import StringIO
from urllib.parse import urljoin
import re

import mechanicalsoup

from .util import currency_to_float

JAMBERRY_WORKSTATION_URL = 'https://workstation.jamberry.com'
JAMBERRY_LOGIN_URL = urljoin(JAMBERRY_WORKSTATION_URL, '')
JAMBERRY_LOGOUT_URL = urljoin(JAMBERRY_WORKSTATION_URL, 'login/logout.aspx')
JAMBERRY_TAR_URL = urljoin(JAMBERRY_WORKSTATION_URL, 'associate/commissions/Activity.aspx')
JAMBERRY_ORDERS_URL = urljoin(JAMBERRY_WORKSTATION_URL, 'associate/orders/')
JAMBERRY_ORDERS_ARCHIVE_URL = urljoin(JAMBERRY_WORKSTATION_URL, 'associate/orders/Archive.aspx')


def field_data(soup, name):
    return name, soup.find('input', attrs=dict(name=name)).get('value')


def requires_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        ws = args[0]
        ws.login()
        return f(*args, **kwargs)

    return wrapper


class Workstation(ABC):
    def __init__(self, *args, **kwargs):
        self.br = Workstation.init_browser()

    @classmethod
    def init_browser(cls):
        br = mechanicalsoup.StatefulBrowser()
        br.addheaders = [('User-agent',
                          'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36')]
        return br

    def orders(self):
        raw_orders = self.fetch_orders()
        yield from (order for order in self.parse_orders(raw_orders))

    @abstractmethod
    def fetch_orders(self):
        return ''


class JamberryWorkstation(Workstation):
    def __init__(self, username, password, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username = username
        self.password = password
        self._cart_url = None
        self._logged_in = False

    def __del__(self):
        if self._cart_url is not None:
            self.delete_tmp_search_cart_retail()

    def login(self):
        if self.logged_in:
            return
        br = self.br
        br.open(JAMBERRY_LOGIN_URL)
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
        if b'Quick Links' not in resp.content:
            raise Exception("could not log in (likely incorrect username or password)")
        resp = self.br.open('https://workstation.jamberry.com/ws/dashboard', allow_redirects=True)
        if '/login' in resp.url:
            raise Exception("login verification failed")
        else:
            self._logged_in = True

    @property
    def logged_in(self):
        return self._logged_in

    def logout(self):
        self.br.get(JAMBERRY_LOGOUT_URL)
        self.br = Workstation.init_browser()
        self._logged_in = False

    @requires_login
    def fetch_tar(self, year=None, month=None, levels='9999', version=1):
        if version != 1:
            raise NotImplemented
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        # step 1 - get form
        resp = self.br.open(JAMBERRY_TAR_URL)
        s = resp.soup.form
        # step 2 - set ddLevels (requires a post)
        d = dict((
            field_data(s, '__VIEWSTATE'),
            field_data(s, '__VIEWSTATEGENERATOR'),
            field_data(s, '__EVENTVALIDATION'),
            ('__EVENTTARGET', 'ctl00$contentMain$ddLevels'),
            ('ctl00$contentMain$ddMonth', str(year * 100 + month)),
            ('ctl00$contentMain$ddLevels', int(levels)),
        ))
        resp = self.br.post(JAMBERRY_TAR_URL, data=d)
        s = resp.soup.form
        # step 3 - retrieve tar csv response
        d = dict((
            field_data(s, '__VIEWSTATE'),
            field_data(s, '__VIEWSTATEGENERATOR'),
            field_data(s, '__EVENTVALIDATION'),
            ('ctl00$contentMain$ddMonth', str(year * 100 + month)),
            ('ctl00$contentMain$ddLevels', 9999),
            ('ctl00$contentMain$rgActivity$ctl00$ctl02$ctl00$ExportToCsvButton', ''),
        ))
        resp = self.br.post(JAMBERRY_TAR_URL, data=d)
        return resp.content

    @requires_login
    def fetch_orders(self):
        resp = self.br.open(JAMBERRY_ORDERS_URL)
        return resp.soup

    def parse_tar(self):
        tar_data = self.fetch_tar()
        tar_file = StringIO(tar_data.decode(encoding='utf-8'))
        results = []
        tar = DictReader(tar_file)
        for row in tar:
            consultant_dict = dict(
                id=row['User Id'],
                downline_level=int(row['Downline Level']),
                first_name=row['First Name'],
                last_name=row['Last Name'],
                sponsor_name=row['Sponsor'],
                sponsor_email=row['Sponsor Email'],
                consultant_type=row['Type'],
                phone=row['Phone'],
                address_line1=row['Address'],
                address_city=row['City'],
                address_state=row['State'],
                address_zip=row['ZIP'],
                address_country=row['Country'],
                team_manager=row['Upline Team Manager'],
                start_date=datetime.strptime(row['Start Date'], '%b %d, %Y') + timedelta(hours=6),
            )
            if "In Progress" in row['Status']:
                status = False
            else:
                status = True
            activity_report_line = dict(
                status=status,
                active_legs=int(row['Active Legs']),
                highest_leg_rank_int=int(row['Highest Leg Rank'][:2]),
                highest_leg_rank_name=row['Highest Leg Rank'][5:],
                pay_rank_int=row['Pay Rank'][:2],
                pay_rank_name=row['Pay Rank'][5:],
                career_title_int=row['Recognition Title'][:2],
                career_title_name=row['Recognition Title'][5:],
                prv=currency_to_float(row['PRV']),
                cv=currency_to_float(row['CV']),
                trv=currency_to_float(row['TRV']),
                drv=currency_to_float(row['DRV']),
                sponsored_this_month=int(row['# Sponsored This Month']),
                downline_count=int(row['In Downline']),
                last_login=None if row['Last Login'].strip() == '' else datetime.strptime(row['Last Login'], '%b %d, %Y')
            )
            results.append((consultant_dict, activity_report_line))
        return results

    @requires_login
    def fetch_archive_orders(self):
        resp = self.br.open(JAMBERRY_ORDERS_ARCHIVE_URL)
        return resp.soup

    def parse_archive_orders(self):
        bs = self.fetch_archive_orders()
        orders = []
        order_table = bs.find(id='ctl00_main_dgAllOrders')
        for row in order_table.findAll('tr')[1:]:
            cols = row.findAll('td')
            order_dict = dict(
                id=cols[0].a.text,
                customer_name=cols[1].a.text,
                shipping_name=cols[2].a.text,
                order_date=datetime.strptime(cols[3].a.text, '%m/%d/%Y') + timedelta(hours=6),
                order_details_url=cols[0].a['href'],
                subtotal=float(cols[4].text.strip().strip('$')),
                shipping_fee=float(cols[5].text.strip().strip('$')),
                tax=float(cols[6].text.strip().strip('$')),
                # 7: total
                # 8: Type (Party, etc)
                status=cols[9].text.strip(),
                retail_bonus=float(cols[10].text.strip().strip('$')),
            )
            try:
                order_dict['details'] = self.parse_order_details(order_dict['id'])
            except Exception as e:
                pass
            orders.append(order_dict)
        return orders

    def parsed_orders(self):
        bs = self.fetch_orders()
        order_table = bs.find(id='ctl00_contentMain_dgAllOrders')
        for row in order_table.findAll('tr')[1:]:
            customer_name = row.find(text="Placed By:").next.strip()
            customer_url = ''
            customer_id = ''
            customer_contact = ''
            if customer_name == u'':
                customer_name = row.find(text="Placed By:").next.next.next.strip()
                customer_url = 'https://workstation.jamberry.com' + row.findAll(['a'])[2]['href']
                customer_id = customer_url.split('/')[-1]
                try:
                    customer_contact = row.find(text="Contact: ").next.strip()
                except AttributeError:
                    customer_contact = ''
            order_dict = dict(
                id=row.td.a.text,
                order_type=row.find(text="Type:").next.strip(),
                order_date=datetime.strptime(row.td.nextSibling.a.text, '%b %d, %Y') + timedelta(hours=6),
                order_details_url='https://workstation.jamberry.com/associate/orders/' + row.td.a['href'],
                customer_name=customer_name,
                customer_url=customer_url,
                customer_id=customer_id,
                customer_contact=customer_contact,
                shipping_name=row.find(text="Shipped To:").next.strip(),
                subtotal=float(row.find(text="Subtotal:").next.strip().strip('$').strip(' USD')),
                shipping_fee=float(row.find(text="Shipping:").next.strip().strip('$').strip(' USD')),
                tax=float(row.find(text="Tax:").next.strip().strip('$').strip(' USD')),
                total=float(row.find(text="Total:").next.strip().strip('$').strip(' USD')),
                prv=float(row.find(text="QV:").next.strip().strip('$').strip(' USD')),
                status=row.find(text="Status: ").next.strip(),
            )
            row_find = row.find(text='Hostess: ')
            if row_find:
                order_dict["hostess"] = row_find.next.strip()
            row_find = row.find(text='Party: ')
            if row_find:
                order_dict["party"] = row_find.next.strip()
            row_find = row.find(text='Shipped On:')
            if row_find:
                order_dict["ship_date"] = row_find.next.strip()
            yield order_dict

    def parsed_orders_with_details(self):
        for order in self.parsed_orders():
            try:
                order['order_detail'] = self.parse_order_details(order['id'])
            except Exception as e:
                pass
            yield order

    def __del__(self):
        if self.logged_in:
            self.logout()

    def parse_order_details(self, id=None):
        if not id:
            return None
        bs = self.fetch_order_detail(id)
        line_items_table = bs.find(id='ctl00_main_dgMain')
        line_items_rows = line_items_table.findAll('tr')[1:]  # skip header row
        lines = []
        for row in line_items_rows:
            cells = row.findAll('td')
            detail = dict(
                sku=cells[0].text.strip(),
                item_name=cells[1].text.strip(),
                price=cells[2].text.strip(),
                quantity=int(cells[3].text.strip()),
                total=currency_to_float(cells[4].text.strip().split('\n')[0]),
            )
            lines.append(detail)
        address = '\n'.join(list(bs.find(text=re.compile('Address')).findNext('strong').stripped_strings))
        return {'lines': lines, 'address': address}

    @requires_login
    def fetch_order_detail(self, id):
        br = self.br
        order_url = 'https://workstation.jamberrynails.net/associate/orders/OrderDetails.aspx?id=%s' % (id)
        tries = 0
        while 1:
            try:
                resp = br.open(order_url)
                break
            except Exception as e:
                tries += 1
                print(e)
                if tries == 3:
                    raise e
        return resp.soup

    @requires_login
    def create_tmp_search_cart_retail(self):
        self.br.open('https://workstation.jamberry.com/us/en/wscart')  # Shop
        self.br.open('https://workstation.jamberry.com/us/en/wscart/cart/new?cartType=2')  # New Cart (retail)
        new_cart_post_url = 'https://workstation.jamberry.com/us/en/wscart/cart/saveCart'
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
        resp = self.br.post(new_cart_post_url, data=form_data)
        self._cart_url = resp.url

    @requires_login
    def delete_tmp_search_cart_retail(self):
        delete_cart_post_url = self._cart_url.replace('cart/display', 'cart/RemoveCart')
        payload = {'CartType': 'Retail'}
        self.br.get(delete_cart_post_url, params=payload)
        self._cart_url = None

    @requires_login
    def fetch_autocomplete_json(self, search_keys="aeiou"):
        if self._cart_url is None:
            self.create_tmp_search_cart_retail()
        search_url = self._cart_url.replace('cart/display', 'search/products')
        defaults = (
            ('cartType', 'Retail'),
            ('catalogType', 'retail'),
            ('take', '9999'),
        )
        json_cache = {}
        for k in search_keys:
            payload = dict(defaults + (('q', k),))
            resp = self.br.get(search_url, params=payload)
            json_cache[k] = resp.content
        return json_cache
