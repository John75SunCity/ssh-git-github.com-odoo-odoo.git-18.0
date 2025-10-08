### Retention Policy View Modernization (Refactor Notes)

The `records.retention.policy` model was refactored to eliminate dozens of legacy boolean mirror fields
(`is_expired`, `is_under_legal_hold`, approval/publication/review duplicates) in favor of authoritative
selection fields and a single derived review axis.

Key changes:

* Removed deprecated boolean mirror flags (approval / publication / lifecycle / review derivatives)
* Added computed fields: `review_state`, `retention_display`, `overdue_days`, `is_latest_version`
* Added workflow selection axes: `approval_state`, `publication_state`, `lifecycle_state`, `version_type`
* Added supersession fields: `supersedes_id`, `superseded_by_id`, `effective_date`, `ineffective_date`
* Added smart buttons: Documents, Child Policies
* Updated tree/search/kanban/form views to rely on selection fields instead of removed booleans

Search filters now include:

* Review lifecycle: Expired, Overdue, Pending Review (via `review_state`)
* Workflow: Approved (`approval_state`), Published (`publication_state`)
* Core state: Draft, Active, Archived
* Flags: Template, Default, Legal Hold

Group By options now include:

* `state`, `approval_state`, `publication_state`, `review_state`, `document_type_id`, `department_id`, `destruction_method`, `compliance_status`

Decorations:

* Warning highlight when `review_state` in (`overdue`, `expired`)
* Muted archived, success active, info draft in list view

Migration guidance:

Any prior domain or code referencing removed booleans must now pivot to:

* Expiration: `review_state in ('expired','overdue')` or compare dates directly (`expiration_date`, `next_review_date`)
* Approval indicators: `approval_state` selection values
* Publication indicators: `publication_state` selection values
* Legal hold: `is_legal_hold`

Rationale:

The consolidation reduces field proliferation, avoids divergent truth sources, and simplifies UI logic while
retaining full analytical capability via multi-axis workflow states.

### Migration Helper Script

A migration utility is provided to locate deprecated boolean mirror usages removed during the refactor:

Run:

```bash
python3 development-tools/migration/migration_scan_retention_policy_booleans.py --root records_management
```

Output columns:

* File – truncated path
* Line – line number of occurrence
* Token – deprecated boolean found
* Suggestion – recommended replacement expression or field

Common replacements:

* `is_expired` -> `review_state = 'expired'`
* `is_overdue` -> `review_state = 'overdue'`
* `is_pending_review` -> `review_state = 'pending_review'`
* `is_approved` -> `approval_state = 'approved'`
* `is_published` -> `publication_state = 'published'`
* `is_locked` -> `lifecycle_state = 'locked'`
* `is_under_legal_hold` -> `is_legal_hold`

If no results are reported, the codebase is free of legacy retention policy boolean dependencies.

# Records Management System - Enterprise Edition for Odoo 19.0

## 🏆 **ENTERPRISE-GRADE DOCUMENT MANAGEMENT SYSTEM** 🏆

> **MASSIVE SCALE**: 102 Python Models | 51 XML Views | 1400+ Fields | 77 Data Files

A comprehensive, enterprise-grade physical document management system with advanced AI analytics, NAID AAA compliance, modern customer portal, and seamless POS integration.

## 📊 **IMPRESSIVE STATISTICS**

- **🔧 102 Python Models** - Comprehensive business logic coverage
- **🎨 51 XML Views** - Rich, modern user interfaces
- **📋 1400+ Fields** - Detailed data capture and analytics
- **📄 77 Data Files** - Complete configuration and demo data
- **🎛️ 5 Controllers** - Advanced web integration
- **🧙 13 Wizards** - User-friendly guided processes
- **💻 15 Static Assets** - Modern frontend components

## 🎯 **VERSION INFORMATION**

**Current Version:** 19.0.0.1
**Major Update:** Enterprise Features & AI Analytics
**Compatibility:** Odoo 19.0
**Last Updated:** July 2025

