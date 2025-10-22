/** @odoo-module **/
import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class PaperLoadProgressField extends Component {
    static template = xml`
        <div class="paper-load-progress-field">
            <div class="progress-container">
                <div class="progress" style="height: 30px;">
                    <div class="progress-bar bg-success"
                         role="progressbar"
                         t-att-style="'width: ' + this.progressPercent + '%'"
                         t-att-aria-valuenow="this.baleCount"
                         aria-valuemin="0"
                         aria-valuemax="28">
                        <t t-esc="this.baleCount"/> / 28 bales (<t t-esc="this.progressPercent"/>%)
                    </div>
                </div>
                <div class="mt-2 small text-muted">
                    <span t-if="this.totalWeight">Weight: <t t-esc="Math.round(this.totalWeight)"/> lbs</span>
                </div>
            </div>
        </div>
    `;

    static props = {
        ...standardFieldProps,
    };

    get baleCount() {
        return this.props.record.data.bale_count || 0;
    }

    get totalWeight() {
        return this.props.record.data.total_weight || this.props.record.data.total_weight_lbs || 0;
    }

    get progressPercent() {
        return Math.round((this.baleCount / 28) * 100);
    }
}

// Register the field widget for Odoo 18/19
registry.category("fields").add("paper_load_progress", {
    component: PaperLoadProgressField,
    displayName: "Paper Load Progress",
    supportedTypes: ["integer", "float"],
});
