/** @odoo-module **/
/**
 * System Flowchart Interactive Client Action
 * Provides a lightweight launcher that guides the user toward building
 * a system diagram and ensures the visualization assets are available.
 */

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class SystemFlowchartClientAction extends Component {
    setup() {
        this.actionService = useService("action");
    }

    onOpenDiagrams() {
        this.actionService.doAction("records_management.action_system_diagram_data");
    }

    onCreateDiagram() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "system.diagram.data",
            view_mode: "form",
            target: "new",
            context: {
                default_name: "Interactive System Overview",
                default_search_type: "all",
            },
        });
    }
}

SystemFlowchartClientAction.template = "records_management.SystemFlowchartClientAction";

registry.category("actions").add(
    "records_management.system_flowchart_interactive",
    SystemFlowchartClientAction
);
