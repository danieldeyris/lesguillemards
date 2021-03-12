
from odoo import api,fields,models


class WkFeed(models.Model):
	_inherit        = 'wk.feed'

	def get_partner_contact_vals(self,partner_id,channel_id):
		vals = super(WkFeed, self).get_partner_contact_vals(partner_id,channel_id)
		vals["branch_id"] = channel_id.branch_id.id
		return vals