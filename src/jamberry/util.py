import re


def currency_to_float(param):
    negative = re.compile(r'\(\$?([0-9]+\.[0-9][0-9])\)')  # parenthesized negative dollar amount
    positive = re.compile(r'\$?([0-9]+\.[0-9][0-9])')
    for r in (negative, positive):
        m = r.match(param)
        if m:
            return float(m.groups()[0])
    raise ValueError()