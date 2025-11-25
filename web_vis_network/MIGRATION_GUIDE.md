# Migration Guide: System Diagram → web_vis_network Module

## Overview

This guide shows how to migrate your existing System Diagram implementation to use the new `web_vis_network` module for better performance, maintainability, and Odoo 18 compliance.

## Current Implementation Issues

Your current system diagram has these problems:

1. **CDN Dependency**: Loading vis.js from CDN in HTML field
2. **Inline JavaScript**: Complex JS embedded in Python-generated HTML
3. **No Caching**: Library loaded fresh on every diagram generation
4. **Hard to Debug**: Embedded code makes debugging difficult
5. **Not Odoo 18 Compliant**: Doesn't use modern Owl components

## Migration Steps

### Step 1: Update records_management Manifest

Add dependency on `web_vis_network`:

```python
# records_management/__manifest__.py

'depends': [
    'base',
    'product',
    'stock',
    # ... other dependencies
    'web_vis_network',  # Add this line
],
```

### Step 2: Download vis.js Library

Follow instructions in `web_vis_network/static/lib/vis-network/DOWNLOAD_INSTRUCTIONS.md`

```bash
cd web_vis_network/static/lib/vis-network/

# Download files
curl -o vis-network.min.js https://cdn.jsdelivr.net/npm/vis-network@9.1.9/standalone/umd/vis-network.min.js
curl -o vis-network.min.css https://cdn.jsdelivr.net/npm/vis-network@9.1.9/dist/dist/vis-network.min.css
```

### Step 3: Create Owl Component for System Diagram

Create new file: `records_management/static/src/components/system_diagram.js`

```javascript
/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { NetworkDiagram } from "@web_vis_network/components/network_diagram";

export class SystemDiagramView extends Component {
    static template = "records_management.SystemDiagramView";
    static components = { NetworkDiagram };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            nodes: [],
            edges: [],
            options: {},
            loading: true,
        });

        onWillStart(async () => {
            await this.loadDiagramData();
        });
    }

    async loadDiagramData() {
        this.state.loading = true;

        // Call your existing Python method to get data
        const result = await this.orm.call(
            'system.diagram.data',
            'get_diagram_data',
            [this.props.action.context.active_id || 1],
        );

        this.state.nodes = JSON.parse(result.nodes_data || '[]');
        this.state.edges = JSON.parse(result.edges_data || '[]');
        this.state.options = JSON.parse(result.diagram_config || '{}');
        this.state.loading = false;
    }

    async onRegenerate() {
        await this.orm.call(
            'system.diagram.data',
            'action_regenerate_diagram',
            [this.props.action.context.active_id || 1],
        );
        await this.loadDiagramData();
    }

    onNodeClick(nodeId, params) {
        console.log('Node clicked:', nodeId, params);
        // Add your custom logic here
    }
}

registry.category("actions").add("system_diagram_view", SystemDiagramView);
```

### Step 4: Create Template

Create new file: `records_management/static/src/xml/system_diagram.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="records_management.SystemDiagramView">
        <div class="o_system_diagram_view">
            <div class="o_control_panel">
                <div class="o_cp_buttons">
                    <button class="btn btn-primary" t-on-click="onRegenerate">
                        <i class="fa fa-refresh"/> Regenerate Diagram
                    </button>
                </div>
            </div>

            <div class="o_content">
                <div t-if="state.loading" class="o_loading">
                    <i class="fa fa-spinner fa-spin fa-3x"/>
                    <p>Loading diagram...</p>
                </div>

                <NetworkDiagram t-else=""
                    nodes="state.nodes"
                    edges="state.edges"
                    options="state.options"
                    height="800"
                    onNodeClick.bind="onNodeClick"/>
            </div>
        </div>
    </t>
</templates>
```

### Step 5: Update records_management Manifest

Add the new assets:

```python
# records_management/__manifest__.py

'assets': {
    'web.assets_backend': [
        # ... existing assets
        'records_management/static/src/components/system_diagram.js',
        'records_management/static/src/xml/system_diagram.xml',
    ],
},
```

### Step 6: Simplify Python Model

Update `system_diagram_data.py` to remove HTML generation:

```python
# records_management/models/system_diagram_data.py

from odoo import api, fields, models
import json

class SystemDiagramData(models.Model):
    _name = 'system.diagram.data'
    _description = 'System Architecture Diagram Data'

    # Keep existing fields but remove diagram_html
    nodes_data = fields.Text('Nodes Data', compute='_compute_diagram_data')
    edges_data = fields.Text('Edges Data', compute='_compute_diagram_data')
    diagram_config = fields.Text('Diagram Configuration', compute='_compute_diagram_config')

    # Remove _compute_diagram_html method - no longer needed!

    @api.model
    def get_diagram_data(self, diagram_id):
        """API method for Owl component to fetch data"""
        diagram = self.browse(diagram_id)
        return {
            'nodes_data': diagram.nodes_data,
            'edges_data': diagram.edges_data,
            'diagram_config': diagram.diagram_config,
        }

    def action_regenerate_diagram(self):
        """Simplified regeneration - just invalidate cache"""
        self.ensure_one()
        self._invalidate_cache(['nodes_data', 'edges_data', 'diagram_config'])
        return True  # Component will reload data via get_diagram_data
```

### Step 7: Update Client Action

```xml
<!-- records_management/views/system_diagram_data_views.xml -->

<record id="action_system_diagram_view" model="ir.actions.client">
    <field name="name">System Architecture Diagram</field>
    <field name="tag">system_diagram_view</field>
    <field name="target">current</field>
</record>

<menuitem id="menu_system_diagram"
          name="System Diagram"
          action="action_system_diagram_view"
          parent="base.menu_administration"
          sequence="100"/>
```

## Benefits After Migration

### ✅ Performance
- vis.js cached by Odoo's asset pipeline
- No CDN requests (faster page load)
- Proper minification and bundling

### ✅ Maintainability
- Clean separation: Python (data) vs JavaScript (presentation)
- Easier to debug (proper browser DevTools support)
- Can use hot-reload in development mode

### ✅ Odoo 18 Compliance
- Uses modern Owl components
- Follows Odoo's asset management best practices
- Proper service usage (ORM, action)

### ✅ Reusability
- NetworkDiagram component can be used anywhere
- Other modules can use web_vis_network
- Easy to create multiple diagram types

### ✅ Extensibility
- Easy to add custom interactions
- Can patch component in other modules
- Service-based architecture

## Testing the Migration

1. Install `web_vis_network` module
2. Update `records_management` module
3. Clear browser cache
4. Open System Diagram menu
5. Click "Regenerate Diagram"
6. Verify diagram displays correctly

## Debugging

Enable debug mode and check browser console:

```javascript
// In browser console
odoo.__DEBUG__.services  // Check if services are available
vis  // Should show vis.js library object
```

## Common Issues

### Issue: "vis is not defined"
**Solution**: Ensure vis.js files are downloaded and assets regenerated

### Issue: Component not rendering
**Solution**: Check that action tag matches registry name: `system_diagram_view`

### Issue: Data not loading
**Solution**: Check Python method `get_diagram_data` exists and returns correct format

## Rollback Plan

If migration fails, you can temporarily keep both implementations:

1. Keep old HTML field approach for production
2. Test new Owl component in staging
3. Gradually migrate once stable

## Next Steps

Once migrated, you can:

1. Add interactive features (zoom, pan, search)
2. Create multiple diagram types (org chart, flow chart)
3. Export diagrams to image/PDF
4. Add real-time updates via bus service
5. Create custom node/edge types with HTML templates
