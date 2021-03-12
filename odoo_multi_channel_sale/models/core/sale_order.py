# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
	_inherit = 'sale.order'

	channel_mapping_ids = fields.One2many(
		string='Mappings',
		comodel_name='channel.order.mappings',
		inverse_name='order_name',
		copy=False
	)

	payment_transaction_count = fields.Integer(
		string="Number of payment transactions",
		compute='_compute_payment_transaction_count_new')

	web_store_id = fields.Char("Numéro de commande WEB", compute="_compute_store_id")

	def _compute_store_id(self):
		for order in self:
			mapping = self.env["channel.order.mappings"].search([('order_name', '=', order.id)])
			if mapping:
				order.web_store_id = mapping.store_order_id
			else:
				order.web_store_id = False

	def action_cancel(self):
		self.ensure_one()
		self.wk_pre_cancel()
		result = super(SaleOrder, self).action_cancel()
		self.wk_post_cancel(result)
		return result

	def wk_pre_cancel(self):
		for order_id in self:
			mapping_ids = order_id.channel_mapping_ids
			if mapping_ids:
				channel_id = mapping_ids[0].channel_id
				if hasattr(channel_id, '%s_pre_cancel_order' % channel_id.channel) and channel_id.sync_cancel:
					getattr(channel_id, '%s_pre_cancel_order' % channel_id.channel)(self, mapping_ids)

	def wk_post_cancel(self,result):
		for order_id in self:
			mapping_ids = order_id.channel_mapping_ids
			if mapping_ids:
				channel_id = mapping_ids[0].channel_id
				if hasattr(channel_id, '%s_post_cancel_order' % channel_id.channel) and channel_id.sync_cancel:
					getattr(channel_id, '%s_post_cancel_order' % channel_id.channel)(self, mapping_ids, result)

	def _compute_payment_transaction_count_new(self):
		for order in self:
			transaction_data = self.env['payment.transaction'].search([('sale_order_ids', 'in', order.ids)],
																	  order="id desc", limit=1)
			order.payment_transaction_count = len(transaction_data)
			payment_method_name = False
			payment_status = False
			if transaction_data:
				payment_method_name = transaction_data.acquirer_id.name
				state = dict(transaction_data.fields_get(['state'])['state']['selection'])[transaction_data.state]
				payment_status = state

			order.payment_method_name = payment_method_name
			order.payment_status = payment_status

	def action_view_transaction(self):
		action = {
			'type': 'ir.actions.act_window',
			'name': 'Payment Transactions',
			'res_model': 'payment.transaction',
		}
		if self.payment_transaction_count == 1:
			action.update({
				'res_id': self.env['payment.transaction'].search([('sale_order_ids', 'in', self.ids)], order="id desc",
																 limit=1).id,
				'view_mode': 'form',
			})
		else:
			action.update({
				'view_mode': 'tree,form',
				'domain': [('sale_order_ids', 'in', self.ids)],
			})
		return action
