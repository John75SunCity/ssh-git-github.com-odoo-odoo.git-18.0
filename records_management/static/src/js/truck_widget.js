/** @odoo-module **/
import { Component, xml } from "@odoo/owl";

export class TruckProgressWidget extends Component {
    static template = xml`
        <svg viewBox="0 0 100 30" class="truck">
            <rect x="0" y="0" width="100" height="30" fill="lightgray" rx="5"/> <!-- Trailer body -->
            <rect x="0" y="0" t-att-width="(props.bale_count / props.max * 100)" height="30" fill="green" rx="5"/> <!-- Progress fill -->
            <text x="50" y="15" fill="black" text-anchor="middle"><t t-esc="props.bale_count + '/' + props.max"/></text>
        </svg>
    `;
}
