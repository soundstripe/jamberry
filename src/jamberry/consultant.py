class Consultant(object):
    __slots__ = (
        'id',
        'downline_level',
        'first_name',
        'last_name',
        'sponsor_name',
        'sponsor_email',
        'consultant_type',
        'phone',
        'address_line1',
        'address_city',
        'address_state',
        'address_zip',
        'address_country',
        'team_manager',
        'start_date',
    )

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def address(self):
        return f'{self.address_line1}\n{self.address_city}, {self.address_state} {self.address_zip}'
