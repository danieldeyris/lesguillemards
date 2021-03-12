# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2020-Present Phidias (https://www.phidias.fr)
#    See LICENSE file for full copyright and licensing details.
##################################################################################
from odoo import models


class WkFeed(models.Model):
	_inherit = 'wk.feed'
	_description = 'Feed'

	def get_partner_shipping_vals(self,partner_id,channel_id):

		vals = super(WkFeed, self).get_partner_shipping_vals(partner_id,channel_id)
		if self.shipping_code_relaypoint:
			vals["code_relaypoint"] = self.shipping_code_relaypoint
			vals["name"] = self.shipping_name
		return vals
