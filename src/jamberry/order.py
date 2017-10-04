class Order:
    __slots__ = (
        'id',
        'customer_name',
        'shipping_name',
        'order_date',
        'order_details_url',
        'subtotal',
        'shipping_fee',
        'tax',
        'status',
        'retail_bonus',
        'order_type',
        'customer_url',
        'customer_id',
        'customer_contact',
        'total',
        'qv',
        'hostess',
        'party',
        'ship_date',
        'line_items',
        'shipping_address',
    )

class OrderLineItem:
    __slots__ = (
        'sku',
        'name',
        'price',
        'quantity',
        'total',
    )
