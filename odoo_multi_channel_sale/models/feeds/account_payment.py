import json
import datetime

from odoo import models, fields, api
from odoo.tools import date_utils


class AccountPayment(models.Model):
	_inherit = 'account.payment'

	def create_payment(self, order, journal):

		acquirer_id = self.env['payment.acquirer'].get_or_create(journal)

		# Create transaction
		vals = {
			'acquirer_id': acquirer_id.id,
			'amount': order.amount_total,
			'currency_id': order.currency_id.id,
			'partner_id': order.partner_id.id,
			'sale_order_ids': [(6, 0, order.ids)],
			'type': order._get_payment_type(),
			'date': order.date_order,
		}

		transaction = self.env['payment.transaction'].create(vals)

		if not acquirer_id.wait_manuel_confirmation:
			transaction._set_transaction_done()
			transaction.date = order.date_order
			transaction._post_process_after_done()
		else:
			transaction.write({'state': 'pending'})


class AccountJournal(models.Model):
	_inherit = 'account.journal'

	@api.model
	def get_or_create(self, payment_method):
		journal_id = False
		if payment_method:
			journal_id = self.env['account.journal'].search([('code', '=', payment_method)])
			if not journal_id:
				res = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
				credit_account_id = res.default_credit_account_id.id
				debit_account_id = res.default_debit_account_id.id
				journal = {
					'name': payment_method,
					'code': payment_method,
					'type': 'bank',
					'default_credit_account_id': credit_account_id,
					'default_debit_account_id': debit_account_id,
				}
				journal_id = self.env['account.journal'].create(journal)

		return journal_id


class PaymentAcquirer(models.Model):
	_inherit = 'payment.acquirer'

	wait_manuel_confirmation = fields.Boolean("Wait manual confirmation", defalut=False)
	external_code = fields.Char("Code Externe")

	@api.model
	def get_or_create(self, name):
		acquirer_id = False
		if name:
			acquirer_id = self.env['payment.acquirer'].search([('name', '=', name)], limit=1)
			if not acquirer_id:
				journal_id = self.env['account.journal'].get_or_create(name)
				vals = {
					'name': name,
					'provider': 'manual',
					'journal_id': journal_id.id,
					'state': 'test',
					'external_code': name,
					'view_template_id': self.env['ir.ui.view'].search([('type', '=', 'qweb')], limit=1).id}
				acquirer_id = self.env['payment.acquirer'].create(vals)
		return acquirer_id


class PaymentTransaction(models.Model):
	_inherit = 'payment.transaction'

	def action_confirm(self):
		if self.state == 'pending':
			self._set_transaction_done()
			self._post_process_after_done()

	def _post_process_after_done(self):
		res = super(PaymentTransaction, self)._post_process_after_done()
		for transaction in self:
			for order in transaction.sale_order_ids:
				if order.state == 'waiting_payment':
					order.action_confirm()
		return res

	def _prepare_account_payment_vals(self):
		res = super(PaymentTransaction, self)._prepare_account_payment_vals()
		res['payment_date'] = self.date
		return res
