# Quick Reference: Views and JavaScript Files

## Records Management Module

### Statistics
- **View Files**: 296 XML files
- **JavaScript Files**: 30 files
  - Owl Components: 4 (modern)
  - Legacy Portal: 15 (migrating)
  - Backend Widgets: 8
  - Libraries: 2 (vis.js)

### Key Directories
```
records_management/
├── views/                          # 296 XML view files
│   ├── Accounting & Billing (42)
│   ├── Barcode & Inventory (18)
│   ├── Container Management (28)
│   ├── Chain of Custody (12)
│   ├── Document Retrieval (16)
│   ├── Portal & Customer (26)
│   ├── Shredding Services (18)
│   └── ...and more
│
└── static/src/
    ├── portal_components/          # Modern Owl components
    │   ├── portal_document_center.js
    │   ├── portal_document_center_enhancements.js
    │   ├── portal_inventory.js
    │   └── portal_search.js
    │
    ├── js/                         # Legacy & Backend JavaScript
    │   ├── portal/                 # Portal-specific
    │   │   ├── portal_barcode_management.js
    │   │   ├── portal_document_retrieval.js
    │   │   └── portal_organization_diagram.js
    │   │
    │   ├── Portal Scripts (15 files - legacy)
    │   ├── Backend Widgets (8 files)
    │   └── Specialized (4 files)
    │
    └── lib/vis/                    # External libraries
        ├── vis-network.js
        └── vis-network.min.js
```

## Records Management FSM Module

### Statistics
- **View Files**: 9 XML files
- **JavaScript Files**: 2 files

### Key Files
```
records_management_fsm/
├── views/
│   ├── enhanced_fsm_integration_views.xml
│   ├── fleet_fsm_integration_menus.xml
│   ├── fsm_notification_manager_views.xml
│   ├── fsm_notification_views.xml
│   ├── fsm_reschedule_wizard_views.xml
│   ├── fsm_task_service_line_views.xml
│   ├── fsm_task_views.xml
│   └── mobile_fsm_integration_views.xml
│
└── static/src/
    ├── js/
    │   └── fleet_fsm_dashboard.js
    └── xml/
        └── fleet_fsm_dashboard.xml
```

## Modern Owl Components (Priority Migration)

### Completed ✅
1. **portal_inventory.js** - Interactive inventory management
2. **portal_document_center.js** - Document center main component
3. **portal_search.js** - Search functionality

### In Progress ⏳
4. **portal_quote_generator.js** - Quote generation
5. **portal_signature.js** - Signature capture
6. **intelligent_search.js** - AI-powered search

## Key Integration Points

### Dependencies
- **Core**: base, mail, web, product, stock, account, sale, portal
- **Enterprise**: sms, maintenance, point_of_sale, barcodes, industry_fsm, sign, survey, documents, helpdesk
- **FSM Module**: records_management, project, fleet

### External Libraries
- **vis.js**: Network and hierarchical visualizations

## Development Quick Start

### Creating New Views
```xml
<!-- Pattern: {model_name}_view_{type} -->
<record id="my_model_view_form" model="ir.ui.view">
    <field name="name">my.model.view.form</field>
    <field name="model">my.model</field>
    <field name="arch" type="xml">
        <!-- View definition -->
    </field>
</record>
```

### Creating Owl Components
```javascript
/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class MyComponent extends Component {
    setup() {
        this.state = useState({ /* ... */ });
    }
}

registry.category("public_components").add("my_component", MyComponent);
```

## File Reference Quick Lookup

### By Function

**Billing**: 42 view files (advanced_billing_*.xml, records_billing_*.xml)
**Containers**: 28 view files (container_*.xml, records_container_*.xml)
**Documents**: 16 view files (document_retrieval_*.xml, file_retrieval_*.xml)
**Shredding**: 18 view files (shred_*.xml, shredding_*.xml)
**Portal**: 26 view files (portal_*.xml, customer_*.xml)
**Chain of Custody**: 12 view files (chain_of_custody_*.xml, naid_*.xml)

### By Technology

**Owl Components**: 4 files in portal_components/
**Legacy Portal**: 15 files in js/ (marked for migration)
**Backend Widgets**: 8 files in js/ (field widgets, visualizations)
**External Libs**: 2 files in lib/vis/

## Common Patterns

### View Loading Order
1. Security files (security/*.xml, ir.model.access.csv)
2. Root menus (records_management_root_menus.xml)
3. Data files (data/*.xml)
4. Report actions (report/*.xml)
5. View files (views/*.xml)
6. Child menus (views/*_menus.xml)

### Asset Loading
```python
"assets": {
    "web.assets_backend": [
        # Backend components
    ],
    "web.assets_frontend": [
        # Portal/public components
    ]
}
```

## See Also

- **Full Documentation**: VIEWS_AND_JS_FILES_OUTLINE.md
- **Handbook**: handbook/views-and-templates-mapping.md
- **Manifest Files**: 
  - records_management/__manifest__.py
  - records_management_fsm/__manifest__.py
