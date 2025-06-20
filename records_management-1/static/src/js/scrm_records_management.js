// This file contains JavaScript functionality for the Records Management module, including barcode scanning integration.

odoo.define('records_management.scrm_records_management', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var rpc = require('web.rpc');

    var _t = core._t;

    publicWidget.registry.PickupRequestForm = publicWidget.Widget.extend({
        selector: '.pickup-request-form',
        events: {
            'click .btn-submit': '_onSubmit',
            'change .item-checkbox': '_onItemChange',
        },

        _onSubmit: function (ev) {
            ev.preventDefault();
            var selectedItems = this._getSelectedItems();
            if (selectedItems.length === 0) {
                this._showError(_t("Please select at least one item for pickup."));
                return;
            }
            this._createPickupRequest(selectedItems);
        },

        _getSelectedItems: function () {
            var selectedItems = [];
            this.$('.item-checkbox:checked').each(function () {
                selectedItems.push($(this).data('item-id'));
            });
            return selectedItems;
        },

        _createPickupRequest: function (itemIds) {
            var self = this;
            rpc.query({
                model: 'pickup.request',
                method: 'create_pickup_request',
                args: [session.partner_id, itemIds],
            }).then(function (result) {
                if (result) {
                    window.location.href = '/my/inventory';
                }
            }).catch(function (error) {
                self._showError(error.data.message);
            });
        },

        _showError: function (message) {
            this.$('.error-message').text(message).show();
        },

        _onItemChange: function () {
            this.$('.error-message').hide();
        },
    });
});