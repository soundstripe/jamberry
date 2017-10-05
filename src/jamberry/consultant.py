class Consultant:
    __slots__ = (
        'id',
        'downline_level',
        'first_name',
        'last_name',
        'email',
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


class ConsultantActivityRecord:
    __slots__ = (
        'timestamp',
        'activity_report_date',
        'generation',
        'attending_conference',
        'status',
        'last_login',
        'title',
        'pay_title',
        'rv',
        'qv',
        'cv',
        'tqv',
        'dqv',
        'active_legs',
        'new_recruits',
        'style_vips',
        'total_downline',
        'trip_points',
        'team_manager',
        'sponsor_name',
        'sponsor_email',
        'highest_title',
    )
