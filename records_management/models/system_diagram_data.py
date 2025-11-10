"""Odoo model for system architecture diagram data aggregation.

This module provides a comprehensive data aggregator for generating interactive
system architecture diagrams in the Records Management module. It dynamically
collects and visualizes relationships between models, users, security groups,
companies, and departments to provide a visual overview of the system structure.

Key Features:
- Dynamic node and edge generation for system components
- User access rights visualization
- Model relationship mapping
- Company and department structure representation
- Interactive diagram configuration with customizable layouts
- Search and filtering capabilities
- Export functionality for external use

The model uses vis.js for diagram rendering and supports hierarchical and
force-directed layouts. It integrates with Odoo's security model to show
access patterns and provides real-time data aggregation with caching.

Typical Usage:
    diagram = env['system.diagram.data'].create({
        'name': 'My System Diagram',
        'search_type': 'models',
        'layout_algorithm': 'hierarchical'
    })
    # Access diagram.nodes_data and diagram.edges_data for visualization
"""

import base64
import json
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SystemDiagramData(models.Model):
    """System Architecture Diagram Data Aggregator.

    This model aggregates and visualizes the Records Management system architecture
    through interactive diagrams. It provides a comprehensive view of system components,
    relationships, user access patterns, and organizational structure.

    The model supports multiple visualization modes:
    - Full system overview with all components
    - Model relationships only
    - User access and security groups
    - Company and department hierarchies
    - Custom search-filtered views

    Diagram generation is optimized with computed fields and caching to handle
    large datasets efficiently. The visualization uses vis.js library for
    interactive network graphs with customizable layouts and styling.

    Attributes:
        name (Char): Display name for the diagram instance
        search_query (Char): Filter criteria for nodes and edges
        search_type (Selection): Type of data to include in diagram
        show_access_only (Boolean): Toggle to show only access-related data
        generation_time (Float): Time taken to generate diagram data
        node_spacing (Integer): Spacing between nodes in layout
        edge_length (Integer): Length of edges in hierarchical layout
        layout_algorithm (Selection): Layout algorithm for diagram
        include_inactive (Boolean): Whether to include inactive records
        group_by_module (Boolean): Group nodes by module affiliation
        max_depth (Integer): Maximum depth for relationship traversal
        exclude_system_models (Boolean): Exclude core Odoo system models
        last_access (Datetime): Timestamp of last diagram access
        diagram_html (Html): Generated HTML for diagram display
        cache_timestamp (Datetime): Timestamp of cached data
        cache_size (Integer): Size of cached data in KB
        edge_count (Integer): Number of edges in diagram
        node_count (Integer): Number of nodes in diagram
        company_id (Many2one): Associated company for data filtering
        nodes_data (Text): JSON representation of diagram nodes
        edges_data (Text): JSON representation of diagram edges
        diagram_config (Text): JSON configuration for diagram layout
    """

    _name = 'system.diagram.data'
    _description = 'System Architecture Diagram Data Aggregator'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Diagram Name", required=True, default="System Architecture Diagram")
    search_query = fields.Char(string="Search Query")
    search_type = fields.Selection(
        [
            ('all', 'All Data'),
            ('models', 'Models Only'),
            ('access', 'Access/Users Only'),
            ('relationships', 'Model Relationships'),
            ('company', 'Company/Departments'),
        ],
        string="Search Type",
        default='all',
    )
    show_access_only = fields.Boolean(string="Show Access Rights Only")

    generation_time = fields.Float(string='Generation Time (seconds)', readonly=True)
    node_spacing = fields.Integer(string='Node Spacing', default=200)
    edge_length = fields.Integer(string='Edge Length', default=150)
    layout_algorithm = fields.Selection([('hierarchical', 'Hierarchical'), ('forceDirected', 'Force Directed')], string='Layout Algorithm', default='hierarchical')
    include_inactive = fields.Boolean(string='Include Inactive Records')
    group_by_module = fields.Boolean(string='Group By Module', default=True)
    max_depth = fields.Integer(string='Maximum Depth', default=5)
    exclude_system_models = fields.Boolean(string='Exclude System Models', default=True)

    last_access = fields.Datetime(string='Last Access', readonly=True)
    diagram_html = fields.Html(string="Diagram HTML", compute="_compute_diagram_html")
    cache_timestamp = fields.Datetime(string="Cache Timestamp", readonly=True)
    cache_size = fields.Integer(string="Cache Size (KB)", readonly=True)

    edge_count = fields.Integer(string="Edge Count", compute="_compute_counts", store=True)
    node_count = fields.Integer(string="Node Count", compute="_compute_counts", store=True)

    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)

    nodes_data = fields.Text(string="Nodes JSON", compute="_compute_diagram_data", store=True)
    edges_data = fields.Text(string="Edges JSON", compute="_compute_diagram_data", store=True)
    diagram_config = fields.Text(string="Diagram Config JSON", compute="_compute_diagram_config", store=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('nodes_data', 'edges_data')
    def _compute_counts(self):
        """Compute the total number of nodes and edges in the diagram.

        This method parses the JSON data stored in nodes_data and edges_data
        fields to calculate the counts. It handles JSON parsing errors gracefully
        by setting counts to zero if data is malformed.

        Args:
            None (operates on self recordset)

        Returns:
            None (sets node_count and edge_count fields)

        Raises:
            None (handles exceptions internally with logging)
        """
        for record in self:
            try:
                nodes = json.loads(record.nodes_data or '[]')
                edges = json.loads(record.edges_data or '[]')
                record.node_count = len(nodes)
                record.edge_count = len(edges)
            except (json.JSONDecodeError, TypeError):
                record.node_count = 0
                record.edge_count = 0

    @api.depends('show_access_only', 'search_query', 'company_id')
    def _compute_diagram_data(self):
        """Generate nodes and edges data for the diagram.

        This is the main computation method that aggregates all diagram data
        based on the current configuration. It collects core system nodes,
        model relationships, user access data, and company structure, then
        applies search filters if specified.

        The method is designed to be efficient with batched operations and
        includes comprehensive error handling to prevent diagram generation
        failures.

        Args:
            None (operates on self recordset)

        Returns:
            None (sets nodes_data and edges_data fields)

        Raises:
            None (handles exceptions internally with logging and fallback data)
        """
        for record in self:
            try:
                nodes = []
                edges = []

                # Core system nodes
                nodes.extend(record._get_core_system_nodes())

                # Model relationship nodes
                if not record.show_access_only:
                    model_nodes, model_edges = record._get_model_relationships()
                    nodes.extend(model_nodes)
                    edges.extend(model_edges)

                # User and access nodes
                user_nodes, access_edges = record._get_user_access_data()
                nodes.extend(user_nodes)
                edges.extend(access_edges)

                # Cross-department sharing nodes
                if not record.show_access_only:
                    sharing_nodes, sharing_edges = record._get_cross_department_sharing()
                    nodes.extend(sharing_nodes)
                    edges.extend(sharing_edges)

                # Apply search filters
                if record.search_query:
                    nodes, edges = record._apply_search_filter(nodes, edges)

                record.nodes_data = json.dumps(nodes, indent=2)
                record.edges_data = json.dumps(edges, indent=2)

            except Exception as e:
                _logger.error("Error computing diagram data: %s", str(e), exc_info=True)
                record.nodes_data = json.dumps([{'id': 'error', 'label': 'Error Generating Data', 'group': 'error'}])
                record.edges_data = json.dumps([])

    @api.depends('layout_algorithm', 'node_spacing', 'edge_length')
    def _compute_diagram_config(self):
        """Generate diagram configuration for vis.js visualization.

        Creates a comprehensive configuration object for the vis.js network
        visualization library. The configuration includes layout settings,
        physics parameters, interaction options, and styling for nodes and edges.

        Supports both hierarchical and force-directed layouts with customizable
        spacing and interaction settings.

        Args:
            None (operates on self recordset)

        Returns:
            None (sets diagram_config field with JSON configuration)
        """
        for record in self:
            config = {
                "layout": {
                    "hierarchical": {
                        "enabled": record.layout_algorithm == 'hierarchical',
                        "direction": "UD",
                        "sortMethod": "directed",
                        "levelSeparation": record.edge_length,
                        "nodeSpacing": record.node_spacing,
                    }
                },
                "physics": {
                    "enabled": True,
                    "stabilization": {"iterations": 100},
                },
                "interaction": {
                    "hover": True,
                    "multiselect": True,
                    "selectConnectedEdges": False,
                },
                "nodes": {
                    "font": {"size": 14, "color": "#333333"},
                    "borderWidth": 2,
                    "shadow": True,
                },
                "edges": {
                    "arrows": {"to": {"enabled": True, "scaleFactor": 0.5}},
                    "font": {"size": 12},
                    "smooth": {"type": "dynamic"},
                }
            }
            record.diagram_config = json.dumps(config, indent=2)

    @api.depends('nodes_data', 'edges_data', 'diagram_config')
    def _compute_diagram_html(self):
        """Generates the full HTML for the diagram to be rendered in a field.

        Creates an embedded HTML snippet with JavaScript code to initialize
        the vis.js network diagram. This method generates a self-contained
        HTML fragment that can be displayed in an Odoo form view.

        Note: In production, this should use QWeb templates for better
        maintainability and performance.

        Args:
            None (operates on self recordset)

        Returns:
            None (sets diagram_html field with generated HTML)
        """
        for record in self:
            # Prepare safe JSON payloads for inline usage
            try:
                nodes_payload = json.loads(record.nodes_data or '[]')
            except (TypeError, json.JSONDecodeError):
                nodes_payload = []

            try:
                edges_payload = json.loads(record.edges_data or '[]')
            except (TypeError, json.JSONDecodeError):
                edges_payload = []

            try:
                config_payload = json.loads(record.diagram_config or '{}')
            except (TypeError, json.JSONDecodeError):
                config_payload = {}

            local_js = "/records_management/static/src/lib/vis/vis-network.min.js"
            local_css = "/records_management/static/src/lib/vis/vis-network.css"
            cdn_js = "https://unpkg.com/vis-network@9.1.6/dist/vis-network.min.js"
            cdn_css = "https://unpkg.com/vis-network@9.1.6/dist/vis-network.min.css"

            container_id = f"diagram-{record.id or 'new'}"

            template = """
<div id="{container_id}" style="height: 800px; border: 1px solid #ccc;"></div>
<script type="text/javascript">
    (function () {{
        var containerId = '{container_id}';
        function ensureResource(tagName, attrs, marker) {{
            return new Promise(function (resolve, reject) {{
                var selector = tagName + '[data-rm-vis="' + marker + '"]';
                var existing = document.querySelector(selector);
                if (existing) {{
                    if (tagName === 'script' && !(existing.readyState === 'loaded' || existing.readyState === 'complete')) {{
                        existing.addEventListener('load', function () {{ resolve(existing); }});
                        existing.addEventListener('error', function () {{ reject(new Error('Failed to load ' + (attrs.src || attrs.href))); }});
                        return;
                    }}
                    resolve(existing);
                    return;
                }}
                var el = document.createElement(tagName);
                Object.keys(attrs).forEach(function (key) {{ el.setAttribute(key, attrs[key]); }});
                el.setAttribute('data-rm-vis', marker);
                if (tagName === 'script') {{
                    el.onload = function () {{ resolve(el); }};
                    el.onerror = function () {{ reject(new Error('Failed to load ' + (attrs.src || attrs.href))); }};
                }} else {{
                    el.onload = function () {{ resolve(el); }};
                    el.onerror = function () {{ reject(new Error('Failed to load ' + (attrs.src || attrs.href))); }};
                }}
                document.head.appendChild(el);
                if (tagName === 'link') {{ resolve(el); }}
            }});
        }}
        function ensureVis() {{
            if (window.vis && window.vis.Network) {{ return Promise.resolve(); }}
            return ensureResource('link', {{ rel: 'stylesheet', href: '{local_css}' }}, 'rm-vis-local-css')
                .catch(function () {{ return ensureResource('link', {{ rel: 'stylesheet', href: '{cdn_css}' }}, 'rm-vis-cdn-css'); }})
                .then(function () {{
                    return ensureResource('script', {{ src: '{local_js}', async: 'true' }}, 'rm-vis-local-js')
                        .catch(function () {{ return ensureResource('script', {{ src: '{cdn_js}', async: 'true' }}, 'rm-vis-cdn-js'); }});
                }});
        }}
        ensureVis().then(function () {{
            if (!(window.vis && window.vis.Network)) {{
                console.error('vis.js library is not loaded after attempting to fetch assets.');
                return;
            }}
            var container = document.getElementById(containerId);
            if (!container) {{ return; }}
            var nodes = new vis.DataSet({nodes});
            var edges = new vis.DataSet({edges});
            var data = {{ nodes: nodes, edges: edges }};
            var options = {options} || {{}};
            new vis.Network(container, data, options);
        }}).catch(function (error) {{
            console.error('Failed to initialize vis.js network:', error);
        }});
    }})();
</script>
"""

            record.diagram_html = template.format(
                container_id=container_id,
                local_css=local_css,
                cdn_css=cdn_css,
                local_js=local_js,
                cdn_js=cdn_js,
                nodes=json.dumps(nodes_payload),
                edges=json.dumps(edges_payload),
                options=json.dumps(config_payload),
            )

    # ============================================================================
    # DATA GENERATION METHODS
    # ============================================================================
    def _get_core_system_nodes(self):
        """Get core system component nodes for the diagram.

        Returns a list of fundamental system nodes that form the backbone
        of the Records Management system architecture. These include the
        main system, backend interface, portal interface, and compliance
        components.

        Returns:
            list: List of node dictionaries with vis.js node properties
                  including id, label, group, color, shape, and level
        """
        return [
            {
                "id": "core_system", "label": "Records Management\nSystem", "group": "system",
                "color": {"background": "#2E86AB", "border": "#1B4B73"}, "shape": "box",
                "font": {"color": "white", "size": 16}, "level": 0,
            },
            {
                "id": "backend", "label": "Backend\n(Internal Users)", "group": "interface",
                "color": {"background": "#A23B72", "border": "#6B1E47"}, "shape": "ellipse", "level": 1,
            },
            {
                "id": "portal", "label": "Customer Portal\n(External Users)", "group": "interface",
                "color": {"background": "#F18F01", "border": "#B8630F"}, "shape": "ellipse", "level": 1,
            },
            {
                "id": "naid_compliance", "label": "NAID AAA\nCompliance", "group": "compliance",
                "color": {"background": "#C73E1D", "border": "#8B2817"}, "shape": "diamond", "level": 2,
            },
        ]

    def _get_model_relationships(self):
        """Get Records Management model relationships for visualization.

        Analyzes the core models in the Records Management module and creates
        nodes and edges representing their relationships. This includes
        containers, documents, locations, requests, and compliance models.

        The method checks for model existence to ensure compatibility across
        different module configurations.

        Returns:
            tuple: (nodes_list, edges_list) where each is a list of dictionaries
                   representing vis.js nodes and edges with appropriate styling
        """
        nodes = []
        edges = []
        core_models = [
            ("records.container", "Container", "#4CAF50"),
            ("records.document", "Document", "#2196F3"),
            ("records.location", "Location", "#FF9800"),
            ("pickup.request", "Pickup Request", "#9C27B0"),
            ("shredding.service", "Shredding Service", "#F44336"),
            ("portal.request", "Portal Request", "#607D8B"),
            ("customer.feedback", "Customer Feedback", "#795548"),
            ("naid.compliance", "NAID Compliance", "#E91E63"),
        ]

        for model_name, display_name, color in core_models:
            if self._model_exists(model_name):
                node_id = f"model_{model_name.replace('.', '_')}"
                nodes.append({
                    "id": node_id, "label": display_name, "group": "model",
                    "color": {"background": color, "border": self._darken_color(color)},
                    "shape": "box", "level": 3,
                })
                edges.append({
                    "from": "core_system", "to": node_id,
                    "color": {"color": "#666666"}, "arrows": {"to": {"enabled": True}},
                })

        edges.extend(self._get_model_field_relationships())
        return nodes, edges

    def _get_user_access_data(self):
        """Get user access rights visualization data.

        Collects and visualizes user access patterns including security groups,
        user memberships, and portal user access. This provides a clear view
        of who has access to what parts of the system.

        The method includes both internal users and portal users, with
        color-coding to indicate access levels and group memberships.

        Returns:
            tuple: (nodes_list, edges_list) representing users, groups, and
                   their relationships in the system

        Note:
            Limits results to prevent performance issues with large user bases
        """
        nodes = []
        edges = []
        try:
            groups = self.env["res.groups"].search([
                '|', ('name', 'ilike', 'records'),
                '|', ('name', 'ilike', 'shredding'),
                ('name', 'ilike', 'warehouse')
            ])
            for group in groups:
                group_id = f"group_{group.id}"
                nodes.append({
                    "id": group_id, "label": group.name, "group": "security_group",
                    "color": {"background": "#8BC34A", "border": "#4CAF50"}, "shape": "ellipse", "level": 4,
                })
                edges.append({
                    "from": "backend", "to": group_id, "color": {"color": "#4CAF50"},
                    "arrows": {"to": {"enabled": True}}, "label": "Access",
                })

            users = self.env["res.users"].search([("active", "=", True), ("share", "=", False)], limit=20)
            for user in users:
                user_id = f"user_{user.id}"
                has_access = self._check_user_records_access(user)
                user_color = "#4CAF50" if has_access else "#F44336"
                nodes.append({
                    "id": user_id, "label": user.name, "group": "user",
                    "color": {"background": user_color, "border": self._darken_color(user_color)},
                    "shape": "circle", "level": 5,
                })
                for group in user.groups_id:
                    if group in groups:
                        edges.append({
                            "from": user_id, "to": f"group_{group.id}",
                            "color": {"color": user_color}, "arrows": {"to": {"enabled": True}}, "label": "Member",
                        })

            portal_users = self.env["res.users"].search([("active", "=", True), ("share", "=", True)], limit=10)
            for user in portal_users:
                user_id = f"portal_user_{user.id}"
                nodes.append({
                    "id": user_id, "label": f"{user.name}\n(Portal)", "group": "portal_user",
                    "color": {"background": "#FF9800", "border": "#F57C00"}, "shape": "circle", "level": 5,
                })
                edges.append({
                    "from": user_id, "to": "portal", "color": {"color": "#FF9800"},
                    "arrows": {"to": {"enabled": True}}, "label": "Access",
                })
        except Exception as e:
            _logger.warning("Error getting user access data: %s", str(e))
        return nodes, edges

    def _get_company_structure(self):
        """Get company and department structure for visualization.

        Creates nodes and edges representing the organizational hierarchy
        including companies and their departments. This helps visualize
        how the system is organized across different business units.

        Only includes departments if the records.department model exists
        to maintain compatibility.

        Returns:
            tuple: (nodes_list, edges_list) showing company and department
                   relationships in the organizational structure
        """
        nodes = []
        edges = []
        try:
            companies = self.env["res.company"].search([])
            for company in companies:
                company_id = f"company_{company.id}"
                nodes.append({
                    "id": company_id, "label": company.name, "group": "company",
                    "color": {"background": "#3F51B5", "border": "#1A237E"}, "shape": "box", "level": 6,
                })
                edges.append({
                    "from": "core_system", "to": company_id, "color": {"color": "#3F51B5"},
                    "arrows": {"to": {"enabled": True}}, "label": "Company",
                })

            if self._model_exists("records.department"):
                departments = self.env["records.department"].search([])
                for dept in departments:
                    dept_id = f"department_{dept.id}"
                    nodes.append({
                        "id": dept_id, "label": dept.name, "group": "department",
                        "color": {"background": "#673AB7", "border": "#4527A0"}, "shape": "ellipse", "level": 7,
                    })
                    if hasattr(dept, "company_id") and dept.company_id:
                        edges.append({
                            "from": f"company_{dept.company_id.id}", "to": dept_id,
                            "color": {"color": "#673AB7"}, "arrows": {"to": {"enabled": True}}, "label": "Department",
                        })
        except Exception as e:
            _logger.warning("Error getting company structure: %s", str(e))
        return nodes, edges

    def _get_cross_department_sharing(self):
        """Get cross-department sharing relationships for visualization.

        Creates nodes and edges representing cross-department sharing requests,
        approvals, and rejections. This helps visualize collaboration patterns
        and access sharing across different departments.

        Returns:
            tuple: (nodes_list, edges_list) showing sharing relationships
                   with appropriate status-based styling
        """
        nodes = []
        edges = []
        try:
            # Get sharing records
            sharing_records = self.env["cross.department.sharing"].search(
                [("company_id", "=", self.company_id.id)], limit=50
            )  # Limit for performance

            for sharing in sharing_records:
                # Create sharing request node
                sharing_id = f"sharing_{sharing.id}"
                status_color = self._get_sharing_status_color(sharing.state)

                nodes.append(
                    {
                        "id": sharing_id,
                        "label": f"Share\n{sharing.name}",
                        "title": "Sharing: %s\nFrom: %s\nTo: %s\nStatus: %s"
                        % (
                            sharing.name,
                            sharing.requesting_department_id.name,
                            sharing.target_department_id.name,
                            sharing.state.title(),
                        ),
                        "group": f"sharing_{sharing.state}",
                        "color": {"background": status_color, "border": self._darken_color(status_color)},
                        "shape": "diamond",
                        "level": 8,
                        "size": 25,
                    }
                )

                # Connect requesting department to sharing
                edges.append(
                    {
                        "from": f"department_{sharing.requesting_department_id.id}",
                        "to": sharing_id,
                        "color": {"color": "#FF6F00"},
                        "arrows": {"to": {"enabled": True}},
                        "label": "Requests",
                        "dashes": [5, 5],
                    }
                )

                # Connect sharing to target department
                edges.append(
                    {
                        "from": sharing_id,
                        "to": f"department_{sharing.target_department_id.id}",
                        "color": {"color": status_color},
                        "arrows": {"to": {"enabled": True}},
                        "label": "Shares With",
                        "width": 3,
                    }
                )

                # Connect shared records to sharing
                for container in sharing.shared_record_ids[:5]:  # Limit for performance
                    edges.append(
                        {
                            "from": "model_records_container",
                            "to": sharing_id,
                            "color": {"color": "#9C27B0"},
                            "arrows": {"to": {"enabled": True}},
                            "label": f"Record: {container.name or container.id}",
                            "dashes": [2, 2],
                        }
                    )

        except Exception as e:
            _logger.warning("Error getting cross-department sharing: %s", str(e))
        return nodes, edges

    def _get_sharing_status_color(self, state):
        """Get color for sharing status.

        Args:
            state (str): Sharing state (draft, sent, approved, rejected, expired, revoked)

        Returns:
            str: Hex color code for the status
        """
        color_map = {
            "draft": "#9E9E9E",  # Gray
            "sent": "#FBC02D",  # Yellow
            "approved": "#388E3C",  # Green
            "rejected": "#D32F2F",  # Red
            "expired": "#757575",  # Dark Gray
            "revoked": "#5D4037",  # Brown
        }
        return color_map.get(state, "#9E9E9E")

    def _get_model_field_relationships(self):
        """Get relationships between models based on field definitions.

        Analyzes predefined key relationships between core models in the
        Records Management system. These relationships are hardcoded based
        on common field connections and business logic dependencies.

        The method creates dashed edges to distinguish field relationships
        from structural relationships in the diagram.

        Returns:
            list: List of edge dictionaries representing model field relationships
                  with dashed styling to indicate field-based connections
        """
        edges = []
        key_relationships = [
            ("records.container", "records.document", "Documents"),
            ("records.document", "records.location", "Location"),
            ("pickup.request", "records.container", "Containers"),
            ("shredding.service", "records.container", "Shred Items"),
            ("portal.request", "res.partner", "Customer"),
            ("naid.compliance", "records.document", "Compliance"),
        ]
        try:
            for from_model, to_model, label in key_relationships:
                if self._model_exists(from_model) and self._model_exists(to_model):
                    from_id = f"model_{from_model.replace('.', '_')}"
                    to_id = f"model_{to_model.replace('.', '_')}"
                    edges.append({
                        "from": from_id, "to": to_id, "color": {"color": "#999999"},
                        "arrows": {"to": {"enabled": True}}, "label": label, "dashes": True,
                    })
        except Exception as e:
            _logger.warning("Error getting model relationships: %s", str(e))
        return edges

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    @api.model
    def _model_exists(self, model_name):
        """Check if a model exists in the system, with caching for performance.

        Performs a quick existence check for a model in the current Odoo
        environment. This method is optimized for repeated calls during
        diagram generation.

        Args:
            model_name (str): The technical name of the model to check
                              (e.g., 'res.partner', 'records.container')

        Returns:
            bool: True if the model exists and is accessible, False otherwise
        """
        return model_name in self.env

    def _check_user_records_access(self, user):
        """Check if user has access to Records Management functionality.

        Determines whether a specific user has access to the Records Management
        module by checking group membership. This is used for color-coding
        users in the access visualization.

        Args:
            user (res.users): User record to check access for

        Returns:
            bool: True if user has records management access, False otherwise

        Note:
            Handles exceptions gracefully to prevent diagram generation failures
        """
        try:
            return user.has_group("records_management.group_records_user")
        except (AttributeError, KeyError, TypeError):
            return False

    def _apply_search_filter(self, nodes, edges):
        """Apply search filtering to nodes and edges based on query.

        Filters the diagram data to only include nodes and edges that match
        the search query. The search is case-insensitive and looks for matches
        in node labels. Connected edges are preserved for filtered nodes.

        Args:
            nodes (list): List of node dictionaries to filter
            edges (list): List of edge dictionaries to filter

        Returns:
            tuple: (filtered_nodes, filtered_edges) containing only matching
                   nodes and their connecting edges
        """
        if not self.search_query:
            return nodes, edges
        query = self.search_query.lower()
        filtered_node_ids = {n['id'] for n in nodes if query in n.get("label", "").lower()}
        filtered_nodes = [n for n in nodes if n['id'] in filtered_node_ids]
        filtered_edges = [e for e in edges if e.get('from') in filtered_node_ids and e.get('to') in filtered_node_ids]
        return filtered_nodes, filtered_edges

    def _darken_color(self, hex_color):
        """Darken a hex color for creating border colors.

        Takes a hex color string and creates a darker version by reducing
        RGB values by 30%. This is used to generate border colors that
        complement the background colors in the diagram.

        Args:
            hex_color (str): Hex color string (e.g., '#FF5733')

        Returns:
            str: Darkened hex color string, or '#333333' if parsing fails
        """
        try:
            hex_color = hex_color.lstrip("#")
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            darkened = tuple(max(0, int(c * 0.7)) for c in rgb)
            return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
        except (ValueError, IndexError, TypeError):
            return "#333333"

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_refresh_diagram(self):
        """Refresh the diagram data by clearing cached computations.

        Forces a complete regeneration of the diagram data by clearing the
        computed fields and invalidating the recordset cache. This ensures
        that any changes to underlying data (users, groups, models) are
        reflected in the diagram.

        Returns:
            dict: Action dictionary to reload the current view
        """
        self.ensure_one()
        self.write({
            'nodes_data': False,
            'edges_data': False,
            'diagram_config': False,
        })
        self.invalidate_recordset(['nodes_data', 'edges_data', 'diagram_config'])
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }

    def action_export_diagram_data(self):
        """Export diagram data for external use or backup.

        Creates a comprehensive export package containing all diagram data
        including nodes, edges, configuration, and metadata. The data is
        exported as a downloadable JSON file with base64 encoding.

        Returns:
            dict: Action dictionary to trigger file download with the
                  exported diagram data

        Note:
            The export includes a timestamp for versioning and external
            system integration
        """
        self.ensure_one()
        export_data = {
            "diagram_name": self.name,
            "nodes": json.loads(self.nodes_data or "[]"),
            "edges": json.loads(self.edges_data or "[]"),
            "config": json.loads(self.diagram_config or "{}"),
            "timestamp": fields.Datetime.now().isoformat(),
        }
        json_data = json.dumps(export_data, indent=2)
        b64_data = base64.b64encode(json_data.encode("utf-8")).decode("utf-8")
        return {
            "type": "ir.actions.act_url",
            "url": f"data:application/json;charset=utf-8;base64,{b64_data}",
            "target": "new",
        }

    def action_regenerate_diagram(self):
        """Manually trigger diagram regeneration.
        
        This method forces recomputation of all diagram data by invalidating
        the cache and triggering field recomputation.
        """
        self.ensure_one()
        # Force recomputation of computed fields
        self.invalidate_cache(['nodes_data', 'edges_data', 'diagram_config', 'diagram_html'])
        self._compute_diagram_data()
        self._compute_diagram_config()
        self._compute_diagram_html()
        return True
