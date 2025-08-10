# -*- coding: utf-8 -*-
"""
Records Management Base Menus Module

This module provides comprehensive menu configuration and management for the Records Management
System. It enables administrators to customize and control the main navigation structure,
menu visibility, and access permissions across the entire Records Management application.

Key Features:
- Dynamic menu configuration with role-based visibility controls
- Hierarchical menu structure with parent-child relationships
- Menu access permissions integrated with security groups
- Custom menu item creation for specialized workflows
- Menu ordering and priority management for optimal user experience
- Integration with Records Management security framework

Business Processes:
1. Menu Configuration: Administrators configure main navigation menus and submenus
2. Access Control: Menu visibility controlled by user roles and security groups
3. Custom Menus: Creation of custom menu items for specialized business processes
4. Menu Hierarchy: Parent-child menu relationships for organized navigation
5. Priority Management: Menu ordering based on usage patterns and business priorities
6. Dynamic Updates: Real-time menu updates based on user permissions and context

Menu Categories:
- Core Records: Document, container, and location management menus
- Compliance: NAID AAA compliance and audit trail menus
- Customer Portal: Customer-facing service and request menus
- Reporting: Analytics, reports, and dashboard menus
- Administration: System configuration and user management menus

Access Control Integration:
- Security group-based menu visibility with granular permission controls
- Department-level menu filtering for multi-tenant environments
- Role-based menu customization for different user types
- Dynamic menu generation based on user permissions and context
- Integration with Records Management security framework

Technical Implementation:
- Modern Odoo 18.0 architecture with mail thread integration
- Comprehensive field validation and business rule enforcement
- Integration with Records Management security and access control systems
- Support for menu translations and multi-language environments
- Performance optimized menu loading with caching mechanisms

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import re


class RecordsManagementBaseMenus(models.Model):
    _name = "records.management.base.menus"
    _description = "Records Management Base Menus"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Menu Name",
        required=True,
        tracking=True,
        index=True,
        help="Name of the menu item",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for menu configuration",
    )
    active = fields.Boolean(
        string="Active", default=True, help="Whether this menu item is active"
    )

    # ============================================================================
    # MENU CONFIGURATION FIELDS
    # ============================================================================
    menu_type = fields.Selection(
        [
            ("main", "Main Menu"),
            ("submenu", "Submenu"),
            ("action", "Action Menu"),
            ("separator", "Separator"),
            ("custom", "Custom Menu"),
        ],
        string="Menu Type",
        default="main",
        required=True,
        tracking=True,
        help="Type of menu item",
    )
    parent_menu_id = fields.Many2one(
        "records.management.base.menus",
        string="Parent Menu",
        help="Parent menu for hierarchical structure",
    )
    child_menu_ids = fields.One2many(
        "records.management.base.menus",
        "parent_menu_id",
        string="Child Menus",
        help="Child menus under this menu",
    )
    sequence = fields.Integer(
        string="Sequence", default=10, help="Order of the menu item"
    )
    icon = fields.Char(string="Icon", help="FontAwesome icon class for the menu")
    url = fields.Char(string="URL", help="URL for external links")
    action_id = fields.Many2one(
        "ir.actions.actions", string="Action", help="Odoo action to execute"
    )

    # ============================================================================
    # ACCESS CONTROL FIELDS
    # ============================================================================
    group_ids = fields.Many2many(
        "res.groups", string="Access Groups", help="Groups that can access this menu"
    )
    department_ids = fields.Many2many(
        "records.department",
        string="Departments",
        help="Departments that can access this menu",
    )
    visibility = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal Users"),
            ("restricted", "Restricted Access"),
            ("admin", "Administrators Only"),
        ],
        string="Visibility Level",
        default="internal",
        help="Who can see this menu",
    )
    role_based = fields.Boolean(
        string="Role Based Access",
        default=True,
        help="Whether access is controlled by user roles",
    )

    # ============================================================================
    # MENU CATEGORY FIELDS
    # ============================================================================
    category = fields.Selection(
        [
            ("records", "Core Records"),
            ("compliance", "Compliance"),
            ("portal", "Customer Portal"),
            ("reporting", "Reporting"),
            ("operations", "Operations"),
            ("configuration", "Configuration"),
            ("administration", "Administration"),
        ],
        string="Category",
        help="Menu category for organization",
    )
    records_menu = fields.Boolean(
        string="Records Menu", help="Menu related to core records management"
    )
    compliance_menu = fields.Boolean(
        string="Compliance Menu", help="Menu related to NAID compliance"
    )
    portal_menu = fields.Boolean(string="Portal Menu", help="Menu for customer portal")
    reporting_menu = fields.Boolean(
        string="Reporting Menu", help="Menu for reports and analytics"
    )

    # ============================================================================
    # STATUS AND WORKFLOW FIELDS
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current status of the menu configuration",
    )
    published = fields.Boolean(
        string="Published",
        default=False,
        help="Whether this menu is published and visible",
    )
    published_date = fields.Datetime(
        string="Published Date", help="Date when the menu was published"
    )

    # ============================================================================
    # MENU CONTENT FIELDS
    # ============================================================================
    description = fields.Text(
        string="Description", help="Description of the menu purpose"
    )
    tooltip = fields.Char(string="Tooltip", help="Tooltip text for the menu item")
    badge_text = fields.Char(string="Badge Text", help="Badge text to display on menu")
    badge_color = fields.Char(
        string="Badge Color", help="Color of the badge (CSS color)"
    )
    custom_css = fields.Text(string="Custom CSS", help="Custom CSS for menu styling")

    # ============================================================================
    # SYSTEM METADATA FIELDS
    # ============================================================================
    menu_key = fields.Char(string="Menu Key", help="Unique key for menu identification")
    external_id = fields.Char(string="External ID", help="External identifier for menu")
    created_date = fields.Datetime(
        string="Created Date",
        default=fields.Datetime.now,
        readonly=True,
        help="Date when menu was created",
    )
    updated_date = fields.Datetime(
        string="Updated Date", help="Date when menu was last updated"
    )
    access_count = fields.Integer(
        string="Access Count", default=0, help="Number of times menu was accessed"
    )
    last_access_date = fields.Datetime(
        string="Last Access Date", help="Date when menu was last accessed"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends("child_menu_ids")
    def _compute_child_count(self):
        """Compute number of child menus"""
        for record in self:
            record.child_count = len(record.child_menu_ids)

    child_count = fields.Integer(
        string="Child Count",
        compute="_compute_child_count",
        store=True,
        help="Number of child menus",
    )

    @api.depends("name", "parent_menu_id.name")
    def _compute_full_name(self):
        """Compute full hierarchical menu name"""
        for record in self:
            if record.parent_menu_id:
                record.full_name = _("%s / %s"
            else:
                record.full_name = record.name

    full_name = fields.Char(
        string="Full Name",
        compute="_compute_full_name",
        store=True,
        help="Full hierarchical menu name",
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record"
    )

    @api.depends("group_ids", "department_ids", "visibility")
    def _compute_access_level(self):
        """Compute access level based on restrictions"""
        for record in self:
            if record.visibility == "public":
                record.access_level = "public"
            elif record.group_ids or record.department_ids:
                record.access_level = "restricted"
            else:
                record.access_level = "standard"

    access_level = fields.Selection(
        [
            ("public", "Public Access"),
            ("standard", "Standard Access"),
            ("restricted", "Restricted Access"),
        ],
        string="Access Level",
        compute="_compute_access_level",
        store=True,
        help="Computed access level",
    )

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set defaults and validation"""
        for vals in vals_list:
            if not vals.get("menu_key"):
                vals["menu_key"] = self._generate_menu_key(vals.get("name", ""))
            vals["updated_date"] = fields.Datetime.now()
        return super().create(vals_list)

    def write(self, vals):
        """Override write to update metadata"""
        vals["updated_date"] = fields.Datetime.now()
        return super().write(vals)

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _generate_menu_key(self, name):
        """Generate unique menu key from name"""
        base_key = name.lower().replace(" ", "_").replace("-", "_")
        # Remove special characters
        base_key = re.sub(r"[^a-z0-9_]", "", base_key)

        # Ensure uniqueness
        counter = 1
        menu_key = base_key
        while self.search([("menu_key", "=", menu_key)], limit=1):
            menu_key = f"{base_key}_{counter}"
            counter += 1

        return menu_key

    def check_user_access(self, user=None):
        """Check if user has access to this menu"""
        self.ensure_one()
        if not user:
            user = self.env.user

        # Check visibility level
        if self.visibility == "public":
            return True

        # Check group access
        if self.group_ids:
            user_groups = user.groups_id
            if not any(group in user_groups for group in self.group_ids):
                return False

        # Check department access
        if self.department_ids:
            user_departments = getattr(
                user, "records_department_ids", self.env["records.department"]
            )
            if not any(dept in user_departments for dept in self.department_ids):
                return False

        return True

    def get_menu_hierarchy(self):
        """Get full menu hierarchy for this menu"""
        self.ensure_one()
        hierarchy = []
        current = self

        while current:
            hierarchy.insert(
                0,
                {
                    "id": current.id,
                    "name": current.name,
                    "menu_type": current.menu_type,
                    "icon": current.icon,
                },
            )
            current = current.parent_menu_id

        return hierarchy

    def increment_access_count(self):
        """Increment access counter when menu is used"""
        self.ensure_one()
        self.write(
            {
                "access_count": self.access_count + 1,
                "last_access_date": fields.Datetime.now(),
            }
        )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate_menu(self):
        """Activate the menu"""
        self.ensure_one()
        self.write(
            {
                "state": "active",
                "published": True,
                "published_date": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Menu activated"))

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Menu Activated"),
                "message": _("Menu '%s' has been activated") % self.name,
                "type": "success",
            },
        }

    def action_deactivate_menu(self):
        """Deactivate the menu"""
        self.ensure_one()
        self.write(
            {
                "state": "inactive",
                "published": False,
            }
        )
        self.message_post(body=_("Menu deactivated"))

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Menu Deactivated"),
                "message": _("Menu '%s' has been deactivated") % self.name,
                "type": "warning",
            },
        }

    def action_publish_menu(self):
        """Publish the menu"""
        self.ensure_one()

        if self.state != "confirmed":
            raise UserError(_("Only confirmed menus can be published"))

        self.write(
            {
                "published": True,
                "published_date": fields.Datetime.now(),
                "state": "active",
            }
        )

        self.message_post(body=_("Menu published"))
        return True

    def action_archive_menu(self):
        """Archive the menu"""
        self.ensure_one()
        self.write(
            {
                "state": "archived",
                "active": False,
                "published": False,
            }
        )
        self.message_post(body=_("Menu archived"))
        return True

    def action_view_child_menus(self):
        """View child menus"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Child Menus: %s", self.name),
            "res_model": "records.management.base.menus",
            "view_mode": "tree,form",
            "domain": [("parent_menu_id", "=", self.id)],
            "context": {"default_parent_menu_id": self.id},
        }

    def action_duplicate_menu(self):
        """Duplicate the menu with new name"""
        self.ensure_one()

        new_name = _("%s (Copy)"
        duplicate = self.copy(
            {
                "name": new_name,
                "menu_key": self._generate_menu_key(new_name),
                "state": "draft",
                "published": False,
                "published_date": False,
                "access_count": 0,
                "last_access_date": False,
            }
        )

        self.message_post(body=_("Menu duplicated as '%s'") % duplicate.name)

        return {
            "type": "ir.actions.act_window",
            "res_model": "records.management.base.menus",
            "res_id": duplicate.id,
            "view_mode": "form",
            "target": "current",
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("parent_menu_id")
    def _check_parent_recursion(self):
        """Prevent circular parent-child relationships"""
        for record in self:
            if record.parent_menu_id:
                current = record.parent_menu_id
                while current:
                    if current == record:
                        raise ValidationError(
                            _("Circular reference detected in menu hierarchy")
                        )
                    current = current.parent_menu_id

    @api.constrains("menu_key")
    def _check_menu_key_unique(self):
        """Ensure menu keys are unique"""
        for record in self:
            if record.menu_key:
                duplicate = self.search(
                    [("menu_key", "=", record.menu_key), ("id", "!=", record.id)],
                    limit=1,
                )
                if duplicate:
                    raise ValidationError(
                        _("Menu key '%s' already exists") % record.menu_key
                    )

    @api.constrains("sequence")
    def _check_sequence_positive(self):
        """Ensure sequence is positive"""
        for record in self:
            if record.sequence < 0:
                raise ValidationError(_("Sequence must be a positive number"))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name_parts = []

            if record.parent_menu_id:
                name_parts.append(f"↳ {record.name}")
            else:
                name_parts.append(record.name)

            if record.menu_type != "main":
                name_parts.append(f"({record.menu_type.title()})")

            if not record.published:
                name_parts.append("[Draft]")

            result.append((record.id, " ".join(name_parts)))
        return result

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Enhanced search by name, description, or menu key"""
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                "|",
                "|",
                ("name", operator, name),
                ("description", operator, name),
                ("menu_key", operator, name),
                ("tooltip", operator, name),
            ]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def get_user_menus(self, category=None):
        """Get menus accessible to current user"""
        domain = [
            ("published", "=", True),
            ("active", "=", True),
        ]

        if category:
            domain.append(("category", "=", category))

        menus = self.search(domain, order="sequence, name")
        accessible_menus = menus.filtered(lambda m: m.check_user_access())

        return accessible_menus

    @api.model
    def get_menu_structure(self, category=None):
        """Get hierarchical menu structure"""
        menus = self.get_user_menus(category=category)

        # Build hierarchy
        menu_tree = {}
        for menu in menus:
            if not menu.parent_menu_id:
                menu_tree[menu.id] = {"menu": menu, "children": []}

        # Add children
        for menu in menus:
            if menu.parent_menu_id and menu.parent_menu_id.id in menu_tree:
                menu_tree[menu.parent_menu_id.id]["children"].append(menu)

        return list(menu_tree.values())
