import re
from decimal import Decimal


def currency_to_decimal(param):
    param = param.replace(',', '').strip()
    negative_paren = re.compile(r'\(\$?([0-9,]+\.[0-9][0-9])\)')  # parenthesized negative dollar amount
    negative_sign = re.compile(r'-\$?([0-9,]+\.[0-9][0-9])')
    positive = re.compile(r'\$?([0-9,]+\.[0-9][0-9])')

    m = negative_paren.match(param)
    if m: return -Decimal(m.groups()[0])

    m = negative_sign.match(param)
    if m: return -Decimal(m.groups()[0])

    m = positive.match(param)
    if m: return Decimal(m.groups()[0])

    raise ValueError()
