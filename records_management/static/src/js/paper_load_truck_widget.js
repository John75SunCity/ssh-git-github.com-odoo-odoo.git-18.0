/** @odoo-module **/
import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class PaperLoadTruckWidget extends Component {
    static template = xml`
        <div class="paper-load-truck-widget">
            <div class="truck-card">
                <div class="truck-header">
                    <div class="truck-header__counts">
                        <span class="truck-header__title">Trailer Load</span>
                        <div class="truck-header__bales">
                            <span class="truck-header__bales-value">
                                <t t-esc="this.safeBaleCount"/>
                            </span>
                            <span class="truck-header__bales-separator">/</span>
                            <span class="truck-header__capacity">
                                <t t-esc="this.capacity"/>
                            </span>
                            <span class="truck-header__suffix">bales</span>
                        </div>
                        <small class="truck-header__weight">
                            <t t-esc="this.weightText"/>
                        </small>
                    </div>
                    <div class="truck-header__meter">
                        <div class="progress-meter">
                            <div class="progress-meter__track">
                                <div class="progress-meter__fill" t-att-style="'width: ' + this.loadPercent + '%'"/>
                            </div>
                            <span class="progress-meter__value">
                                <t t-esc="this.loadPercent"/>%
                            </span>
                        </div>
                        <small class="truck-header__hint">Capacity utilized</small>
                    </div>
                </div>

                <div class="truck-visual">
                    <svg viewBox="0 0 720 220" class="truck-svg" role="img" aria-labelledby="truckLoadTitle truckLoadDesc">
                        <title id="truckLoadTitle">
                            <t t-esc="this.accessibleLabel"/>
                        </title>
                        <desc id="truckLoadDesc">
                            <t t-esc="this.accessibleDescription"/>
                        </desc>
                        <defs>
                            <linearGradient id="rmTrailerBody" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" stop-color="#ffffff"/>
                                <stop offset="100%" stop-color="#dbe7f6"/>
                            </linearGradient>
                            <linearGradient id="rmTrailerFill" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stop-color="#4caf50"/>
                                <stop offset="100%" stop-color="#7ad879"/>
                            </linearGradient>
                            <linearGradient id="rmCabBody" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stop-color="#ff9029"/>
                                <stop offset="55%" stop-color="#ff7b1f"/>
                                <stop offset="100%" stop-color="#ff6018"/>
                            </linearGradient>
                            <linearGradient id="rmCabShadow" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stop-color="#e05c10"/>
                                <stop offset="100%" stop-color="#b8400a"/>
                            </linearGradient>
                            <linearGradient id="rmWindow" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" stop-color="#e9f6ff"/>
                                <stop offset="100%" stop-color="#cde8fb"/>
                            </linearGradient>
                            <radialGradient id="rmWheel" cx="50%" cy="50%" r="50%">
                                <stop offset="20%" stop-color="#4e5a61"/>
                                <stop offset="100%" stop-color="#111418"/>
                            </radialGradient>
                            <filter id="rmGroundBlur" x="-10%" y="-40%" width="120%" height="180%">
                                <feGaussianBlur in="SourceGraphic" stdDeviation="12" result="blur"/>
                                <feOffset dy="6" result="offset"/>
                                <feBlend in="blur" in2="offset" mode="normal"/>
                            </filter>
                        </defs>
                        <ellipse class="ground-shadow" cx="340" cy="204" rx="280" ry="26" filter="url(#rmGroundBlur)"/>

                        <g class="trailer-group">
                            <rect class="trailer-body" x="40" y="68" width="520" height="116" rx="18" fill="url(#rmTrailerBody)"/>
                            <rect class="trailer-fill" x="52" y="80" height="92" rx="14" fill="url(#rmTrailerFill)" t-att-width="this.trailerFillWidth"/>
                            <rect class="trailer-outline" x="40" y="68" width="520" height="116" rx="18"/>
                            <line class="trailer-divider" x1="40" y1="126" x2="560" y2="126"/>
                            <rect class="connector" x="550" y="118" width="36" height="16" rx="6"/>
                            <rect class="connector-pin" x="566" y="132" width="24" height="12" rx="5"/>
                        </g>

                        <g class="bale-grid">
                            <t t-foreach="this.slotLayout" t-as="slot" t-key="slot.id">
                                <rect width="52" height="18" rx="9"
                                      t-att-x="slot.x"
                                      t-att-y="slot.y"
                                      t-att-class="'bale-slot ' + (slot.filled ? 'is-filled' : 'is-empty')"
                                      t-att-style="slot.filled and slot.color ? '--slot-color: ' + slot.color : ''"/>
                                <t t-if="slot.filled and slot.label">
                                    <text t-att-x="slot.x + 26"
                                          t-att-y="slot.y + 13"
                                          text-anchor="middle"
                                          class="bale-slot__label">
                                        <t t-esc="slot.label"/>
                                    </text>
                                </t>
                            </t>
                        </g>

                        <g class="cab-group">
                            <path class="cab-body" d="M584,74h78c22,0,40,14,40,32v66c0,18-18,32-40,32h-82c-18,0-32-10-32-26v-68c0-20,16-36,36-36z" fill="url(#rmCabBody)"/>
                            <path class="cab-shadow" d="M678,74h18c18,0,32,14,32,32v66c0,18-14,32-32,32h-34z" fill="url(#rmCabShadow)"/>
                            <rect class="cab-window" x="604" y="96" width="56" height="34" rx="10" fill="url(#rmWindow)"/>
                            <rect class="cab-door" x="664" y="124" width="34" height="48" rx="9"/>
                            <rect class="cab-step" x="676" y="164" width="42" height="12" rx="6"/>
                            <circle class="marker-light" cx="604" cy="152" r="9"/>
                            <circle class="marker-light" cx="704" cy="152" r="9"/>
                        </g>

                        <g class="wheel-group">
                            <g class="wheel" transform="translate(210 188)">
                                <circle class="wheel-outer" r="30" fill="url(#rmWheel)"/>
                                <circle class="wheel-inner" r="16"/>
                                <circle class="wheel-cap" r="9"/>
                            </g>
                            <g class="wheel" transform="translate(270 188)">
                                <circle class="wheel-outer" r="30" fill="url(#rmWheel)"/>
                                <circle class="wheel-inner" r="16"/>
                                <circle class="wheel-cap" r="9"/>
                            </g>
                            <g class="wheel" transform="translate(330 188)">
                                <circle class="wheel-outer" r="30" fill="url(#rmWheel)"/>
                                <circle class="wheel-inner" r="16"/>
                                <circle class="wheel-cap" r="9"/>
                            </g>
                            <g class="wheel" transform="translate(520 192)">
                                <circle class="wheel-outer" r="32" fill="url(#rmWheel)"/>
                                <circle class="wheel-inner" r="18"/>
                                <circle class="wheel-cap" r="10"/>
                            </g>
                            <g class="wheel" transform="translate(628 192)">
                                <circle class="wheel-outer" r="32" fill="url(#rmWheel)"/>
                                <circle class="wheel-inner" r="18"/>
                                <circle class="wheel-cap" r="10"/>
                            </g>
                        </g>
                    </svg>
                </div>

                <div class="load-breakdown">
                    <div class="load-breakdown__item"
                         t-foreach="this.gradeData"
                         t-as="grade"
                         t-key="grade.key">
                        <div class="load-breakdown__swatch" t-att-style="'--grade-color: ' + grade.color">
                            <span><t t-esc="grade.letter"/></span>
                        </div>
                        <div class="load-breakdown__meta">
                            <span class="load-breakdown__label">
                                <t t-esc="grade.name"/>
                            </span>
                            <span class="load-breakdown__count">
                                <t t-esc="grade.count"/> bales
                                <t t-if="grade.percent !== null">
                                    • <t t-esc="grade.percent"/>%
                                </t>
                            </span>
                        </div>
                    </div>
                </div>

                <div class="load-status" t-att-class="'status-' + (this.status || 'draft')">
                    <div class="status-content">
                        <span class="status-text">
                            <t t-if="this.status === 'draft'">📝 Planning</t>
                            <t t-elif="this.status === 'scheduled'">📅 Scheduled</t>
                            <t t-elif="this.status === 'ready_pickup'">🚛 Ready</t>
                            <t t-elif="this.status === 'in_transit'">🚚 In Transit</t>
                            <t t-elif="this.status === 'delivered'">✅ Delivered</t>
                            <t t-elif="this.status === 'paid'">💰 Paid</t>
                            <t t-else="">📦 Load</t>
                        </span>
                        <span class="status-meta">
                            <t t-esc="this.loadPercent"/>% full
                        </span>
                    </div>
                </div>
            </div>
        </div>
    `;

    static props = {
        ...standardFieldProps,
        baleCount: { type: Number, optional: true },
        totalWeight: { type: Number, optional: true },
        whiteCount: { type: Number, optional: true },
        mixedCount: { type: Number, optional: true },
        cardboardCount: { type: Number, optional: true },
        status: { type: String, optional: true },
    };

    get capacity() {
        return 28;
    }

    get safeBaleCount() {
        return Math.max(0, Math.min(this.capacity, this.baleCount));
    }

    get loadPercent() {
        if (!this.capacity) {
            return 0;
        }
        return Math.min(100, Math.round((this.safeBaleCount / this.capacity) * 100));
    }

    get trailerFillWidth() {
        const maxWidth = 496;
        if (!this.capacity) {
            return 0;
        }
        return Math.max(0, Math.min(maxWidth, (this.safeBaleCount / this.capacity) * maxWidth));
    }

    get weightText() {
        const weight = Math.round(this.totalWeight || 0);
        return weight ? `${weight} lbs total` : "No weight logged";
    }

    get accessibleLabel() {
        return `Trailer load ${this.safeBaleCount} of ${this.capacity} bales (${this.loadPercent}% capacity).`;
    }

    get accessibleDescription() {
        const parts = this.gradeData
            .filter((grade) => grade.count)
            .map((grade) => `${grade.count} ${grade.name.toLowerCase()}`);
        return parts.length ? parts.join(", ") : "No paper grade distribution provided.";
    }

    get gradeData() {
        const safe = this.safeBaleCount;
        const grades = [
            { key: "white", name: "White Ledger", letter: "W", color: "#1E88E5", count: this.whiteCount },
            { key: "mixed", name: "Mixed Paper", letter: "M", color: "#FB8C00", count: this.mixedCount },
            { key: "cardboard", name: "Cardboard", letter: "C", color: "#7CB342", count: this.cardboardCount },
        ];

        let allocated = 0;
        return grades.map((grade) => {
            const rawCount = Math.max(0, grade.count || 0);
            const remainingCapacity = Math.max(0, safe - allocated);
            const allocatedForSlots = safe ? Math.min(rawCount, remainingCapacity) : 0;
            allocated += allocatedForSlots;
            return {
                ...grade,
                count: rawCount,
                allocated: allocatedForSlots,
                percent: safe ? Math.round((allocatedForSlots / safe) * 100) : null,
            };
        });
    }

    get slotLayout() {
        const capacity = this.capacity;
        const filledSlots = this.safeBaleCount;
        const gradeData = this.gradeData;
        const slotWidth = 52;
        const slotHeight = 18;
        const gapX = 14;
        const gapY = 10;
        const columns = 7;
        const startX = 68;
        const startY = 82;

        const gradeOrder = [];
        for (const grade of gradeData) {
            const maxSlots = Math.min(grade.allocated, filledSlots - gradeOrder.length);
            for (let i = 0; i < maxSlots; i++) {
                gradeOrder.push(grade);
            }
        }
        while (gradeOrder.length < filledSlots) {
            gradeOrder.push({
                key: "overflow",
                letter: "•",
                color: "#90A4AE",
            });
        }

        return Array.from({ length: capacity }, (_, index) => {
            const column = index % columns;
            const row = Math.floor(index / columns);
            const x = startX + column * (slotWidth + gapX);
            const y = startY + row * (slotHeight + gapY);
            const filled = index < filledSlots;
            const grade = filled ? gradeOrder[index] : null;
            return {
                id: `slot-${index}`,
                x,
                y,
                filled,
                color: grade ? grade.color : null,
                label: grade ? grade.letter : null,
            };
        });
    }

    get baleCount() {
        return this.props.record.data.bale_count || 0;
    }

    get totalWeight() {
        return this.props.record.data.total_weight || 0;
    }

    get whiteCount() {
        return this.props.record.data.white_count || 0;
    }

    get mixedCount() {
        return this.props.record.data.mixed_count || 0;
    }

    get cardboardCount() {
        return this.props.record.data.cardboard_count || 0;
    }

    get status() {
        return this.props.record.data.status || 'draft';
    }
}

