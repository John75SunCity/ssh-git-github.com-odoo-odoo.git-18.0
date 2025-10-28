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
                    <svg viewBox="0 0 360 200" class="truck-svg" role="img" aria-labelledby="truckLoadTitle truckLoadDesc">
                        <title id="truckLoadTitle">
                            <t t-esc="this.accessibleLabel"/>
                        </title>
                        <desc id="truckLoadDesc">
                            <t t-esc="this.accessibleDescription"/>
                        </desc>
                        <defs>
                            <linearGradient id="rmTrailerGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" stop-color="#f5fbff"/>
                                <stop offset="100%" stop-color="#d8e9f6"/>
                            </linearGradient>
                            <linearGradient id="rmCabGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stop-color="#1f77d0"/>
                                <stop offset="100%" stop-color="#1457a5"/>
                            </linearGradient>
                            <linearGradient id="rmFillGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stop-color="#4caf50"/>
                                <stop offset="100%" stop-color="#7fd37f"/>
                            </linearGradient>
                            <filter id="rmShadowBlur" x="-15%" y="-15%" width="130%" height="130%">
                                <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#8fa3b5" flood-opacity="0.25"/>
                            </filter>
                        </defs>

                        <g class="trailer-group" filter="url(#rmShadowBlur)">
                            <rect class="trailer-base" x="36" y="60" width="250" height="96" rx="16" fill="url(#rmTrailerGradient)"/>
                            <rect class="trailer-fill" x="42" y="66" height="84" rx="12" fill="url(#rmFillGradient)" t-att-width="this.trailerFillWidth"/>
                            <rect class="trailer-outline" x="36" y="60" width="250" height="96" rx="16" fill="none" stroke="#0d47a1" stroke-width="2"/>
                            <line x1="36" y1="108" x2="286" y2="108" stroke="#bbd3e6" stroke-width="1.5" stroke-dasharray="6 6"/>
                        </g>

                        <g class="bale-grid">
                            <t t-foreach="this.slotLayout" t-as="slot" t-key="slot.id">
                                <rect width="26" height="18" rx="5"
                                      t-att-x="slot.x"
                                      t-att-y="slot.y"
                                      t-att-class="'bale-slot ' + (slot.filled ? 'is-filled' : 'is-empty')"
                                      t-att-style="slot.filled and slot.color ? '--slot-color: ' + slot.color : ''"/>
                                <t t-if="slot.filled and slot.label">
                                    <text t-att-x="slot.x + 13"
                                          t-att-y="slot.y + 13"
                                          text-anchor="middle"
                                          class="bale-slot__label">
                                        <t t-esc="slot.label"/>
                                    </text>
                                </t>
                            </t>
                        </g>

                        <g class="truck-cab">
                            <rect class="cab-body" x="288" y="86" width="58" height="66" rx="14" fill="url(#rmCabGradient)"/>
                            <rect class="cab-window" x="298" y="98" width="26" height="20" rx="4" fill="#e1f2ff"/>
                            <rect class="cab-door" x="324" y="100" width="12" height="34" rx="3" fill="#0d47a1" opacity="0.25"/>
                            <rect class="cab-bumper" x="340" y="124" width="20" height="12" rx="3" fill="#455a64"/>
                        </g>

                        <g class="truck-wheels">
                            <circle class="wheel" cx="120" cy="170" r="18"/>
                            <circle class="wheel" cx="230" cy="170" r="18"/>
                            <circle class="wheel" cx="300" cy="170" r="20"/>
                            <circle class="wheel-hub" cx="120" cy="170" r="8"/>
                            <circle class="wheel-hub" cx="230" cy="170" r="8"/>
                            <circle class="wheel-hub" cx="300" cy="170" r="9"/>
                        </g>

                        <g class="front-detail">
                            <rect x="278" y="122" width="16" height="12" rx="2" fill="#90a4ae" opacity="0.45"/>
                            <circle cx="278" cy="128" r="5" fill="#ffc107" opacity="0.85"/>
                            <circle cx="348" cy="134" r="5" fill="#ffc107" opacity="0.75"/>
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
        const maxWidth = 238;
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
        const slotWidth = 26;
        const slotHeight = 18;
        const gapX = 6;
        const gapY = 4;
        const columns = 7;
        const startX = 52;
        const startY = 66;

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
    background: radial-gradient(circle at top, #e6f1ff 0%, #f7fbff 60%, #ffffff 100%);
    border-radius: 14px;
    padding: 16px;
    border: 1px solid #d4e4f6;
}

.truck-svg {
    width: 100%;
    height: auto;
    display: block;
}

.bale-slot {
    fill: rgba(255, 255, 255, 0.5);
    stroke: rgba(13, 71, 161, 0.15);
    stroke-width: 1;
}

.bale-slot.is-filled {
    fill: var(--slot-color, #4caf50);
    stroke: rgba(0, 0, 0, 0.08);
}

.bale-slot.is-empty {
    fill: rgba(255, 255, 255, 0.35);
    stroke-dasharray: 4 3;
}

.bale-slot__label {
    fill: #ffffff;
    font-size: 11px;
    font-weight: 600;
    pointer-events: none;
}

.truck-wheels .wheel {
    fill: #1f2933;
    stroke: #0b141f;
    stroke-width: 2;
}

.truck-wheels .wheel-hub {
    fill: #cfd8dc;
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
