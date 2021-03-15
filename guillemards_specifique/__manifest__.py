# -*- coding: utf-8 -*-
{
    'name': "Phidias : specifique guillemards",

    'summary': """
        Phidias : specifique guillemards
        """,

    'description': """
        Phidias : specifique guillemards
    """,

    'author': "Phidias",
    'website': "http://www.phidias.fr",
    'category': 'Uncategorized',
    'version': '13.0.0.4',

    # any module necessary for this one to work correctly
    'depends': [
        'branch',
        'web',
        'odoo_multi_channel_sale',
        'woocommerce_odoo_connector',
    ],
    "data": [
        'views/partner.xml',
        'views/branch.xml',
        'views/report_templates.xml',
        'views/sale_order.xml',
        'views/multi_channel_sale.xml',
        'views/order_feed.xml',
        'views/pos_config.xml',
    ],
}
