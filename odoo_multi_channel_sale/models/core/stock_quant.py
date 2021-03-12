# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero


class StockQuant(models.Model):
	_inherit = 'stock.quant'

	def write(self, vals):
		res = super(StockQuant, self).write(vals)
		for record in self:
			channels = self.env["multi.channel.sale"].search([])
			for channel in channels:
				match_record = self.env['channel.template.mappings'].search([
					('template_name', '=', record.product_tmpl_id.id),
					('channel_id', '=', channel.id)])
				if match_record:
					match_record.write({'need_sync': 'yes'})
		return res
