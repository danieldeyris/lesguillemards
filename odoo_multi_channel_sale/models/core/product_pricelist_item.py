# -*- coding: utf-8 -*-
from odoo import fields,models


class PricelistItem(models.Model):
	_inherit = 'product.pricelist.item'

	def write(self, vals):
		res = super(PricelistItem, self).write(vals)
		for record in self:
			channels = self.env["multi.channel.sale"].search(['|', ('pricelist_name', '=', self.pricelist_id.id), ('pricelist_regular', '=', self.pricelist_id.id)])
			for channel in channels:
				if record.applied_on == '0_product_variant':
					match_record = self.env['channel.template.mappings'].search([
						('template_name', '=', self.product_id.product_tmpl_id.id),
						('channel_id', '=', channel.id)])
					if match_record:
						match_record.write({'need_sync': 'yes'})
				elif record.applied_on == '1_product':
					match_record = self.env['channel.template.mappings'].search([
						('template_name', '=', self.product_tmpl_id.id),
						('channel_id', '=', channel.id)])
					if match_record:
						match_record.write({'need_sync': 'yes'})
				elif record.applied_on == '3_global':
					# TODO : a faire
					pass
				elif record.applied_on == '2_product_category':
					# TODO : a faire
					pass
		return res
