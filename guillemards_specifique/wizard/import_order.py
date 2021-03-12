# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
##########H#########Y#########P#########N#########O#########S##################


from odoo import models


class ImportWoocommerceOrders(models.TransientModel):
    _inherit = 'import.woocommerce.orders'

    def _get_order_by_id(self, woocommerce, channel, order):
        res = super(ImportWoocommerceOrders, self)._get_order_by_id(woocommerce, channel, order)
        res["branch_id"] = channel.branch_id.id
        return res
