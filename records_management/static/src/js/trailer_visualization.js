/** @odoo-module **/

import { registry } from "@web/core/registry";
import { TruckProgressWidget } from "./truck_widget";

// Register the TruckProgressWidget component
registry.category("components").add("TruckProgressWidget", TruckProgressWidget);

/* Trailer visualization JavaScript for interactive truck loading display */
// Additional trailer visualization widgets can be added here using @odoo-module style
