/** @odoo-module **/
import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { PaperLoadTruckWidget } from "./paper_load_truck_widget";

export class PaperLoadProgressField extends Component {
    static template = xml`
        <div class="paper-load-progress-field">
            <PaperLoadTruckWidget 
                bale_count="props.record.data.bale_count"
                total_weight="props.record.data.total_weight_lbs"
                white_count="props.record.data.white_paper_count"
                mixed_count="props.record.data.mixed_paper_count"
                cardboard_count="props.record.data.cardboard_count"
                status="props.record.data.status"
                max_capacity="50"/>
        </div>
    `;

    static components = { PaperLoadTruckWidget };
    static props = {
        ...standardFieldProps,
    };
}

// Register the field widget (Odoo 19 expects an object with `component`)
registry.category("fields").add("paper_load_progress", {
    component: PaperLoadProgressField,
    displayName: "Paper Load Progress",
    supportedTypes: ["char", "text", "integer", "float"],
});
