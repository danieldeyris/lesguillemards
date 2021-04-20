# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _set_delivery_packaging(self):
        self.ensure_one()
        delivery_type = 'none' if self.carrier_id.delivery_type == 'fixed' else self.carrier_id.delivery_type

        packaging = self.env['product.packaging'].search([('package_carrier_type', '=', delivery_type)])
        if len(packaging) <= 1:
            delivery_package = self.env["choose.delivery.package"]
            delivery_package.picking_id = self.id
            delivery_package.delivery_packaging_id = packaging.id
            return delivery_package.put_in_pack()
        else:
            return super(StockPicking, self)._set_delivery_packaging()

    def action_done(self):
        self.ensure_one()
        if self.carrier_id:
            if self.carrier_id.integration_level == 'rate_and_ship' and self.picking_type_code != 'incoming':
                move_line_ids = self.move_line_ids.filtered(lambda ml:
                                                            float_compare(ml.qty_done, 0.0,
                                                                          precision_rounding=ml.product_uom_id.rounding) > 0
                                                            and not ml.result_package_id
                                                            )
                #package_count = len(self.package_ids)
                if move_line_ids:
                    self.put_in_pack()
        return super(StockPicking, self).action_done()


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    shipping_weight = fields.Float(string='Shipping Weight', help="Total weight of the package.", compute='_compute_weight_shipping',store=True)

    @api.depends('weight')
    def _compute_weight_shipping(self):
        for package in self:
            if package.weight:
                package.shipping_weight = package.weight
            else:
                package.shipping_weight = 0.25
            if package.weight < 0.1:
                package.shipping_weight = 0.1
