
from odoo import api, fields, models

from odoo.addons.odoo_multi_channel_sale.models.feeds.order_feed import OrderFields

class OrderFeed(models.Model):
	_inherit        = 'order.feed'

	branch_id = fields.Char('Branch')

	def _create_feed(self, order_data):
		channel_id = order_data.get('channel_id')
		channel = self.env["multi.channel.sale"].browse(channel_id)
		order_data["branch_id"] = channel.branch_id.id
		feed = super(OrderFeed, self)._create_feed(order_data)
		return feed

	@api.model
	def get_order_fields(self):
		OrderFields.append('branch_id')
		return super(OrderFeed, self).get_order_fields()