// Register as a field widget in the fields registry for Odoo 18/19
registry.category("fields").add("paper_load_truck_widget", {
    component: PaperLoadTruckWidget,
    displayName: "Paper Load Truck Visualization",
    supportedTypes: ["integer", "float"],
});

if (!document.getElementById("rm-paper-load-truck-style")) {
    const style = document.createElement("style");
    style.id = "rm-paper-load-truck-style";
    style.textContent = `
.paper-load-truck-widget {
    font-family: inherit;
    color: #0d213d;
}

.paper-load-truck-widget .truck-card {
    display: flex;
    flex-direction: column;
    gap: 18px;
    background: linear-gradient(180deg, #ffffff 0%, #f4f8ff 100%);
    border: 1px solid #d6e2f3;
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 10px 26px -18px rgba(12, 61, 119, 0.5);
}

.truck-header {
    display: flex;
    justify-content: space-between;
    gap: 18px;
    flex-wrap: wrap;
}

.truck-header__counts {
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-width: 160px;
}

.truck-header__title {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #4b678c;
}

.truck-header__bales {
    display: flex;
    align-items: baseline;
    gap: 4px;
    font-weight: 600;
    color: #0d47a1;
    font-size: 26px;
}

.truck-header__bales-value {
    font-size: 32px;
    line-height: 1;
}

.truck-header__bales-separator,
.truck-header__capacity {
    font-size: 18px;
    color: #3f5a86;
}

.truck-header__suffix {
    font-size: 14px;
    color: #5f7998;
    font-weight: 500;
}

.truck-header__weight {
    font-size: 12px;
    color: #6c84a2;
}

.truck-header__meter {
    display: flex;
    flex-direction: column;
    gap: 8px;
    align-items: flex-end;
}

.progress-meter {
    display: flex;
    align-items: center;
    gap: 12px;
}

.progress-meter__track {
    width: 160px;
    height: 8px;
    background: #e3ecf7;
    border-radius: 999px;
    overflow: hidden;
}

.progress-meter__fill {
    display: block;
    height: 100%;
    background: linear-gradient(90deg, #4caf50 0%, #7fd37f 100%);
    border-radius: inherit;
    transition: width 180ms ease-out;
}

.progress-meter__value {
    font-weight: 600;
    color: #1b4d89;
}

.truck-header__hint {
    font-size: 11px;
    color: #7891b0;
}

.truck-visual {
    background: linear-gradient(180deg, rgba(240, 245, 255, 0.9) 0%, rgba(255, 255, 255, 0.95) 100%);
    border-radius: 18px;
    padding: 18px 22px;
    border: 1px solid rgba(138, 170, 210, 0.45);
}

.truck-svg {
    width: 100%;
    height: auto;
    display: block;
}

.bale-slot {
    fill: rgba(255, 255, 255, 0.55);
    stroke: rgba(15, 67, 140, 0.22);
    stroke-width: 1.6;
}

.bale-slot.is-filled {
    fill: var(--slot-color, #4caf50);
    stroke: rgba(0, 0, 0, 0.12);
}

.bale-slot.is-empty {
    fill: rgba(255, 255, 255, 0.32);
    stroke-dasharray: 12 8;
}

.bale-slot__label {
    fill: #ffffff;
    font-size: 11px;
    font-weight: 600;
    pointer-events: none;
}

.ground-shadow {
    fill: rgba(17, 33, 56, 0.14);
}

.trailer-outline {
    fill: none;
    stroke: #1b4d89;
    stroke-width: 4;
}

.trailer-divider {
    stroke: rgba(33, 74, 126, 0.22);
    stroke-width: 2;
    stroke-dasharray: 20 14;
}

.connector {
    fill: rgba(24, 58, 102, 0.35);
}

.connector-pin {
    fill: rgba(54, 76, 103, 0.45);
}

.cab-door {
    fill: rgba(7, 24, 46, 0.22);
}

.cab-step {
    fill: rgba(26, 47, 72, 0.48);
}

.marker-light {
    fill: rgba(255, 193, 7, 0.85);
}

.wheel-group .wheel-inner {
    fill: #cfd8df;
}

.wheel-group .wheel-cap {
    fill: #f7fbff;
}

.load-breakdown {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
}

.load-breakdown__item {
    display: flex;
    align-items: center;
    gap: 12px;
    background: #ffffff;
    border: 1px solid #d8e4f5;
    border-radius: 12px;
    padding: 12px 14px;
    flex: 1 1 180px;
    min-width: 160px;
}

.load-breakdown__swatch {
    width: 42px;
    height: 42px;
    border-radius: 10px;
    background: var(--grade-color, #90a4ae);
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 18px;
    box-shadow: 0 8px 16px -12px var(--grade-color, rgba(0, 0, 0, 0.2));
}

.load-breakdown__meta {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.load-breakdown__label {
    font-weight: 600;
    color: #1f3c66;
}

.load-breakdown__count {
    font-size: 12px;
    color: #556d8d;
}

.load-status {
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 13px;
    border: 1px solid transparent;
}

.status-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.status-meta {
    font-weight: 600;
    color: #275080;
}

.status-draft {
    background: rgba(120, 144, 156, 0.14);
    border-color: rgba(120, 144, 156, 0.32);
    color: #37474f;
}

.status-scheduled {
    background: rgba(33, 150, 243, 0.12);
    border-color: rgba(33, 150, 243, 0.28);
    color: #0d47a1;
}

.status-ready_pickup {
    background: rgba(255, 152, 0, 0.12);
    border-color: rgba(255, 152, 0, 0.28);
    color: #e65100;
}

.status-in_transit {
    background: rgba(76, 175, 80, 0.12);
    border-color: rgba(76, 175, 80, 0.28);
    color: #1b5e20;
}

.status-delivered {
    background: rgba(0, 188, 212, 0.1);
    border-color: rgba(0, 188, 212, 0.26);
    color: #006064;
}

.status-paid {
    background: rgba(129, 199, 132, 0.14);
    border-color: rgba(129, 199, 132, 0.3);
    color: #1b5e20;
}
`;
    document.head.appendChild(style);
}
