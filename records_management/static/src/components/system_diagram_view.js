/** @odoo-module **/

import { Component, onWillStart, onMounted, onWillUpdateProps, useState } from "@odoo/owl";
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
            diagramId: null,  // Will be set from context or found
            diagramName: '',
            nodeCount: 0,
            edgeCount: 0,
            availableDiagrams: [],  // All diagrams for dropdown selector
        });
        
        onWillStart(async () => {
            // Load all available diagrams for dropdown
            await this.loadAvailableDiagrams();
            // Then load the selected diagram data
            await this.loadDiagramData();
        });
        
        onWillUpdateProps(async (nextProps) => {
            // Reload diagram when props change (e.g., clicking different diagram in list)
            const newActiveId = nextProps.action?.context?.active_id;
            const newResId = nextProps.action?.res_id;
            
            if (newActiveId && newActiveId !== this.state.diagramId) {
                console.log(`Props changed: loading new diagram ID ${newActiveId}`);
                this.state.diagramId = newActiveId;
                await this.loadDiagramData();
            } else if (newResId && newResId !== this.state.diagramId) {
                console.log(`Props changed: loading new diagram ID ${newResId}`);
                this.state.diagramId = newResId;
                await this.loadDiagramData();
            }
        });
        
        onMounted(() => {
            console.log("System Diagram View mounted", this.state);
        });
    }
    
    /**
     * Load all available diagrams for dropdown selector
     */
    async loadAvailableDiagrams() {
        try {
            this.state.availableDiagrams = await this.orm.searchRead(
                'system.diagram.data',
                [],
                ['id', 'name', 'search_type', 'node_count', 'edge_count'],
                { order: 'name' }
            );
            console.log(`Loaded ${this.state.availableDiagrams.length} diagrams for dropdown`);
        } catch (error) {
            console.error('Error loading available diagrams:', error);
            this.state.availableDiagrams = [];
        }
    }
    
    /**
     * Handle diagram selection change from dropdown
     */
    async onDiagramChange(event) {
        const newDiagramId = parseInt(event.target.value, 10);
        if (newDiagramId && newDiagramId !== this.state.diagramId) {
            console.log(`Switching to diagram ID: ${newDiagramId}`);
            this.state.diagramId = newDiagramId;
            await this.loadDiagramData();
        }
    }
    
    /**
     * Load diagram data from the backend
     * 
     * Fetches nodes, edges, and configuration from the system.diagram.data
     * model using the get_diagram_data API method. 
     * 
     * Priority order for diagram selection:
     * 1. active_id from action context (when opening from list/form)
     * 2. res_id from action context (when opening specific record)
     * 3. First available diagram in database
     * 4. Create new default diagram
     */
    async loadDiagramData() {
        this.state.loading = true;
        this.state.error = null;
        
        try {
            // Get diagram ID from context or find/create one
            if (!this.state.diagramId) {
                console.log("Determining which diagram to load...");
                
                // Priority 1: Check action context for active_id
                const activeId = this.props.action?.context?.active_id;
                if (activeId) {
                    this.state.diagramId = activeId;
                    console.log(`Using active_id from context: ${this.state.diagramId}`);
                }
                // Priority 2: Check for res_id in action context
                else if (this.props.action?.res_id) {
                    this.state.diagramId = this.props.action.res_id;
                    console.log(`Using res_id from action: ${this.state.diagramId}`);
                }
                // Priority 3: Use first from available diagrams
                else if (this.state.availableDiagrams.length > 0) {
                    this.state.diagramId = this.state.availableDiagrams[0].id;
                    console.log(`Using first available diagram: ID ${this.state.diagramId}`);
                }
                // Priority 4: No diagrams exist - let backend create one
                else {
                    console.log("No diagrams available, backend will create default");
                }
            }
            
            // Verify diagram still exists before trying to load it
            if (this.state.diagramId) {
                const exists = this.state.availableDiagrams.some(d => d.id === this.state.diagramId);
                if (!exists) {
                    console.warn(`Diagram ID ${this.state.diagramId} no longer exists, will reload list`);
                    this.state.diagramId = null;
                    await this.loadAvailableDiagrams();
                    if (this.state.availableDiagrams.length > 0) {
                        this.state.diagramId = this.state.availableDiagrams[0].id;
                    }
                }
            }
            
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
            
            // Get diagram name for display
            try {
                const diagramRecord = await this.orm.read(
                    'system.diagram.data',
                    [this.state.diagramId],
                    ['name', 'search_type']
                );
                if (diagramRecord.length > 0) {
                    this.state.diagramName = diagramRecord[0].name;
                    console.log(`Loaded diagram: "${this.state.diagramName}" (${diagramRecord[0].search_type})`);
                }
            } catch (readError) {
                // If we can't read the diagram (it was deleted), refresh the list
                console.warn("Could not read diagram record, refreshing available diagrams", readError);
                await this.loadAvailableDiagrams();
                if (this.state.availableDiagrams.length > 0) {
                    // Try loading the first available diagram instead
                    this.state.diagramId = this.state.availableDiagrams[0].id;
                    return await this.loadDiagramData();
                }
            }
            
            // Refresh available diagrams list to sync with any backend changes
            await this.loadAvailableDiagrams();
            
            console.log(`Loaded ${this.state.nodeCount} nodes and ${this.state.edgeCount} edges`);
            
            if (this.state.nodeCount === 0) {
                console.warn("No nodes loaded - diagram will be empty");
            }
            
        } catch (error) {
            console.error('Error loading diagram data:', error);
            
            // Check if it's an "Invalid ids list" error (deleted diagram)
            if (error.message && error.message.includes('Invalid ids list')) {
                console.warn('Diagram was deleted, refreshing available diagrams and trying again');
                this.state.diagramId = null;
                await this.loadAvailableDiagrams();
                
                if (this.state.availableDiagrams.length > 0) {
                    // Retry with first available diagram
                    this.state.diagramId = this.state.availableDiagrams[0].id;
                    return await this.loadDiagramData();
                } else {
                    // No diagrams exist - backend will create one
                    this.state.error = "No diagrams available. Click Regenerate to create a new diagram.";
                }
            } else {
                this.state.error = error.message || "Failed to load diagram data";
                this.notification.add(
                    `Failed to load diagram: ${this.state.error}`,
                    { type: "danger" }
                );
            }
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
            
            // Check if current diagram still exists
            if (this.state.diagramId) {
                const exists = this.state.availableDiagrams.some(d => d.id === this.state.diagramId);
                if (!exists) {
                    console.warn(`Current diagram ${this.state.diagramId} was deleted, refreshing list`);
                    await this.loadAvailableDiagrams();
                    if (this.state.availableDiagrams.length > 0) {
                        this.state.diagramId = this.state.availableDiagrams[0].id;
                    } else {
                        this.state.diagramId = null;
                    }
                }
            }
            
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
            
            // Handle deleted diagram during regeneration
            if (error.message && error.message.includes('Invalid ids list')) {
                this.notification.add(
                    "The diagram was deleted. Loading available diagrams...",
                    { type: "warning" }
                );
                this.state.diagramId = null;
                await this.loadAvailableDiagrams();
                if (this.state.availableDiagrams.length > 0) {
                    this.state.diagramId = this.state.availableDiagrams[0].id;
                    await this.loadDiagramData();
                }
            } else {
                this.notification.add(
                    `Failed to regenerate diagram: ${error.message}`,
                    { type: "danger" }
                );
            }
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
        // Safety check for params and nodes array
        if (!params || !params.nodes || params.nodes.length === 0) {
            return;
        }
        
        const nodeId = params.nodes[0];
        console.log('Node clicked:', nodeId, params);
        
        // Find the clicked node
        const node = this.state.nodes.find(n => n.id === nodeId);
        if (!node) {
            return;
        }
        
        // Extract node metadata (stored in title or custom fields)
        const nodeType = node.group || node.nodeType;
        const recordId = node.recordId;
        const modelName = node.model;
        
        console.log(`Node click - Type: ${nodeType}, Model: ${modelName}, ID: ${recordId}`);
        
        // Handle different node types
        if (nodeType === 'model' && modelName) {
            // Open the model's list view
            this.action.doAction({
                type: 'ir.actions.act_window',
                res_model: modelName,
                views: [[false, 'list'], [false, 'form']],
                name: node.label,
                target: 'current',
            });
            this.notification.add(`Opening ${node.label} records`, { type: "info" });
            
        } else if (nodeType === 'user' && recordId) {
            // Open user form view
            this.action.doAction({
                type: 'ir.actions.act_window',
                res_model: 'res.users',
                res_id: recordId,
                views: [[false, 'form']],
                name: `User: ${node.label}`,
                target: 'new',
            });
            
        } else if (nodeType === 'department' && recordId) {
            // Open department form view
            this.action.doAction({
                type: 'ir.actions.act_window',
                res_model: 'hr.department',
                res_id: recordId,
                views: [[false, 'form']],
                name: `Department: ${node.label}`,
                target: 'new',
            });
            
        } else if (nodeType === 'record' && modelName && recordId) {
            // Open specific record form view
            this.action.doAction({
                type: 'ir.actions.act_window',
                res_model: modelName,
                res_id: recordId,
                views: [[false, 'form']],
                name: node.label,
                target: 'new',
            });
            
        } else if (nodeType === 'field' && modelName) {
            // Open model configuration for field details
            this.action.doAction({
                type: 'ir.actions.act_window',
                res_model: 'ir.model',
                domain: [['model', '=', modelName]],
                views: [[false, 'list'], [false, 'form']],
                name: `Model Fields: ${modelName}`,
                target: 'current',
            });
            this.notification.add(`Viewing fields for ${modelName}`, { type: "info" });
            
        } else {
            // Generic node - just show notification
            this.notification.add(`Clicked: ${node.label}`, { type: "info" });
        }
    }
    
    /**
     * Handle edge click events
     * 
     * @param {Object} params - Click event parameters from vis.js
     */
    onEdgeClick(params) {
        // Safety check for params and edges array
        if (!params || !params.edges || params.edges.length === 0) {
            return;
        }
        
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
