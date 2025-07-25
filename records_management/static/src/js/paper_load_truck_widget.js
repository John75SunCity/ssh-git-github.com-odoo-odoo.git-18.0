/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class PaperLoadTruckWidget extends Component {
    static template = xml`
        <div class="paper-load-truck-widget">
            <div class="truck-container">
                <svg viewBox="0 0 200 60" class="truck-svg">
                    <!-- Truck Trailer Body -->
                    <rect x="10" y="15" width="140" height="30" fill="#e8f4f8" stroke="#2196F3" stroke-width="2" rx="5"/>
                    
                    <!-- Progress Fill based on load capacity -->
                    <rect x="10" y="15" 
                          t-att-width="Math.min(140, (props.bale_count / 50) * 140)" 
                          height="30" 
                          fill="#4CAF50" 
                          rx="5"
                          opacity="0.8"/>
                    
                    <!-- Truck Cab -->
                    <rect x="150" y="20" width="30" height="20" fill="#2196F3" rx="3"/>
                    
                    <!-- Wheels -->
                    <circle cx="30" cy="50" r="5" fill="#333"/>
                    <circle cx="130" cy="50" r="5" fill="#333"/>
                    <circle cx="165" cy="50" r="5" fill="#333"/>
                    
                    <!-- Load Information Text -->
                    <text x="80" y="32" text-anchor="middle" fill="#000" font-size="12" font-weight="bold">
                        <t t-esc="props.bale_count"/> / 50 bales
                    </text>
                    
                    <!-- Weight Information -->
                    <text x="80" y="42" text-anchor="middle" fill="#555" font-size="10">
                        <t t-esc="Math.round(props.total_weight || 0)"/> lbs
                    </text>
                </svg>
                
                <!-- Load Breakdown by Paper Grade -->
                <div class="load-breakdown mt-2">
                    <div class="row">
                        <div class="col-4 text-center">
                            <div class="grade-indicator">
                                <div class="grade-box" style="background-color: #fff; border: 2px solid #2196F3;">W</div>
                                <small><t t-esc="props.white_count || 0"/> bales</small>
                            </div>
                        </div>
                        <div class="col-4 text-center">
                            <div class="grade-indicator">
                                <div class="grade-box" style="background-color: #FFC107; border: 2px solid #FF9800;">M</div>
                                <small><t t-esc="props.mixed_count || 0"/> bales</small>
                            </div>
                        </div>
                        <div class="col-4 text-center">
                            <div class="grade-indicator">
                                <div class="grade-box" style="background-color: #8BC34A; border: 2px solid #4CAF50;">C</div>
                                <small><t t-esc="props.cardboard_count || 0"/> bales</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Load Status Indicator -->
                <div class="load-status mt-2" t-att-class="'status-' + (props.status || 'draft')">
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="status-text">
                            <t t-if="props.status === 'draft'">📝 Planning</t>
                            <t t-elif="props.status === 'scheduled'">📅 Scheduled</t>
                            <t t-elif="props.status === 'ready_pickup'">🚛 Ready</t>
                            <t t-elif="props.status === 'in_transit'">🚚 In Transit</t>
                            <t t-elif="props.status === 'delivered'">✅ Delivered</t>
                            <t t-elif="props.status === 'paid'">💰 Paid</t>
                            <t t-else="">📦 Load</t>
                        </span>
                        <span class="capacity-percentage">
                            <t t-esc="Math.round((props.bale_count / 50) * 100)"/>% capacity
                        </span>
                    </div>
                </div>
            </div>
        </div>
    `;

    static props = {
        bale_count: { type: Number, optional: true },
        total_weight: { type: Number, optional: true },
        white_count: { type: Number, optional: true },
        mixed_count: { type: Number, optional: true },
        cardboard_count: { type: Number, optional: true },
        status: { type: String, optional: true },
        max_capacity: { type: Number, optional: true }
    };
}

// Register the widget
registry.category("components").add("PaperLoadTruckWidget", PaperLoadTruckWidget);

// CSS for the widget (would normally be in a separate CSS file)
const style = document.createElement('style');
style.textContent = `
.paper-load-truck-widget {
    padding: 15px;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #dee2e6;
}

.truck-svg {
    width: 100%;
    height: 60px;
    background: linear-gradient(180deg, #e3f2fd 0%, #bbdefb 100%);
    border-radius: 5px;
}

.load-breakdown {
    margin-top: 10px;
}

.grade-indicator {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.grade-box {
    width: 24px;
    height: 24px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 12px;
    margin-bottom: 4px;
}

.load-status {
    padding: 8px;
    border-radius: 5px;
    font-size: 12px;
}

.status-draft { background-color: #f8f9fa; border-left: 4px solid #6c757d; }
.status-scheduled { background-color: #e3f2fd; border-left: 4px solid #2196F3; }
.status-ready_pickup { background-color: #fff3e0; border-left: 4px solid #ff9800; }
.status-in_transit { background-color: #e8f5e8; border-left: 4px solid #4caf50; }
.status-delivered { background-color: #e3f2fd; border-left: 4px solid #00bcd4; }
.status-paid { background-color: #e8f5e8; border-left: 4px solid #4caf50; }

.status-text {
    font-weight: 500;
}

.capacity-percentage {
    font-size: 11px;
    color: #666;
}
`;
document.head.appendChild(style);
