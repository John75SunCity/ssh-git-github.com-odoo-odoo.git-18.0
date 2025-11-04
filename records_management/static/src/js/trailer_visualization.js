/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, xml } from "@odoo/owl";

export class TrailerVisualizationWidget extends Component {
    static template = xml`
        <div class="trailer-visualization">
            <svg viewBox="0 0 520 160" class="trailer-svg" role="img" aria-labelledby="rmTrailerTitle rmTrailerDesc">
                <title id="rmTrailerTitle">Trailer loading progress</title>
                <desc id="rmTrailerDesc">Visual indicator showing how full the trailer is based on the number of loaded bales.</desc>
                <defs>
                    <linearGradient id="rmTrailerBody" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stop-color="#e3f2fd" />
                        <stop offset="100%" stop-color="#bbdefb" />
                    </linearGradient>
                    <linearGradient id="rmCabGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stop-color="#1565c0" />
                        <stop offset="100%" stop-color="#42a5f5" />
                    </linearGradient>
                </defs>

                <!-- Cab -->
                <rect x="48" y="72" width="82" height="48" rx="6" fill="url(#rmCabGradient)" stroke="#0d47a1" stroke-width="2" />
                <rect x="60" y="58" width="54" height="24" rx="4" fill="#64b5f6" stroke="#0d47a1" stroke-width="2" />
                <rect x="70" y="62" width="22" height="14" rx="2" fill="#e1f5fe" stroke="#0d47a1" stroke-width="1.5" />
                <circle cx="120" cy="98" r="6" fill="#0d47a1" />

                <!-- Trailer body -->
                <rect x="140" y="52" width="340" height="76" rx="10" fill="url(#rmTrailerBody)" stroke="#1e88e5" stroke-width="2" />
                <rect x="140" y="52" width="340" height="76" rx="10" fill="none" stroke="#1565c0" stroke-width="1" stroke-dasharray="6 6" opacity="0.35" />

                <!-- Load indicator -->
                <rect x="154" y="64" height="52" rx="8"
                      t-att-width="this.fillWidth"
                      t-att-fill="this.fillColor"
                      opacity="0.9" />
                <rect x="154" y="64" width="312" height="52" rx="8" fill="none" stroke="#0d47a1" stroke-width="1.5" opacity="0.4" />

                <!-- Capacity markers -->
                <g stroke="#64b5f6" stroke-width="1" opacity="0.45">
                    <line x1="232" y1="64" x2="232" y2="116" />
                    <line x1="310" y1="64" x2="310" y2="116" />
                    <line x1="388" y1="64" x2="388" y2="116" />
                    <line x1="466" y1="64" x2="466" y2="116" />
                </g>

                <!-- Text overlay -->
                <text x="310" y="97" text-anchor="middle" fill="#0d47a1" font-size="18" font-weight="600">
                    <t t-esc="this.baleCount"/> / <t t-esc="this.capacityLabel"/> bales
                </text>
                <text x="310" y="118" text-anchor="middle" fill="#546e7a" font-size="12">
                    <t t-esc="this.loadStatusLabel"/>
                </text>

                <!-- Wheels -->
                <g fill="#263238">
                    <ellipse cx="190" cy="135" rx="14" ry="10" />
                    <ellipse cx="245" cy="135" rx="14" ry="10" />
                    <ellipse cx="300" cy="135" rx="14" ry="10" />
                    <ellipse cx="355" cy="135" rx="14" ry="10" />
                    <ellipse cx="410" cy="135" rx="14" ry="10" />
                </g>
                <g fill="#eceff1">
                    <ellipse cx="190" cy="135" rx="5" ry="4" />
                    <ellipse cx="245" cy="135" rx="5" ry="4" />
                    <ellipse cx="300" cy="135" rx="5" ry="4" />
                    <ellipse cx="355" cy="135" rx="5" ry="4" />
                    <ellipse cx="410" cy="135" rx="5" ry="4" />
                </g>
            </svg>

            <div class="capacity-info mt-2 text-center">
                <span class="badge" t-att-class="this.loadBadgeClass">
                    <t t-esc="this.loadPercentage"/>% Loaded
                </span>
                <div class="text-muted small mt-1">
                    <t t-esc="this.baleCount"/> bales in trailer · <t t-esc="this.remainingLabel"/>
                </div>
            </div>
        </div>
    `;

    static props = {
        ...standardFieldProps,
    };

    get baleCount() {
        return this.props.record.data.bale_count || this.props.record.data.total_bales || 0;
    }

    get capacity() {
        return this.props.record.data.trailer_capacity || this.props.record.data.capacity || 28;
    }

    get capacityLabel() {
        return this.capacity || 0;
    }

    get loadRatio() {
        if (!this.capacity) {
            return 0;
        }
        return Math.max(0, Math.min(1, this.baleCount / this.capacity));
    }

    get fillWidth() {
        const maxWidth = 312;
        return Math.round(this.loadRatio * maxWidth);
    }

    get loadPercentage() {
        return Math.round(this.loadRatio * 100);
    }

    get fillColor() {
        if (this.loadRatio >= 1) {
            return "#2e7d32";
        }
        if (this.loadRatio >= 0.75) {
            return "#43a047";
        }
        if (this.loadRatio >= 0.5) {
            return "#1e88e5";
        }
        return "#42a5f5";
    }

    get loadBadgeClass() {
        if (this.loadRatio >= 1) {
            return "badge-success";
        }
        if (this.loadRatio >= 0.75) {
            return "badge-primary";
        }
        return "badge-info";
    }

    get remainingLabel() {
        if (!this.capacity) {
            return "capacity unknown";
        }
        const remaining = Math.max(0, this.capacity - this.baleCount);
        if (remaining === 0) {
            return "trailer is at capacity";
        }
        return `${remaining} bales remaining`;
    }

    get loadStatusLabel() {
        if (this.loadRatio >= 1) {
            return "Fully loaded";
        }
        if (this.loadRatio >= 0.75) {
            return "Approaching capacity";
        }
        if (this.loadRatio >= 0.5) {
            return "Half loaded";
        }
        return "Room available";
    }
}

// Register as field widget for Odoo 18/19
registry.category("fields").add("trailer_visualization", {
    component: TrailerVisualizationWidget,
    displayName: "Trailer Visualization",
    supportedTypes: ["integer", "float"],
});
