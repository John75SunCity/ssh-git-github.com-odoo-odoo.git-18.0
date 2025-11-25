/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class Warehouse3DView extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        
        this.graphContainer = useRef("graph3d-container");
        
        this.state = useState({
            config_id: this.props.action.params?.config_id || null,
            data: null,
            loading: true,
            error: null,
            selectedContainer: null,
            rotating: false,
            viewMode: 'capacity',
        });
        
        onWillStart(async () => {
            await this.loadData();
        });
        
        onMounted(() => {
            if (this.state.data) {
                this.renderGraph3D();
            }
        });
    }
    
    async loadData() {
        try {
            this.state.loading = true;
            this.state.error = null;
            
            // Call the model method directly via ORM service (like system_flowchart_view.js pattern)
            const config = await this.orm.searchRead(
                'warehouse.3d.view.config',
                [['id', '=', this.state.config_id]],
                ['blueprint_id', 'view_mode', 'color_scheme']
            );
            
            if (!config || config.length === 0) {
                throw new Error('Configuration not found');
            }
            
            // Call the model's method to get visualization data
            const result = await this.orm.call(
                'warehouse.3d.view.config',
                'get_3d_visualization_data',
                [this.state.config_id]
            );
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            this.state.data = result;
            this.state.viewMode = result.view_mode;
            this.state.loading = false;
            
            if (this.graphContainer.el) {
                this.renderGraph3D();
            }
        } catch (error) {
            this.state.error = error.message || "Failed to load warehouse data";
            this.state.loading = false;
            
            this.notification.add(
                this.state.error,
                { type: "danger", title: "Error Loading 3D View" }
            );
        }
    }
    
    renderGraph3D() {
        if (!this.graphContainer.el || !this.state.data) {
            console.warn("Graph container or data not ready");
            return;
        }
        
        const data = this.prepareGraph3DData();
        const options = this.buildGraph3DOptions();
        
        // Clear any existing graph
        this.graphContainer.el.innerHTML = '';
        
        try {
            // Create vis.js Graph3d
            this.graph3d = new vis.Graph3d(this.graphContainer.el, data, options);
            
            // Set up event handlers
            this.setupEventHandlers();
            
            // Add warehouse structure overlay if enabled
            if (this.state.data.settings.show_warehouse_structure) {
                this.addWarehouseStructure();
            }
            
        } catch (error) {
            console.error("Error creating 3D graph:", error);
            this.notification.add(
                "Failed to render 3D visualization: " + error.message,
                { type: "danger" }
            );
        }
    }
    
    prepareGraph3DData() {
        const dataPoints = [];
        const data = this.state.data;
        
        for (const point of data.data_points) {
            // Each container at this location
            const containers = point.containers_data || [];
            
            if (containers.length === 0 && !data.settings.show_empty_locations) {
                continue;
            }
            
            // For each container, create a data point
            containers.forEach((container, index) => {
                // Get container type dimensions (defaultto standard box)
                const boxWidth = 15;  // inches, will be dynamic from type
                const boxDepth = 12;
                const boxHeight = 10;
                
                // Calculate stacking position
                const stackZ = point.z + (boxHeight * index);
                
                dataPoints.push({
                    x: point.x / 12,  // Convert inches to feet for display
                    y: point.y / 12,
                    z: stackZ / 12,
                    
                    // For bar/dot size
                    style: point.value,
                    
                    // Color
                    color: point.color,
                    
                    // Metadata for tooltips and clicks
                    location_id: point.id,
                    location_name: point.name,
                    container_id: container.id,
                    container_name: container.name,
                    container_barcode: container.barcode,
                    customer_name: container.customer,
                    monthly_fee: container.monthly_fee,
                    age_days: container.age_days,
                    has_fsm: container.has_fsm,
                    has_files: container.has_files,
                    file_count: container.file_count,
                });
            });
            
            // If no containers but showing empty, show empty location marker
            if (containers.length === 0) {
                dataPoints.push({
                    x: point.x / 12,
                    y: point.y / 12,
                    z: point.z / 12,
                    style: 0,
                    color: '#CCCCCC',
                    location_id: point.id,
                    location_name: point.name,
                    is_empty: true,
                });
            }
        }
        
        return new vis.DataSet(dataPoints);
    }
    
    buildGraph3DOptions() {
        const blueprint = this.state.data.blueprint;
        const settings = this.state.data.settings;
        
        return {
            width: '100%',
            height: '700px',
            style: this.getStyleForViewMode(),
            showPerspective: true,
            showGrid: settings.show_grid,
            showShadow: false,
            showLegend: settings.show_legend,
            keepAspectRatio: true,
            verticalRatio: 0.5,
            
            // Axis labels
            xLabel: 'Length (feet)',
            yLabel: 'Width (feet)',
            zLabel: 'Height (feet)',
            
            // Value ranges
            xMin: 0,
            xMax: (blueprint.length / 12) + 5,
            yMin: 0,
            yMax: (blueprint.width / 12) + 5,
            zMin: 0,
            zMax: (blueprint.height / 12) + 2,
            
            // Camera position
            cameraPosition: {
                horizontal: settings.camera_horizontal || -0.35,
                vertical: settings.camera_vertical || 0.22,
                distance: settings.camera_distance || 1.8,
            },
            
            // Tooltips
            tooltip: settings.show_tooltips,
            tooltipStyle: {
                content: {
                    background: 'rgba(0, 0, 0, 0.8)',
                    color: '#ffffff',
                    fontSize: '12px',
                    padding: '10px',
                    borderRadius: '4px',
                },
            },
            
            // Animation
            animationInterval: 1000,
            animationPreload: false,
            animationAutoStart: false,
        };
    }
    
    getStyleForViewMode() {
        const mode = this.state.viewMode;
        
        const styles = {
            'capacity': vis.Graph3d.STYLE.BARCOLOR,
            'revenue': vis.Graph3d.STYLE.BARSIZE,
            'customer': vis.Graph3d.STYLE.DOT,
            'age_fifo': vis.Graph3d.STYLE.GRID,
            'age_lifo': vis.Graph3d.STYLE.GRID,
            'fsm_orders': vis.Graph3d.STYLE.DOTCOLOR,
            'metadata': vis.Graph3d.STYLE.DOTSIZE,
            'security': vis.Graph3d.STYLE.BARCOLOR,
            'temperature': vis.Graph3d.STYLE.DOT,
            'file_folders': vis.Graph3d.STYLE.BARSIZE,
        };
        
        return styles[mode] || vis.Graph3d.STYLE.BAR;
    }
    
    setupEventHandlers() {
        // Click handler for containers
        if (this.graph3d && this.graph3d.on) {
            this.graph3d.on('click', (properties) => {
                this.onContainerClick(properties);
            });
        }
    }
    
    addWarehouseStructure() {
        // This would add walls, doors, offices as overlay elements
        // Simplified for now - full implementation would use canvas overlays
        const blueprint = this.state.data.blueprint;
        
        // TODO: Add warehouse structure rendering
        // Could use additional vis components or canvas overlays
    }
    
    async onContainerClick(properties) {
        if (!properties || !properties.point) {
            return;
        }
        
        const point = properties.point;
        
        if (point.is_empty) {
            this.notification.add(
                `Empty Location: ${point.location_name}`,
                { type: "info" }
            );
            return;
        }
        
        // Load full container details
        const containerDetails = await this.rpc("/warehouse/3d/container/" + point.container_id);
        
        if (containerDetails.error) {
            this.notification.add(containerDetails.error, { type: "danger" });
            return;
        }
        
        this.state.selectedContainer = containerDetails;
        
        // Open container form view
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'records.container',
            res_id: point.container_id,
            views: [[false, 'form']],
            target: 'new',
        });
    }
    
    async switchViewMode(mode) {
        this.state.viewMode = mode;
        
        // Update config and reload
        await this.orm.write(
            'warehouse.3d.view.config',
            [this.state.config_id],
            { view_mode: mode }
        );
        
        await this.loadData();
    }
    
    toggleRotation() {
        this.state.rotating = !this.state.rotating;
        
        if (this.state.rotating) {
            this.startRotation();
        } else {
            this.stopRotation();
        }
    }
    
    startRotation() {
        if (this.graph3d) {
            this.graph3d.setOptions({ animationAutoStart: true });
        }
    }
    
    stopRotation() {
        if (this.graph3d) {
            this.graph3d.setOptions({ animationAutoStart: false });
        }
    }
    
    exportToPNG() {
        if (!this.graph3d || !this.graph3d.frame) {
            this.notification.add("Cannot export: visualization not ready", { type: "warning" });
            return;
        }
        
        try {
            const canvas = this.graph3d.frame.canvas;
            const dataURL = canvas.toDataURL('image/png');
            
            const link = document.createElement('a');
            link.href = dataURL;
            link.download = `warehouse-3d-${new Date().toISOString()}.png`;
            link.click();
            
            this.notification.add("3D view exported successfully", { type: "success" });
        } catch (error) {
            this.notification.add("Export failed: " + error.message, { type: "danger" });
        }
    }
    
    async openSettings() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'warehouse.3d.view.config',
            res_id: this.state.config_id,
            views: [[false, 'form']],
            target: 'new',
        });
    }
}

Warehouse3DView.template = "records_management_3d_warehouse.Warehouse3DView";
Warehouse3DView.components = {};

registry.category("actions").add("warehouse_3d_view", Warehouse3DView);
