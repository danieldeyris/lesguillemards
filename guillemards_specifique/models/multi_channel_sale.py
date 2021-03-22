
from odoo import fields, models, api, _


class MultiChannelSale(models.Model):
	_inherit = 'multi.channel.sale'

	branch_id = fields.Many2one('res.branch', string="Branch")
	