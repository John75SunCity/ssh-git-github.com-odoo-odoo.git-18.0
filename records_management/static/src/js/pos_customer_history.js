'use strict';
/**
 * POS Customer History Widget (minimal stub)
 * Fetches recent order history for selected customer and stores in env for future UI integration.
 * This keeps implementation lightweight; future enhancement can render a side panel or popup.
 */
odoo.define('records_management.PosCustomerHistory', function (require) {
    const { registry } = require('@web/core/registry');
    const { patch } = require('@web/core/utils/patch');
    const PosStore = require('point_of_sale.PosStore');
    const rpc = require('web.rpc');

    patch(PosStore.prototype, 'records_management_pos_customer_history', {
        async afterSetClient(partner) {
            await this._super(...arguments);
            try {
                const config = this.config || {};
                if (!config.enable_pos_customer_history || !partner || !partner.id) {
                    this.pos_customer_history = [];
                    return;
                }
                const result = await rpc.query({
                    route: '/records_management/pos/customer_history',
                    params: { partner_id: partner.id, limit: 15 },
                });
                this.pos_customer_history = (result && result.orders) || [];
                // Simple console log for now; UI integration can follow.
                console.log('POS Customer History loaded', this.pos_customer_history);
            } catch (err) {
                console.warn('Failed to load customer history', err);
            }
        },
    });

    // Debug command palette (optional future enhancement)
    registry.category('pos_customer_history') && registry.category('pos_customer_history').add('history_debug', {
        name: 'Show Last Customer History',
        run: (env) => {
            console.log('Current customer history', env.services.pos.pos_customer_history);
        },
    });
});
