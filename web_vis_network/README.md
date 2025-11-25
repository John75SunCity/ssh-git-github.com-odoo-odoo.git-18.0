# Vis.js Network Library for Odoo

![Version](https://img.shields.io/badge/version-18.0.1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-LGPL--3-green.svg)

## Overview

This module provides the **vis.js network visualization library** for use in Odoo 18.0. It properly bundles the vis.js library as an Odoo asset, making it available for any module that needs advanced network/graph visualizations.

## Why Use This Module?

### ✅ **Benefits**
- **Proper Asset Management**: vis.js is bundled correctly in Odoo's asset pipeline
- **No CDN Dependencies**: Library served locally (with CDN fallback option)
- **Reusable**: Any module can depend on it without duplicating the library
- **Performance**: Assets are cached and minified by Odoo
- **Version Control**: Library version is locked and managed

### ❌ **Without This Module**
- Loading from CDN in HTML fields (unreliable, slow, network dependent)
- Duplicate library files in multiple modules
- No proper caching or asset optimization
- Harder to maintain and upgrade

## Installation

1. Copy this module to your Odoo addons directory
2. Update the apps list
3. Install "Vis.js Network Library" module

## Usage

### In Your Module's Manifest

Add `web_vis_network` to your dependencies:

```python
{
    'name': 'My Custom Module',
    'depends': ['web', 'web_vis_network'],
    # ...
}
```

### In Owl Components (Recommended for Odoo 18)

Create a custom Owl component that uses vis.js:

```javascript
/** @odoo-module **/

import { Component, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class NetworkDiagram extends Component {
    setup() {
        this.containerRef = useRef("network-container");
        
        onMounted(() => {
            this.renderNetwork();
        });
    }
    
    renderNetwork() {
        const container = this.containerRef.el;
        const nodes = new vis.DataSet([
            { id: 1, label: 'Node 1' },
            { id: 2, label: 'Node 2' },
            { id: 3, label: 'Node 3' }
        ]);
        
        const edges = new vis.DataSet([
            { from: 1, to: 2 },
            { from: 1, to: 3 }
        ]);
        
        const data = { nodes, edges };
        const options = {
            physics: {
                enabled: true,
                barnesHut: {
                    gravitationalConstant: -2000,
                    springLength: 200
                }
            }
        };
        
        new vis.Network(container, data, options);
    }
}

NetworkDiagram.template = "my_module.NetworkDiagramTemplate";

registry.category("actions").add("network_diagram", NetworkDiagram);
```

### In XML Views

Create a QWeb template for your component:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="my_module.NetworkDiagramTemplate">
        <div class="o_network_diagram">
            <div t-ref="network-container" style="height: 600px; border: 1px solid #ccc;"/>
        </div>
    </t>
</templates>
```

### As a Client Action

Register as a client action to open from menus:

```xml
<record id="action_network_diagram" model="ir.actions.client">
    <field name="name">Network Diagram</field>
    <field name="tag">network_diagram</field>
</record>

<menuitem id="menu_network_diagram"
          name="Network Diagram"
          action="action_network_diagram"
          parent="base.menu_custom"
          sequence="10"/>
```

## Advanced: Widget Field Integration

You can also create a custom widget for use in form views:

```javascript
/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, useRef } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class FieldNetworkWidget extends Component {
    setup() {
        this.containerRef = useRef("network");
        
        onMounted(() => {
            this.renderNetwork();
        });
    }
    
    renderNetwork() {
        const data = JSON.parse(this.props.value || '{"nodes":[],"edges":[]}');
        const container = this.containerRef.el;
        
        const nodes = new vis.DataSet(data.nodes);
        const edges = new vis.DataSet(data.edges);
        
        new vis.Network(container, { nodes, edges }, this.getOptions());
    }
    
    getOptions() {
        return {
            physics: { enabled: true },
            layout: { hierarchical: false }
        };
    }
}

FieldNetworkWidget.template = "web_vis_network.FieldNetworkWidget";
FieldNetworkWidget.props = {
    ...standardFieldProps,
};

registry.category("fields").add("network_widget", FieldNetworkWidget);
```

Then use in your model:

```python
class MyModel(models.Model):
    _name = 'my.model'
    
    network_data = fields.Text('Network Data')
```

And in your form view:

```xml
<field name="network_data" widget="network_widget"/>
```

## Library Information

**Library**: vis.js Network  
**Version**: 9.1.9 (update as needed)  
**License**: Apache 2.0 / MIT  
**Website**: https://visjs.org/  
**GitHub**: https://github.com/visjs/vis-network

## File Structure

```
web_vis_network/
├── __init__.py
├── __manifest__.py
├── README.md
├── static/
│   └── lib/
│       └── vis-network/
│           ├── vis-network.min.js
│           ├── vis-network.min.css
│           └── img/  (optional: network images)
└── static/src/  (optional: your custom JS components)
    ├── components/
    │   └── network_diagram.js
    └── xml/
        └── network_diagram.xml
```

## Download vis.js

Download the latest vis.js network library from:
https://github.com/visjs/vis-network/releases

Extract and place files in:
- `static/lib/vis-network/vis-network.min.js`
- `static/lib/vis-network/vis-network.min.css`

## Benefits for Your System Diagram

For your existing system diagram in `records_management`:

1. **Add dependency**:
```python
# records_management/__manifest__.py
'depends': [..., 'web_vis_network'],
```

2. **Simplify your code** - Remove CDN loading:
```python
# BEFORE (in system_diagram_data.py)
template = """
<script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
"""

# AFTER - Library already loaded via asset bundle!
template = """
<div id="{container_id}" style="height: 800px;"></div>
<script type="text/javascript">
    // vis is already available globally
    var network = new vis.Network(container, data, options);
</script>
"""
```

3. **Better performance**: Library cached, no external requests
4. **Offline capable**: No CDN dependency

## Upgrading vis.js

To upgrade to a new version:

1. Download new version from GitHub releases
2. Replace files in `static/lib/vis-network/`
3. Update version in `__manifest__.py`
4. Restart Odoo and regenerate assets

## License

LGPL-3 (Odoo module wrapper)  
Apache 2.0 / MIT (vis.js library)

## Support

For vis.js documentation: https://visjs.github.io/vis-network/docs/network/  
For Odoo integration issues: Create an issue in your repository

## Credits

- **Vis.js Team**: https://github.com/visjs
- **Odoo Framework**: https://www.odoo.com
