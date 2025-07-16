/** @odoo-module **/

import { registry } from "@web/core/registry";
import { TruckProgressWidget } from "./truck_widget";

// Register the TruckProgressWidget component
registry.category("components").add("TruckProgressWidget", TruckProgressWidget);

/* Trailer visualization JavaScript for interactive truck loading display */

odoo.define('records_management.trailer_visualization', function (require) {
    'use strict';
    
    // Additional trailer visualization widgets will be implemented here
    
});