## 🚀 **ENTERPRISE FEATURES**

### 🤖 **AI-Ready Analytics Engine**

- **Sentiment Analysis**: Advanced customer feedback processing with ML extensibility
- **Predictive Analytics**: Smart document destruction scheduling
- **Risk Assessment**: Automated compliance scoring and alerts
- **Business Intelligence**: Real-time KPIs and performance metrics
- **Smart Prioritization**: AI-driven task and request prioritization

### 🔒 **NAID AAA Compliance & Security**

- **Complete Audit Trails**: Encrypted, tamper-proof logging system
- **Chain of Custody**: Full document lifecycle tracking
- **Digital Signatures**: E-signature integration for service requests
- **Access Control**: Multi-level security with department isolation
- **Destruction Certificates**: Verified, legally-compliant documentation

### 🌐 **Advanced Customer Portal**

- **Modern AJAX Interface**: Real-time updates without page refresh
- **Centralized Document Center**: Unified access to all customer documents
- **Self-Service Capabilities**: Quote generation, service requests, inventory management
- **Interactive Dashboards**: Custom analytics and performance insights
- **Mobile-Responsive**: Full functionality on all devices

### 💼 **Comprehensive Business Operations**

#### **Document Management**

- Physical document box tracking with intelligent location management
- Advanced barcode classification system (auto-detects 5-15 character patterns)
- Document retention policy automation with compliance alerts
- Digital copy management with secure access controls
- Advanced search and filtering capabilities

#### **Service Operations**

- **Shredding Services**: Documents, hard drives, uniforms, paper
- **Document Retrieval**: Work order management with automated pricing
- **Paper Recycling**: Weight tracking, baling, trailer load optimization
- **Visitor Management**: Walk-in customer processing with POS integration
- **Field Service**: Mobile-ready task management

### �️ **POS Integration Modules**

- **module_pos_discount**: Advanced discount management for walk-in services
- **module_pos_loyalty**: Customer loyalty programs with points tracking
- **module_pos_mercury**: Payment processing integration for secure transactions
- **module_pos_reprint**: Receipt reprinting capabilities for customer convenience
- **module_pos_restaurant**: Restaurant-specific features for food service integration

### 📊 **Enterprise Reporting & Analytics**

- **Real-Time Dashboards**: KPI monitoring with live performance metrics
- **Custom Report Generation**: Excel, PDF, CSV export with scheduling
- **Compliance Audit Reports**: Drill-down capabilities for detailed analysis
- **Revenue Analytics**: Profit margin analysis and forecasting
- **Advanced Business Intelligence**: Trend analysis and predictive insights

### 🔧 **Advanced Technical Architecture**

- **Modern Frontend**: Vue.js components with progressive web app capabilities
- **RESTful API**: Comprehensive webhook support for third-party integrations
- **Mobile-Responsive**: Touch-friendly interface optimized for all devices
- **Advanced Search**: Elasticsearch integration for lightning-fast queries
- **Cloud Integration**: AWS S3, Azure Blob storage support

## 🎯 **CORE MODELS & CAPABILITIES**

### **📦 Document & Box Management (15+ Models)**

- `records.box` - Advanced box tracking with location intelligence
- `records.document` - Complete document lifecycle management
- `records.box.movement` - Chain of custody tracking
- `records.retention.policy` - Automated compliance management
- `records.location` - GPS-enabled location tracking

### **🔒 Security & Compliance (12+ Models)**

- `naid.audit.log` - Encrypted audit trail system
- `chain.of.custody` - Tamper-proof custody tracking
- `naid.compliance` - Comprehensive compliance management
- `records.access.log` - Detailed access control logging
- `records.approval.workflow` - Multi-level approval processes

### **💼 Business Operations (25+ Models)**

- `shredding.service` - Complete destruction service management
- `paper.bale` - Weight tracking and optimization
- `trailer.load` - Load planning with mathematical optimization
- `portal.request` - Customer service request management
- `customer.feedback` - AI-ready sentiment analysis

