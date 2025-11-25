/** @odoo-module **/

import { Component, onWillStart, onMounted, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { NetworkDiagram } from "@web_vis_network/components/network_diagram";

/**
 * System Diagram View Component
 * 
 * Displays the Records Management system architecture using the web_vis_network
 * module's NetworkDiagram component. Shows relationships between models, users,
 * departments, and system components.
 * 
 * This Owl component replaces the old embedded HTML approach and provides:
 * - Better debugging with browser DevTools
 * - Proper Odoo 18 architecture patterns
 * - Clean separation of data (Python) and presentation (JavaScript)
 * - Integration with the reusable web_vis_network module
 */
export class SystemDiagramView extends Component {
    static template = "records_management.SystemDiagramView";
    static components = { NetworkDiagram };
    
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        
        this.state = useState({
            nodes: [],
            edges: [],
            options: {},
            loading: true,
            error: null,
            diagramId: this.props.action?.context?.active_id || 1,
            nodeCount: 0,
            edgeCount: 0,
        });
        
        onWillStart(async () => {
            await this.loadDiagramData();
        });
        
        onMounted(() => {
            console.log("System Diagram View mounted", this.state);
        });
    }
    
    /**
     * Load diagram data from the backend
     * 
     * Fetches nodes, edges, and configuration from the system.diagram.data
     * model using the get_diagram_data API method.
     */
    async loadDiagramData() {
        this.state.loading = true;
        this.state.error = null;
        
        try {
            console.log(`Loading diagram data for ID: ${this.state.diagramId}`);
            
            const result = await this.orm.call(
                'system.diagram.data',
                'get_diagram_data',
                [this.state.diagramId],
            );
            
            console.log("Backend response:", result);
            
            // Parse JSON data from backend
            const nodesData = result.nodes_data || '[]';
            const edgesData = result.edges_data || '[]';
            const configData = result.diagram_config || '{}';
            
            this.state.nodes = JSON.parse(nodesData);
            this.state.edges = JSON.parse(edgesData);
            this.state.options = JSON.parse(configData);
            
            this.state.nodeCount = this.state.nodes.length;
            this.state.edgeCount = this.state.edges.length;
            
            console.log(`Loaded ${this.state.nodeCount} nodes and ${this.state.edgeCount} edges`);
            
            if (this.state.nodeCount === 0) {
                console.warn("No nodes loaded - diagram will be empty");
            }
            
        } catch (error) {
            console.error('Error loading diagram data:', error);
            this.state.error = error.message || "Failed to load diagram data";
            this.notification.add(
                `Failed to load diagram: ${this.state.error}`,
                { type: "danger" }
            );
        } finally {
            this.state.loading = false;
        }
    }
    
    /**
     * Regenerate diagram data
     * 
     * Calls the backend to recompute the diagram data, then reloads
     * the visualization.
     */
    async onRegenerate() {
        this.state.loading = true;
        
        try {
            console.log("Regenerating diagram data...");
            
            await this.orm.call(
                'system.diagram.data',
                'action_regenerate_diagram',
                [[this.state.diagramId]],
            );
            
            await this.loadDiagramData();
            
            this.notification.add(
                `Diagram regenerated: ${this.state.nodeCount} nodes, ${this.state.edgeCount} edges`,
                { type: "success" }
            );
            
        } catch (error) {
            console.error('Error regenerating diagram:', error);
            this.notification.add(
                `Failed to regenerate diagram: ${error.message}`,
                { type: "danger" }
            );
        } finally {
            this.state.loading = false;
        }
    }
    
    /**
     * Handle node click events
     * 
     * @param {Object} params - Click event parameters from vis.js
     */
    onNodeClick(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            console.log('Node clicked:', nodeId, params);
            
            // Find the clicked node
            const node = this.state.nodes.find(n => n.id === nodeId);
            if (node) {
                this.notification.add(
                    `Clicked: ${node.label}`,
                    { type: "info" }
                );
            }
            
            // TODO: Add custom logic for different node types
            // e.g., open model record, show user details, etc.
        }
    }
    
    /**
     * Handle edge click events
     * 
     * @param {Object} params - Click event parameters from vis.js
     */
    onEdgeClick(params) {
        if (params.edges.length > 0) {
            const edgeId = params.edges[0];
            console.log('Edge clicked:', edgeId, params);
            
            // Find the clicked edge
            const edge = this.state.edges.find(e => e.id === edgeId);
            if (edge) {
                const fromNode = this.state.nodes.find(n => n.id === edge.from);
                const toNode = this.state.nodes.find(n => n.id === edge.to);
                
                if (fromNode && toNode) {
                    this.notification.add(
                        `Connection: ${fromNode.label} → ${toNode.label}`,
                        { type: "info" }
                    );
                }
            }
        }
    }
    
    /**
     * Export diagram to image
     * 
     * TODO: Implement diagram export functionality
     */
    async onExport() {
        this.notification.add(
            "Export functionality coming soon",
            { type: "info" }
        );
    }
}

// Register as a client action
registry.category("actions").add("system_diagram_view", SystemDiagramView);
