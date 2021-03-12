from odoo import api,fields,models
from odoo.addons.odoo_multi_channel_sale.tools import extract_list as EL
from logging import getLogger

_logger = getLogger(__name__)


class ProductImages(models.Model):
	_name        = 'product.images'
	_description = 'product Images'
	_order = 'product_tmpl_id, product_id, sequence asc, id'

	product_tmpl_id = fields.Many2one('product.template', 'Product Template')
	product_id = fields.Many2one('product.product', 'Product')
	image_1920 = fields.Image("Image", max_width=1920, max_height=1920)
	image_128 = fields.Image("Image 128", related="image_1920", max_width=128, max_height=128, store=True)
	image_preview = fields.Image("Image preview", related="image_1920", max_width=128, max_height=128)
	sequence = fields.Integer('Sequence', default=0)
	web_image_id = fields.Integer("Id Site WEB")

	def write(self, vals):
		res = super(ProductImages, self).write(vals)
		for record in self:
			channels = self.env["multi.channel.sale"].search([])
			for channel in channels:
				if record.product_tmpl_id:
					match_record = self.env['channel.template.mappings'].search([
						('template_name', '=', self.product_tmpl_id.id),
						('channel_id', '=', channel.id)])
					if match_record:
						match_record.write({'need_sync': 'yes'})
				elif record.product_id:
					match_record = self.env['channel.template.mappings'].search([
						('template_name', '=', self.product_id.id),
						('channel_id', '=', channel.id)])
					if match_record:
						match_record.write({'need_sync': 'yes'})
		return res

	@api.model
	def create(self, vals):
		res = super(ProductImages, self).create(vals)
		for record in self:
			channels = self.env["multi.channel.sale"].search([])
			for channel in channels:
				if record.product_tmpl_id:
					match_record = self.env['channel.template.mappings'].search([
						('template_name', '=', self.product_tmpl_id.id),
						('channel_id', '=', channel.id)])
					if match_record:
						match_record.write({'need_sync': 'yes'})
				elif record.product_id:
					match_record = self.env['channel.template.mappings'].search([
						('template_name', '=', self.product_id.id),
						('channel_id', '=', channel.id)])
					if match_record:
						match_record.write({'need_sync': 'yes'})
		return res