### **🌐 Customer Portal & Integration (20+ Models)**

- `portal.feedback` - Advanced feedback system with sentiment analysis
- `customer.inventory.report` - Real-time inventory dashboards
- `transitory.items` - Dynamic customer inventory management
- `field.label.customization` - Personalized field configurations
- `visitor.pos.wizard` - Seamless walk-in customer processing

### **📊 Analytics & Reporting (15+ Models)**

- `records.billing` - Advanced billing automation
- `performance.analytics` - Business intelligence metrics
- `compliance.reporting` - Automated audit report generation
- `revenue.optimization` - Profit margin analysis
- `predictive.analytics` - AI-driven forecasting

### **🔧 System Integration (15+ Models)**

- `pos.config` - Point of sale integration management
- `fsm.task` - Field service management integration
- `sms.notification` - Multi-channel communication
- `email.automation` - Automated workflow notifications
- `api.integration` - Third-party system connectivity

## 💡 **INNOVATION HIGHLIGHTS**

### **🤖 AI & Machine Learning Ready**

- Sentiment analysis engine extensible with PyTorch
- Predictive document destruction scheduling
- Smart priority assignment based on ML algorithms
- Automated risk assessment and compliance scoring
- Advanced pattern recognition for document classification

### **⚡ Performance & Scalability**

- **1000+ Concurrent Users**: Enterprise-grade performance
- **Millions of Records**: Optimized for massive scale
- **Sub-Second Response**: Advanced database optimization
- **Background Processing**: Heavy operations handled asynchronously
- **Smart Caching**: Intelligent memory management

### **🔐 Enterprise Security**

- Multi-tenant architecture with complete data isolation
- Advanced encryption for sensitive document handling
- Role-based access control with granular permissions
- Comprehensive audit trails for compliance requirements
- Secure API endpoints with authentication and rate limiting
'product', 'stock', 'account', 'sale', 'website'

# Optional Features

'point_of_sale'  # For walk-in services
'project'        # For work order management
'survey'         # For customer feedback
'hr'            # For employee management
'sign'          # For electronic signatures

### Python Dependencies

```bash
pip install qrcode Pillow cryptography
# Optional: pip install pulp torch  # For optimization and AI features
```

## 🔧 Installation Instructions

### Step 1: Dependencies

Ensure all required Odoo modules are installed first:

1. Install core modules: `base`, `mail`, `web`, `portal`
2. Install business modules: `product`, `stock`, `account`, `sale`
3. Install optional modules as needed

### Step 2: Module Installation

1. Place the `records_management` folder in your Odoo addons directory
2. Update the addons list: `Settings > Apps > Update Apps List`
3. Install the module: `Apps > Search "Records Management" > Install`

### Step 3: Initial Configuration

1. Configure basic settings: `Records > Configuration > Settings`
2. Set up locations: `Records > Configuration > Locations`
3. Configure retention policies: `Records > Configuration > Retention Policies`
4. Set up products and services: `Records > Configuration > Products`

## 🏗️ Module Structure

### Core Models

- **Records Box**: Physical document container tracking
- **Records Document**: Individual document management
- **Records Location**: Storage location hierarchy
- **Records Retention Policy**: Document lifecycle management

### Service Models

- **Shredding Services**: Destruction work orders and inventory
- **Paper Recycling**: Baling and shipment management
- **Document Retrieval**: Request and fulfillment tracking
- **Visitor Management**: Walk-in customer processing

### Billing & Portal

- **Advanced Billing**: Automated rate calculation and invoicing

### Records Profile (User Role Abstraction)

The module adds a high-level "Records Profile" selector on the User form (res.users) to simplify access provisioning.

Selection values map to security groups as follows (implied groups handle cascading privileges):

