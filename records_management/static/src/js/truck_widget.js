/** @odoo-module **/
import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class TruckProgressWidget extends Component {
    static template = xml`
        <svg viewBox="0 0 100 30" class="truck-progress">
            <rect x="0" y="0" width="100" height="30" fill="lightgray" rx="5"/> 
            <rect x="0" y="0" t-att-width="(this.baleCount / this.maxCapacity * 100)" height="30" fill="green" rx="5"/> 
            <text x="50" y="20" fill="black" text-anchor="middle" font-size="12">
                <t t-esc="this.baleCount + '/' + this.maxCapacity"/>
            </text>
        </svg>
    `;

    static props = {
        ...standardFieldProps,
    };

    get baleCount() {
        return this.props.record.data.bale_count || 0;
    }

    get maxCapacity() {
        return this.props.record.data.max_capacity || 50;
    }
}

// Register as field widget for Odoo 18/19
registry.category("fields").add("truck_widget", {
    component: TruckProgressWidget,
    displayName: "Truck Progress",
    supportedTypes: ["integer", "float"],
});
