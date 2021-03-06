# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import api,fields,models


class MultiChannelSkeleton(models.Model):
	_name        = 'multi.channel.skeleton'
	_description = 'Multi Channel Skeleton'

	def _get_journal_code(self, string, sep=' '):
		"""
		Takes payment method as argumnet and generates a jurnal code.
		"""
		tl = []
		for t in string.split(sep):
			tl.append(t.title()[0])
		code = ''.join(tl)
		code = code[0:3]
		is_exist = self.env['account.journal'].search([('code', '=', code)])
		if is_exist:
			for i in range(99):
				is_exist = self.env['account.journal'].search(
					[('code', '=', code + str(i))])
				if not is_exist:
					return code + str(i)[-5:]
		return code

	def _get_journal_name(self, string):
		is_exist = self.env['account.journal'].search([('name', '=', string)])
		if is_exist:
			for i in range(99):
				is_exist = self.env['account.journal'].search(
					[('name', '=', string + str(i))])
				if not is_exist:
					return string + str(i)
		return string

	@api.model
	def CreatePaymentMethod(self, ChannelID, PaymentMethod):
		"""
		Takes PaymentMethod as argument and returns Journal ID
		"""
		journal_id = False
		status_message = ''
		if PaymentMethod:
			journal_id = 0
			MapObj = self.env['channel.account.journal.mappings']
			exists = MapObj.search(
				[('store_journal_name', '=', PaymentMethod)])
			if not exists:
				res = self.env['account.journal'].search(
					[('type', '=', 'bank')], limit=1)
				credit_account_id = res.default_credit_account_id.id
				debit_account_id = res.default_debit_account_id.id
				journal = {
					'name': self._get_journal_name(PaymentMethod),
					'code': self._get_journal_code(PaymentMethod),
					'type': 'bank',
					'default_credit_account_id': credit_account_id,
					'default_debit_account_id': debit_account_id,
				}
				journal_obj = self.env['account.journal'].create(journal)
				journal_id = journal_obj.id
				if journal_obj:
					MapVals = {
						'name': journal_obj.name,
						'store_journal_name': PaymentMethod,
						'journal_code': journal_obj.code,
						'odoo_journal': journal_id,
						'odoo_journal_id': journal_id,
						'channel_id': ChannelID.id,
						'ecom_store': ChannelID.channel}
					MapObj.create(MapVals)
			else:
				journal_id = exists[0].odoo_journal_id
		return {
			'journal_id': journal_id,
			'status_message': status_message
		}

	@api.model
	def _ConfirmOdooOrder(self, order_obj, **kwargs):
		""" Confirms Odoo Order from E-Commerce
		@param order_id: Odoo/ERP Sale Order ID
		@return: a dictionary of True or False based on Transaction Result with status_message"""
		context = self._context or {}
		status = True
		status_message = ""
		try:
			order_obj.action_confirm()
			if kwargs.get('confirmation_date'):
				order_obj.write({'date_order':kwargs.get('confirmation_date')})
			status_message += "Order==> Confirmed. "
		except Exception as e:
			status_message += "Error in Confirming Order on Odoo: %s<br/>" % str(
				e)
			status = False
		finally:
			return {
				'status': status,
				'status_message': status_message
			}

	def set_order_shipped(self, order_id, **kwargs):
		"""Cancel the order in Odoo via requests from XML-RPC
		@param order_id: Odoo Order ID
		@param context: Mandatory Dictionary with key 'ecommerce' to identify the request from E-Commerce
		@return:  A dictionary of status and status message of transaction"""
		status = True
		context = dict(self._context or {})
		status_message = ""
		backOrderModel = self.env['stock.backorder.confirmation']
		try:
			sale = self.env['sale.order'].browse(order_id)
			if sale.state == 'draft':
				res = self._ConfirmOdooOrder(sale, **kwargs)
				status_message += res['status_message']
			for picking in sale.picking_ids:
			   backorder = False

			   if picking.state == 'draft':
				   picking.action_confirm()
			   if picking.state != 'assigned':
				   picking.action_assign()


			for picking in sale.picking_ids.filtered(
									lambda pickingObj: pickingObj.picking_type_code == 'outgoing' and pickingObj.state != 'done'):
				backorder = False
				# picking.force_assign()
				context = dict(self._context or {})

				context['active_id'] = picking.id
				context['picking_id'] = picking.id
				for move in picking.move_lines:
					if move.move_line_ids:
						for move_line in move.move_line_ids:
								move_line.qty_done = move_line.product_uom_qty
					else:
						move.quantity_done = move.product_uom_qty
				if picking._check_backorder():
					backorder=True
					continue
				if backorder:
					backorder_obj = self.env['stock.backorder.confirmation'].create({'pick_ids': [(4, picking.id)]})
					backorder_obj.with_context(context).process_cancel_backorder()
				else:
					picking.with_context(context).action_done()
				status_message += "Order==> Shipped. "
		except Exception as e:
			status = False
			status_message = "<br/> Error in Delivering Order: %s <br/>" % str(
					e)
		finally:
			return {
					'status_message': status_message,
					'status': status
			}

	@api.model
	def create_order_invoice(self, order_obj):
		"""Creates Order Invoice by request from Store.
		@param order_id: Odoo Order ID
		@return: a dictionary containig Odoo Invoice IDs and Status with Status Message
		"""
		invoice_id = False
		status = True
		status_message = "Invoice==> Created. "
		try:
			if not order_obj.invoice_ids:
				invoice_id = order_obj._create_invoices()
			else:
				status = False
				status_message = "<br/>Already Created"
		except Exception as e:
			status = False
			status_message = "<br/>Error in creating Invoice: %s <br/>" % str(e)
		finally:
			return {
				'status': status,
				'status_message': status_message,
				'invoice_id': invoice_id and invoice_id[0]
			}

	@api.model
	def SetOrderPaid(self, payment_data):
		"""Make the order Paid in Odoo using store payment data
		@param payment_data: A standard dictionary consisting of 'order_id', 'journal_id', 'amount'
		@param context: A Dictionary with key 'ecommerce' to identify the request from E-Commerce
		@return:  A dictionary of status and status message of transaction"""

		status = True
		status_message = ""

		journal_id = payment_data.get('journal_id', False)
		if journal_id:
			journal = self.env['account.journal'].browse(journal_id)
			order = self.env['sale.order'].browse(payment_data['order_id'])
			if journal and order:
				self.env['account.payment'].create_payment(order, journal.name)

		return {
			'status_message': status_message,
			'status': status
		}

	@api.model
	def get_default_payment_method(self, journal_id):
		""" @params journal_id: Journal Id for making payment
		@params context : Must have key 'ecommerce' and then return payment payment method based on Odoo Bridge used else return the default payment method for Journal
		@return: Payment method ID(integer)"""
		payment_method_ids = self.env['account.journal'].browse(
			journal_id)._default_inbound_payment_methods()
		if payment_method_ids:
			return payment_method_ids[0].id
		return False

	@api.model
	def _cancel_order(self, order_id, channel_id):
		status_message = ''
		status = True
		try:
			order_id.action_cancel()
			status_message += '<br/> Order ==> Cancelled. '
		except Exception as e:
			status_message += '%s' % (e)
			Status = False
		return dict(
			status_message=status_message,
			status=status,
		)

	@api.model
	def _ConfirmOrderAndCreateInvoice(self, OrderObj, ChannelID, PaymentMethod,
	OrderState=False, CreateInvoice=False, InvoiceState=False, ShipOrder=False,**kwargs):
		"""
		Confirm order in odoo..
		@arguments order object , channel object ,order state, invoice state, payment method
		"""
		status = True
		context = dict(self._context or {})
		status_message = ""
		draft_invoice_ids = []
		invoice_id = False
		sale_obj = self.env['sale.order']

		if OrderState and OrderState in ['sale', 'done']:
			res = self._ConfirmOdooOrder(OrderObj,**kwargs)
			status_message += res['status_message']
			status = res['status']
			if PaymentMethod and CreateInvoice:
				res_payment = self.CreatePaymentMethod(
					ChannelID, PaymentMethod)
				data = {
					'order_id': OrderObj.id,
					'journal_id': res_payment['journal_id'],
					'channel_id': ChannelID,
					'order_state': OrderState,
					'invoice_state': InvoiceState,
					'date_invoice':kwargs.get('date_invoice')
				}
				date_invoice = kwargs.get('date_invoice')
				if date_invoice:
					data['date_invoice']=date_invoice
				if res_payment['status_message']:
					status_message += res_payment['status_message']
				res = self.SetOrderPaid(data)
				status_message += res['status_message']
				status = res['status']
			if OrderState and OrderState == 'done':
				sale_obj.action_done()
				status_message += "Order==> Done ."
		if OrderState and OrderState == 'shipped' or ShipOrder:
			res = self.set_order_shipped(OrderObj.id,**kwargs)
			if res:
				status_message += res['status_message']
				status = res['status']

		return {'status_message': status_message,
				'status': status
				}

	def _SetOdooOrderState(self, order_id, channel_id, feed_order_state='', payment_method=False,**kwargs):
		status_message = "<br/>Order %s " % (order_id.name)
		if channel_id and order_id and order_id.order_line:
			context = dict(self._context or {})
			order_state = ''
			create_invoice = False
			ship_order=False
			invoice_state = ''
			om_order_state_ids =channel_id.order_state_ids
			order_state_ids = om_order_state_ids.filtered(
				lambda state: state.channel_state == feed_order_state) or channel_id.order_state_ids.filtered(
					'default_order_state')
			if order_state_ids:
				state_id = order_state_ids[0]
				order_state = state_id.odoo_order_state
				create_invoice = state_id.odoo_create_invoice
				invoice_state = state_id.odoo_set_invoice_state
				ship_order = state_id.odoo_ship_order
			if order_state in ['cancelled']:
				res = self.with_context(context)._cancel_order(
					order_id, channel_id)
				status_message += res['status_message']
			else:
				res = self.with_context(context)._ConfirmOrderAndCreateInvoice(
					order_id, channel_id, payment_method, order_state,
					create_invoice, invoice_state, ship_order,**kwargs)
				status_message += res['status_message']
		return status_message
