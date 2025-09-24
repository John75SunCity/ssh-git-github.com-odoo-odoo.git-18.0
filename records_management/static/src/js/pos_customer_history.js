/** @odoo-module **/
/**
 * POS Customer History Extension (ESM Version)
 * Fetches recent order history for the selected customer and stores it on the PosStore.
 * Lightweight stub; future enhancement can expose a component / side panel UI.
 */
import { patch } from '@web/core/utils/patch';
import { registry } from '@web/core/registry';
import { PosStore } from 'point_of_sale.PosStore';
import { rpc } from '@web/core/network/rpc_service';

patch(PosStore.prototype, 'records_management_pos_customer_history', {
    async afterSetClient(partner) {
        await this._super(...arguments);
        try {
            const config = this.config || {};
            if (!config.enable_pos_customer_history || !partner || !partner.id) {
                this.pos_customer_history = [];
                return;
            }
            const result = await rpc('/records_management/pos/customer_history', {
                partner_id: partner.id,
                limit: 15,
            });
            this.pos_customer_history = (result && result.orders) || [];
            // Debug log; safe to remove in production hardening.
            console.log('POS Customer History loaded', this.pos_customer_history);
        } catch (err) {
            console.warn('Failed to load customer history', err);
        }
    },
});

// Optional command palette category for quick debug (guard if category absent)
const historyCategory = registry.category('pos_customer_history');
if (historyCategory) {
    historyCategory.add('history_debug', {
        name: 'Show Last Customer History',
        run: (env) => {
            console.log('Current customer history', env.services.pos.pos_customer_history);
        },
    });
}