| Profile Key | Label                       | Primary Group XML ID                                        | Base Tier |
|-------------|-----------------------------|--------------------------------------------------------------|-----------|
| records_admin | Records Admin             | records_management.group_records_admin                      | Internal  |
| records_user  | Records User              | records_management.group_records_user                       | Internal  |
| portal_company_admin | Portal Company Admin | records_management.group_portal_company_admin             | Portal    |
| portal_department_admin | Portal Department Admin | records_management.group_portal_department_admin     | Portal    |
| portal_user | Portal User                 | records_management.group_portal_department_user             | Portal    |
| portal_read_only | Portal Read Only       | records_management.group_portal_readonly_employee           | Portal    |

Behavior Rules:
* Internal profiles enforce membership in base.group_user and remove base.group_portal.
* Portal profiles enforce membership in base.group_portal and remove base.group_user.
* Switching profiles removes any prior Records profile groups to avoid privilege leakage.
* Hierarchical implied_ids already defined in security XML continue to cascade permissions (e.g., Admin → Manager → User).

Implementation Details:
* Field: res.users.records_user_profile (selection, tracking enabled)
* Synchronization executed post-create and on write when the profile changes.
* Logic lives in models/res_users.py (_apply_records_user_profile) and assigns groups atomically with (6, 0, ids) to prevent residual links.

Customization:
* To introduce a new tier, define a new res.groups record, add its XML ID to the mapping dictionaries in models/res_users.py, and extend the selection field choices.
* For per-company overrides, inherit res.users and override _apply_records_user_profile adding contextual conditions.

- **Portal Requests**: Customer self-service functionality
- **Feedback System**: Customer satisfaction tracking
- **Certificate Management**: Secure document downloads

### Portal Barcode Generation (New Feature)

This module introduces a lightweight, extensible generic barcode model powering on-demand barcode creation from the portal UI.

Key components:

* Model: `portal.barcode` (mail.thread, activity) – stores generated barcodes with lifecycle state
* Sequence: `ir.sequence` code `portal.barcode` (prefix `PB`, padding 7, no_gap) – ensures uniqueness
* JSON Route: `/records_management/portal/generate_barcode` (POST, `auth="user"`) – returns newly created record data + optional rendered row fragment
* QWeb Fragment: `portal_barcode_row.xml` – server-rendered `<tr>` snippet for progressive enhancement
* Frontend JS: `static/src/js/portal/portal_barcode_management.js` – dual implementation (Odoo widget + vanilla fallback) handling spinner, optimistic insertion, and graceful degradation
* Access Control: Records User (create/read/update), Records Manager (full CRUD) – intentionally excludes anonymous/public users

Response Schema (successful JSON call):

```json
{
	"success": true,
	"barcode": {
		"id": 123,
		"name": "PB0000123",
		"state": "active",
		"barcode_type": "generic",
		"barcode_format": "code128"
	},
	"row_html": "<tr>...</tr>" // Present when template rendering succeeds
}
```

Usage Flow:

1. User clicks "Generate" in the portal barcode management view
2. Button enters loading state; JSON POST issued with optional `barcode_type` / `barcode_format`
3. Server creates record via sequence – creation audited via chatter
4. Client inserts server-rendered row (`row_html`) at top, or builds a minimal fallback row if fragment missing
5. Optional future association to boxes/documents can extend model via many2one fields

Extension Points:

* Override `generate_portal_barcode` to inject domain-specific validation or linking
* Add new selection values for `barcode_type` / `barcode_format` (ensure related views updated)
* Attach to container / document models by adding relational fields + adapting row template
* Introduce scheduled expiration by adding cron to transition `state` → `expired`

Security Notes:

* Endpoint restricted to internal records groups (no raw portal/public access yet)
* All dynamic HTML either QWeb-rendered or sanitized fallback; no user-supplied fragments injected
* Sequence usage is atomic; uniqueness enforced by (name, company_id) constraint

Future Enhancements (Roadmap Candidates):

* Optional link to `records.box` for pre-label staging
* Batch generation (server-side loop with streamed fragment response)
* Printable sheet (A4 / Letter) with multiple barcodes
* Direct embedding of SVG/PNG barcode images via rendering library

---

## 🔍 Key Improvements in v6.0.0

### Odoo 19.0 Compatibility

