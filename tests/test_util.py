from decimal import Decimal
from src.jamberry.util import currency_to_decimal


def test_currency_to_decimal():
    result = currency_to_decimal('$4.00')
    assert result == Decimal('4.00')
    result = currency_to_decimal('$4.00 USD')
    assert result == Decimal('4.00')

    result = currency_to_decimal('($8.00)')
    assert result == Decimal('-8.00')
    result = currency_to_decimal('($8.00) USD')
    assert result == Decimal('-8.00')

    result = currency_to_decimal('$0.00')
    assert result == Decimal('0.00')
    result = currency_to_decimal('$0.00 USD')
    assert result == Decimal('0.00')

    result = currency_to_decimal('$12.63')
    assert result == Decimal('12.63')
    result = currency_to_decimal('$12.63 USD')
    assert result == Decimal('12.63')

    result = currency_to_decimal('$1,342.63 USD')
    assert result == Decimal('1342.63')
