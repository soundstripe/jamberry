class Customer:
    """This class represents a customer, and is primarily useful for storing contact information. The workstation
    also provides information such as total sales to the customer and the customer's original consultant."""
    __slots__ = (
        'id',
        'name',
        'address_line_1',
        'address_line_2',
        'address_city',
        'address_state',
        'address_zip',
        'address_country',
        'type',
        'first_purchase_date',
        'last_purchase_date',
        'sponsor_rv',
        'sponsor_qv',
        'other_rv',
        'other_qv',
        'email',
        'phone',
        'birthdate',
        'original_consultant',
    )

    @property
    def address(self):
        """Simple address formatting for mailing"""
        street = self.address_line_1
        if self.address_line_2:
            street = f'{street}\n{self.address_line_2}'
        return f'{street}\n' \
               f'{self.address_city}, {self.address_state} {self.address_zip}'
