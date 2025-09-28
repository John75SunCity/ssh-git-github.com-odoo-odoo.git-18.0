/** @odoo-module **/
/**
 * Customer Portal Diagram (Odoo 18 Compatible)
 * Simplified version to prevent asset bundle errors
 */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";

// Minimal compatible implementation
console.log("Customer Portal Diagram module loaded (simplified version)");

class CustomerPortalDiagramComponent extends Component {
    static template = `<div class="o_customer_portal_diagram">
        <p>Customer Portal Diagram - Odoo 18 Compatible</p>
    </div>`;
}

// Register the component
registry.category("actions").add("customer_portal_diagram", CustomerPortalDiagramComponent);
