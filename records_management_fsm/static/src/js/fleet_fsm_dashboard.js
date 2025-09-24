/**
 * Fleet & FSM Integration Dashboard Client Action
 * Minimal placeholder to satisfy ir.actions.client tag "fleet_fsm_dashboard".
 * Extend later with real KPIs / graphs / RPC calls.
 */

/** @odoo-module **/
import { registry } from '@web/core/registry';
import { Component, onWillStart } from '@odoo/owl';
import { useService } from '@web/core/utils/hooks';

class FleetFSMDashboard extends Component {
    setup() {
        this.orm = useService('orm');
        this.user = useService('user');
        this.action = useService('action');
        onWillStart(async () => {
            // Placeholder for async prefetch; keep extremely light.
            this.metrics = await this._loadMetrics();
        });
    }

    async _loadMetrics() { // Future: aggregate KPIs from FSM tasks, routes, fleet vehicles
        return {
            tasks_today: 0,
            open_routes: 0,
            active_vehicles: 0,
        };
    }
}

FleetFSMDashboard.template = 'records_management_fsm.FleetFSMDashboard';
FleetFSMDashboard.displayName = 'Fleet & FSM Dashboard';

registry.category('actions').add('fleet_fsm_dashboard', FleetFSMDashboard);
