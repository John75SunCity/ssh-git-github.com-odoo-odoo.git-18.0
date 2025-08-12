# -*- coding: utf-8 -*-
"""
Customer Portal Interactive Diagram Model

This model provides an interactive organizational diagram specifically designed for
customer portal users. Unlike the admin system flowchart, this focuses on:
- Company organizational structure
- User relationships within customer's organization
- Messaging and communication capabilities
- Portal-specific security and access controls

Key Differences from System Flowchart:
- Customer-facing (portal users only)
- Focus on organizational structure and communication
- Simplified access rights visualization
- Integrated messaging capabilities
- Department and company hierarchy emphasis
"""

# Python stdlib imports
import base64
import json
import logging

# Odoo core imports
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CustomerPortalDiagram(models.TransientModel):
    _name = "customer.portal.diagram"
    _description = "Interactive Customer Portal Organization Diagram"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Diagram Name", default="Organization Diagram", required=True
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, required=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # COMPUTED DIAGRAM DATA FIELDS
    # ============================================================================
    node_data = fields.Text(
        string="Node Data", compute="_compute_diagram_data", store=False
    )
    edge_data = fields.Text(
        string="Edge Data", compute="_compute_diagram_data", store=False
    )
    diagram_stats = fields.Text(
        string="Diagram Statistics", compute="_compute_diagram_stats", store=False
    )

    # ============================================================================
    # SEARCH AND FILTER FIELDS
    # ============================================================================
    search_user_id = fields.Many2one(
        "res.users", string="Search User", help="Filter diagram to show specific user"
    )
    search_company_id = fields.Many2one(
        "res.company",
        string="Search Company",
        help="Filter diagram to show specific company",
    )
    search_department_id = fields.Many2one(
        "records.department",
        string="Search Department",
        help="Filter diagram to show specific department",
    )
    search_query = fields.Char(
        string="Search Query", help="Text search for nodes and edges"
    )

    # ============================================================================
    # DIAGRAM CONFIGURATION FIELDS
    # ============================================================================
    show_access_rights = fields.Boolean(
        string="Show Access Rights",
        default=True,
        help="Display access rights as colored edges",
    )
    show_messaging = fields.Boolean(
        string="Enable Messaging",
        default=True,
        help="Allow clicking users to open messaging",
    )
    layout_type = fields.Selection(
        [
            ("hierarchical", "Hierarchical"),
            ("network", "Network"),
            ("circular", "Circular"),
        ],
        string="Layout Type",
        default="hierarchical",
    )

    # ============================================================================
    # SECURITY AND ACCESS FIELDS
    # ============================================================================
    allowed_user_ids = fields.Many2many(
        "res.users", string="Allowed Users", help="Users who can view this diagram"
    )
    restricted_models = fields.Char(
        string="Restricted Models",
        default="records.document,records.container,portal.request",
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends(
        "search_user_id",
        "search_company_id",
        "search_department_id",
        "search_query",
        "show_access_rights",
    )
    def _compute_diagram_data(self):
        """Compute the diagram nodes and edges data for the interactive visualization"""
        for record in self:
            nodes = []
            edges = []
            
            try:
                current_user = self.env.user
                portal_user = current_user.has_group("portal.group_portal")

                # Security check - portal users can only see their company data
                if portal_user:
                    allowed_companies = [current_user.company_id.id]
                    allowed_departments = (
                        current_user.partner_id.records_department_ids.ids
                        if current_user.partner_id.records_department_ids
                        else []
                    )
                else:
                    # Internal users can see more data based on permissions
                    allowed_companies = self.env["res.company"].search([]).ids
                    allowed_departments = self.env["records.department"].search([]).ids

                # Generate company nodes
                nodes, edges = record._generate_company_nodes(
                    nodes, edges, allowed_companies
                )

                # Generate department nodes
                nodes, edges = record._generate_department_nodes(
                    nodes, edges, allowed_companies, allowed_departments
                )

                # Generate user nodes
                nodes, edges = record._generate_user_nodes(
                    nodes, edges, allowed_companies, allowed_departments, current_user
                )

                # Generate access rights visualization if enabled
                if record.show_access_rights and not portal_user:
                    nodes, edges = record._generate_access_rights_nodes(
                        nodes, edges, allowed_companies
                    )

                # Apply search filtering
                if record.search_query:
                    nodes, edges = record._apply_search_filtering(nodes, edges)

                # Store computed data
                record.node_data = json.dumps(nodes)
                record.edge_data = json.dumps(edges)

            except Exception as e:
                _logger.error("Error computing diagram data: %s", e)
                record.node_data = json.dumps([])
                record.edge_data = json.dumps([])

    @api.depends("node_data", "edge_data")
    def _compute_diagram_stats(self):
        """Compute diagram statistics for display"""
        for record in self:
            try:
                nodes = json.loads(record.node_data or "[]")
                edges = json.loads(record.edge_data or "[]")

                stats = {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "companies": len([n for n in nodes if n["group"] == "company"]),
                    "departments": len(
                        [n for n in nodes if n["group"] == "department"]
                    ),
                    "users": len([n for n in nodes if n["group"] == "user"]),
                    "models": len([n for n in nodes if n["group"] == "model"]),
                }

                record.diagram_stats = json.dumps(stats)
            except Exception as e:
                _logger.error("Error computing diagram stats: %s", e)
                record.diagram_stats = json.dumps({})

    # ============================================================================
    # HELPER METHODS FOR DIAGRAM GENERATION
    # ============================================================================
    def _generate_company_nodes(self, nodes, edges, allowed_companies):
        """Generate company nodes for the diagram"""
        company_domain = [("id", "in", allowed_companies)]
        if self.search_company_id:
            company_domain.append(("id", "=", self.search_company_id.id))

        companies = self.env["res.company"].sudo().search(company_domain)
        for company in companies:
            node_id = "company_%s" % company.id
            nodes.append(
                {
                    "id": node_id,
                    "label": company.name,
                    "title": _("Company: %s", company.name),
                    "group": "company",
                    "level": 0,
                    "color": {"background": "#FFD700", "border": "#FFA500"},
                    "shape": "box",
                    "font": {"color": "#000000", "size": 14},
                }
            )
        return nodes, edges

    def _generate_department_nodes(self, nodes, edges, allowed_companies, allowed_departments):
        """Generate department nodes for the diagram"""
        dept_domain = [("company_id", "in", allowed_companies)]
        if allowed_departments:
            dept_domain.append(("id", "in", allowed_departments))
        if self.search_department_id:
            dept_domain = [("id", "=", self.search_department_id.id)]

        departments = self.env["records.department"].sudo().search(dept_domain)
        for dept in departments:
            node_id = "dept_%s" % dept.id
            company_name = dept.company_id.name if dept.company_id else _("N/A")
            
            nodes.append(
                {
                    "id": node_id,
                    "label": dept.name,
                    "title": _("Department: %s\nCompany: %s", dept.name, company_name),
                    "group": "department",
                    "level": 1,
                    "color": {"background": "#90EE90", "border": "#32CD32"},
                    "shape": "ellipse",
                    "font": {"color": "#000000", "size": 12},
                }
            )

            # Link departments to companies
            if dept.company_id:
                edges.append(
                    {
                        "from": node_id,
                        "to": "company_%s" % dept.company_id.id,
                        "label": _("Belongs to"),
                        "color": {"color": "#808080"},
                        "arrows": {"to": {"enabled": True}},
                        "dashes": False,
                    }
                )
        return nodes, edges

    def _generate_user_nodes(self, nodes, edges, allowed_companies, allowed_departments, current_user):
        """Generate user nodes for the diagram"""
        portal_user = current_user.has_group("portal.group_portal")
        
        user_domain = [
            ("company_id", "in", allowed_companies),
            ("active", "=", True),
        ]
        
        if portal_user:
            # Portal users can only see users in their company and departments
            if allowed_departments:
                user_domain.append(
                    ("partner_id.records_department_ids", "in", allowed_departments)
                )
            else:
                user_domain.append(("company_id", "=", current_user.company_id.id))

        if self.search_user_id:
            user_domain = [("id", "=", self.search_user_id.id)]

        users = self.env["res.users"].sudo().search(user_domain)
        for user in users:
            node_id = "user_%s" % user.id
            is_portal = user.has_group("portal.group_portal")
            is_current = user.id == current_user.id

            # Color coding for different user types
            if is_current:
                color = {"background": "#FF6B6B", "border": "#FF5252"}
            elif is_portal:
                color = {"background": "#FF69B4", "border": "#C2185B"}
            else:
                color = {"background": "#87CEEB", "border": "#5DADE2"}

            user_role = _("Portal User") if is_portal else _("Internal User")
            email_display = user.email or _("No email")
            
            nodes.append(
                {
                    "id": node_id,
                    "label": user.name,
                    "title": _("User: %s\nRole: %s\nEmail: %s\nCompany: %s", 
                             user.name, user_role, email_display, user.company_id.name),
                    "group": "user",
                    "level": 2,
                    "color": color,
                    "shape": "circularImage" if user.image_1920 else "dot",
                    "image": (
                        "/web/image/res.users/%s/image_1920" % user.id
                        if user.image_1920
                        else None
                    ),
                    "font": {"color": "#FFFFFF", "size": 10},
                    "size": 25 if is_current else 20,
                }
            )

            # Link users to their departments
            if user.partner_id.records_department_ids:
                for dept in user.partner_id.records_department_ids:
                    edges.append(
                        {
                            "from": node_id,
                            "to": "dept_%s" % dept.id,
                            "label": _("Assigned to"),
                            "color": {"color": "#9E9E9E"},
                            "arrows": {"to": {"enabled": True}},
                            "dashes": [5, 5],
                        }
                    )
            else:
                # Link to company if no department
                edges.append(
                    {
                        "from": node_id,
                        "to": "company_%s" % user.company_id.id,
                        "label": _("Employee"),
                        "color": {"color": "#9E9E9E"},
                        "arrows": {"to": {"enabled": True}},
                        "dashes": [5, 5],
                    }
                )

        return nodes, edges

    def _generate_access_rights_nodes(self, nodes, edges, allowed_companies):
        """Generate access rights visualization nodes"""
        restricted_models = (self.restricted_models or "").split(",")
        model_list = [m.strip() for m in restricted_models if m.strip()]
        
        if not model_list:
            return nodes, edges

        ir_models = self.env["ir.model"].sudo().search([("model", "in", model_list)])

        user_domain = [("company_id", "in", allowed_companies), ("active", "=", True)]
        users = self.env["res.users"].sudo().search(user_domain)

        for model in ir_models:
            model_node_id = "model_%s" % model.id
            short_name = model.name.split(".")[-1]  # Short name
            
            nodes.append(
                {
                    "id": model_node_id,
                    "label": short_name,
                    "title": _("Model: %s\nDescription: %s", model.name, model.model),
                    "group": "model",
                    "level": 3,
                    "color": {"background": "#ADD8E6", "border": "#4682B4"},
                    "shape": "box",
                    "font": {"color": "#000000", "size": 8},
                }
            )

            # Check access for each user
            for user in users:
                user_node_id = _("user_%s", user.id)
                try:
                    # Check if user has read access to this model
                    has_access = (
                        self.env[model.model]
                        .with_user(user.id)
                        .check_access_rights("read", raise_exception=False)
                    )
                    edge_color = "#4CAF50" if has_access else "#F44336"

                    edges.append(
                        {
                            "from": user_node_id,
                            "to": model_node_id,
                            "label": _("Access"),
                            "color": {"color": edge_color},
                            "arrows": {"to": {"enabled": True}},
                            "dashes": True,
                            "width": 2,
                        }
                    )
                except Exception as e:
                    _logger.warning(
                        "Access check failed for user %s on model %s: %s",
                        user.name, model.model, e
                    )

        return nodes, edges

    def _apply_search_filtering(self, nodes, edges):
        """Apply search filtering to nodes and edges"""
        search_lower = self.search_query.lower()
        filtered_nodes = []
        filtered_edges = []
        matched_node_ids = set()

        # Find matching nodes
        for node in nodes:
            node_label = node.get("label", "").lower()
            node_title = node.get("title", "").lower()
            
            if search_lower in node_label or search_lower in node_title:
                filtered_nodes.append(node)
                matched_node_ids.add(node["id"])

        # Include edges that connect to matched nodes
        for edge in edges:
            if edge["from"] in matched_node_ids or edge["to"] in matched_node_ids:
                filtered_edges.append(edge)
                # Also include connected nodes
                for node in nodes:
                    node_id = node["id"]
                    if (node_id == edge["from"] or node_id == edge["to"]) and node not in filtered_nodes:
                        filtered_nodes.append(node)

        return filtered_nodes, filtered_edges

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_open_messaging(self, target_user_id):
        """Open messaging interface for communicating with another user"""
        self.ensure_one()

        if not self.show_messaging:
            raise UserError(_("Messaging is disabled for this diagram"))

        target_user = self.env["res.users"].browse(target_user_id)
        current_user = self.env.user

        # Security checks
        if not target_user.exists():
            raise UserError(_("Target user not found"))

        # Portal users can only message users in same company/department
        if current_user.has_group("portal.group_portal"):
            if target_user.company_id != current_user.company_id:
                raise UserError(_("You can only message users in your company"))

            # Check if they share a department
            shared_depts = (
                current_user.partner_id.records_department_ids
                & target_user.partner_id.records_department_ids
            )
            if not shared_depts and not current_user.has_group(
                "records_management.group_records_manager"
            ):
                raise UserError(_("You can only message users in your department"))

        # Open mail compose wizard
        return {
            "type": "ir.actions.act_window",
            "name": _("Message %s", target_user.name),
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_model": "res.users",
                "default_res_id": target_user.id,
                "default_partner_ids": [(6, 0, [target_user.partner_id.id])],
                "default_subject": _("Message from Organization Diagram"),
                "default_body": _("<p>Hi %s,</p><p>I'm reaching out to you via the organization diagram.</p>", target_user.name),
            },
        }

    def action_refresh_diagram(self):
        """Refresh the diagram data"""
        self.ensure_one()
        # Trigger recomputation
        self._compute_diagram_data()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": _("Diagram refreshed successfully"),
                "type": "success",
                "sticky": False,
            },
        }

    def action_export_diagram_data(self):
        """Export diagram data as JSON for external use"""
        self.ensure_one()

        export_data = {
            "name": self.name,
            "created_by": self.user_id.name,
            "created_at": fields.Datetime.now().isoformat(),
            "nodes": json.loads(self.node_data or "[]"),
            "edges": json.loads(self.edge_data or "[]"),
            "stats": json.loads(self.diagram_stats or "{}"),
            "config": {
                "show_access_rights": self.show_access_rights,
                "show_messaging": self.show_messaging,
                "layout_type": self.layout_type,
            },
        }

        json_data = json.dumps(export_data, indent=2)
        encoded_data = base64.b64encode(json_data.encode()).decode()
        
        return {
            "type": "ir.actions.act_url",
            "url": "data:application/json;base64,%s" % encoded_data,
            "target": "self",
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("search_user_id", "search_company_id")
    def _check_search_security_constraints(self):
        """Ensure portal users can only search within their allowed scope"""
        for record in self:
            current_user = self.env.user
            if current_user.has_group("portal.group_portal"):
                if (
                    record.search_company_id
                    and record.search_company_id != current_user.company_id
                ):
                    raise UserError(_("You can only search within your own company"))

                if (
                    record.search_user_id
                    and record.search_user_id.company_id != current_user.company_id
                ):
                    raise UserError(_("You can only search for users in your company"))

    # ============================================================================
    # PORTAL-SPECIFIC HELPER METHODS
    # ============================================================================
    def _get_portal_user_domain(self):
        """Get the domain for filtering data based on portal user permissions"""
        current_user = self.env.user
        if current_user.has_group("portal.group_portal"):
            # Portal users see only their company data
            return [("company_id", "=", current_user.company_id.id)]
        
        # Internal users can see all data (subject to regular security rules)
        return []

    def _check_messaging_permission(self, target_user):
        """Check if current user can message the target user"""
        current_user = self.env.user

        # Same user check
        if current_user.id == target_user.id:
            return False, _("You cannot message yourself")

        # Company check
        if target_user.company_id != current_user.company_id:
            return False, _("You can only message users in your company")

        # Portal user additional checks
        if current_user.has_group("portal.group_portal"):
            # Check shared departments
            shared_depts = (
                current_user.partner_id.records_department_ids
                & target_user.partner_id.records_department_ids
            )
            if not shared_depts:
                return False, _("You can only message users in your department")

        return True, ""