- ✅ Removed deprecated `frontdesk` dependency
- ✅ Updated visitor model to standalone implementation
- ✅ Fixed syntax errors from duplicate field removal
- ✅ Improved dependency management
- ✅ Enhanced error handling

### Code Quality

- ✅ Systematic syntax validation
- ✅ Improved import order for ORM compatibility
- ✅ Enhanced field definitions and relationships
- ✅ Better comment documentation

### Performance & Security

- ✅ Optimized computed field calculations
- ✅ Enhanced search and filtering capabilities
- ✅ Improved access control and security
- ✅ Better error handling and validation

## 📊 Business Process Flow

```
1. Document Intake → Box Creation → Location Assignment
2. Retention Policy → Audit Schedule → Compliance Tracking
3. Service Request → Work Order → Completion Certificate
4. Customer Portal → Self-Service → Automated Billing
```

## 🛡️ Security Features

- **Access Control**: Role-based permissions and record rules
- **Audit Logging**: Complete activity tracking and compliance reports
- **Data Encryption**: Secure handling of sensitive information
- **Portal Security**: Controlled customer access with authentication

## 📞 Support & Development

### Getting Help

- Check the [Odoo Documentation](https://www.odoo.com/documentation/19.0/)
- Visit the module's GitHub repository
- Contact: `John75SunCity`

### Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request with detailed description

## 📝 License

This module is licensed under LGPL-3.

## 🔄 Change Log

### v6.0.0 (January 2025)

- Fixed Odoo 19.0 compatibility issues
- Removed deprecated dependencies
- Enhanced visitor management system
- Improved syntax validation and error handling
- Updated manifest for better dependency management

### Previous Versions

See CHANGELOG.md for detailed version history.

---

**Note**: This module requires careful installation order. Install all dependencies first, then the Records Management module. Contact support if you encounter installation issues.

<!-- Trigger rebuild: 2025-08-21 10:43 -->

### Visualization Asset Policy (Updated Local-First Strategy)

The module now implements a **local-first, CDN-fallback** strategy for visualization libraries (currently `vis-network`).

| Aspect | Local First | CDN Fallback |
|--------|-------------|--------------|
| Primary Source | `static/src/lib/vis/vis-network.js/css` | `https://unpkg.com/vis-network@VERSION/*` |
| Trigger | Diagram widgets detected | Local file missing OR placeholder stub present |
| Benefits | Offline, reproducible, version-pinned | Zero initial bundle weight if unused |
| Risk | Must manually upgrade | External availability / network dependency |

#### How It Works
1. `visualization_dynamic_loader.js` checks for `window.vis.Network`.
2. If absent: inject local CSS/JS.
3. If after local load the object is still a stub (placeholder), loader logs a warning and requests CDN assets.
4. If CDN also fails, diagrams gracefully skip rendering (no hard crash).

#### Replacing the Placeholder with Real Library
1. Download the unminified (or prettified) JS + CSS for the desired `vis-network` version.
2. Replace:
   * `static/src/lib/vis/vis-network.js`
   * `static/src/lib/vis/vis-network.css`
3. (Optional) Remove the placeholder stub logic; not required.
4. Increment module version (assets cache bust) in `__manifest__.py` if diagrams already used in deployments.
5. Re-run validator and manual portal diagram smoke test.

#### Version Upgrades
- Update `CDN_VERSION` constant in `visualization_dynamic_loader.js`.
- Replace local files with the new version.
- Add a short CHANGELOG entry if behavior or API changed.

#### Offline / Air-Gapped Environments
No configuration change required—if local assets exist, CDN is never contacted.

#### Rationale
- Ensures future-proof functionality without hard reliance on external URLs.
- Keeps repository lean (placeholder small) until diagrams are a priority.
- Provides deterministic behavior in secure or isolated installations.

#### Validation Notes
- Place readable multi-line sources (avoid giant single-line minified blobs) to prevent cloc / lint warnings.
- If adding source maps, store them alongside and ensure license compliance.

---
