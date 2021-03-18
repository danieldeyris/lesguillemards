
//console.log("custom js caleedddddddddddddddddddddddddddddddddd")
odoo.define('guillemards_specifique.pos_extended', function (require) {
	"use strict";

	var models = require('point_of_sale.models');
	var screens = require('point_of_sale.screens');
	var core = require('web.core');
	var gui = require('point_of_sale.gui');
	var popups = require('point_of_sale.popups');
	

	var QWeb = core.qweb;
	var _t = core._t;

	var _super_posmodel = models.PosModel.prototype;
	models.PosModel = models.PosModel.extend({
		initialize: function (session, attributes) {
			var session_model = _.find(this.models, function(model){ return model.model === 'pos.session'; });
			session_model.fields.push('branch_telephone');
			session_model.fields.push('branch_email');
			session_model.fields.push('branch_website');
			return _super_posmodel.initialize.call(this, session, attributes);
		},

	});

    screens.ReceiptScreenWidget.include({
        get_receipt_render_env: function() {
            var env = this._super.apply(this, arguments);
            env.receipt.company.logo = window.location.origin + '/web/image?model=pos.config&field=image&id='+this.pos.config.id
            env.receipt.company.contact_address = this.pos.config.branch_id[1];
            env.receipt.company.phone = this.pos.pos_session.branch_telephone;
            env.receipt.company.email = this.pos.pos_session.branch_email;
            env.receipt.company.website = this.pos.pos_session.branch_website;
            return env;
        },
    });

});


