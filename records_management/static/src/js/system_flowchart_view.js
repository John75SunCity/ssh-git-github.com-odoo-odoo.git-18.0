/** @odoo-module **/
/**
 * System Flowchart View (Odoo 19 Compatible)
 * Simplified version to prevent asset bundle errors
 */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";

// Minimal compatible implementation
console.log("System Flowchart module loaded (simplified version)");

class SystemFlowchartComponent extends Component {
    static template = `<div class="o_system_flowchart">
        <p>System Flowchart View - Odoo 19 Compatible</p>
    </div>`;
}

// Register the component
registry.category("actions").add("system_flowchart", SystemFlowchartComponent);
