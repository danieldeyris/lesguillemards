# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        for saleOrder in self:
            if saleOrder.partner_id.branch_id:
                saleOrder.branch_id = saleOrder.partner_id.branch_id
            else:
                saleOrder.branch_id = self.env.user.branch_id
