/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, xml } from "@odoo/owl";

export class TrailerVisualizationWidget extends Component {
    static template = xml`
        <div class="trailer-visualization">
            <svg viewBox="0 0 300 120" class="trailer-svg">
                <!-- 3D-like trailer perspective -->
                <defs>
                    <linearGradient id="trailerGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:#e3f2fd;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#90caf9;stop-opacity:1" />
                    </linearGradient>
                </defs>
                
                <!-- Trailer body with perspective -->
                <polygon points="50,30 250,30 270,50 30,50" fill="url(#trailerGradient)" stroke="#1976d2" stroke-width="2"/>
                <polygon points="250,30 270,50 270,90 250,70" fill="#bbdefb" stroke="#1976d2" stroke-width="2"/>
                <polygon points="30,50 270,50 270,90 30,90" fill="#e3f2fd" stroke="#1976d2" stroke-width="2"/>
                
                <!-- Load fill indicator -->
                <rect x="35" y="55" 
                      t-att-width="Math.min(230, (this.baleCount / 50) * 230)" 
                      height="30" 
                      fill="#4caf50" 
                      opacity="0.7"/>
                
                <!-- Bale count text -->
                <text x="150" y="75" text-anchor="middle" fill="#000" font-size="14" font-weight="bold">
                    <t t-esc="this.baleCount"/> / 50 bales
                </text>
                
                <!-- Wheels -->
                <ellipse cx="80" cy="95" rx="8" ry="4" fill="#333"/>
                <ellipse cx="220" cy="95" rx="8" ry="4" fill="#333"/>
            </svg>
            
            <div class="capacity-info mt-2 text-center">
                <span class="badge" t-att-class="this.baleCount >= 50 ? 'badge-success' : 'badge-info'">
                    <t t-esc="Math.round((this.baleCount / 50) * 100)"/>% Loaded
                </span>
            </div>
        </div>
    `;

    static props = {
        ...standardFieldProps,
    };

    get baleCount() {
        return this.props.record.data.bale_count || this.props.record.data.total_bales || 0;
    }
}

// Register as field widget for Odoo 18/19
registry.category("fields").add("trailer_visualization", {
    component: TrailerVisualizationWidget,
    displayName: "Trailer Visualization",
    supportedTypes: ["integer", "float"],
});
