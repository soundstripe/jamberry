import re
import locale

locale.setlocale(locale.LC_ALL, 'english_USA')


def currency_to_float(param):
    negative_paren = re.compile(r'\(\$?([0-9,]+\.[0-9][0-9])\)')  # parenthesized negative dollar amount
    negative_sign = re.compile(r'-\$?([0-9,]+\.[0-9][0-9])')
    positive = re.compile(r'\$?([0-9,]+\.[0-9][0-9])')
    for r in (negative_paren, positive):
        m = r.match(param)
        if m:
            return locale.atof(m.groups()[0])
    m = negative_sign.match(param)
    if m:
        return -locale.atof(m.groups()[0])
    raise ValueError()
