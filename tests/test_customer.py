from src.jamberry.customer import Customer


def test_address_property():
    c = Customer()
    c.name = 'Ima Customer'
    c.address_line_1 = '123 Nowhere St.'
    c.address_city = 'Somewhere'
    c.address_state = 'NV'
    c.address_zip = '12345'
    assert c.address == 'Ima Customer\n123 Nowhere St.\nSomewhere, NV 12345'
    c.address_line_2 = 'Suite 1'
    assert c.address == 'Ima Customer\n123 Nowhere St.\nSuite 1\nSomewhere, NV 12345'

