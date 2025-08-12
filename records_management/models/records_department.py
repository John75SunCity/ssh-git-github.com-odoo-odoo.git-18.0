# -*- coding: utf-8 -*-
"""
Records Department Management Module

This module provides comprehensive departmental organization and management within the Records
Management System. It implements hierarchical department structures, access control integration,
and departmental workflow management for multi-tenant and enterprise-scale operations.

Key Features:
- Hierarchical department structure with parent-child relationships
- Department-based access control and data segregation for multi-tenant operations
- User assignment and role management within departmental boundaries
- Department-specific workflow configuration and process customization
- Integration with customer assignment and service delivery organization
- Department performance tracking and analytics with operational metrics
- Cost center management and departmental billing allocation

Business Processes:
1. Department Setup: Initial department creation with hierarchy and structure definition
2. User Assignment: Department-based user allocation and role assignment
3. Access Control: Departmental data segregation and permission management
4. Workflow Configuration: Department-specific process and workflow customization
5. Customer Assignment: Customer allocation to appropriate service departments
6. Performance Monitoring: Departmental metrics tracking and performance analysis
7. Cost Management: Department-based cost allocation and budget management

Department Types:
- Operations Departments: Field service, pickup, and delivery operations
- Compliance Departments: NAID AAA compliance, audit, and regulatory management
- Customer Service Departments: Customer support, portal management, and communications
- Administrative Departments: Billing, accounting, and business administration
- Technical Departments: IT support, system administration, and technical services
- Management Departments: Executive management, oversight, and strategic planning

Access Control Integration:
- Department-based record filtering and data segregation for security
- User role assignment within departmental boundaries and hierarchies
- Customer data access control based on department assignments
- Document and container access restrictions by department authorization
- Integration with Records Management security groups and permissions
- Multi-tenant support with complete departmental data isolation

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsDepartment(models.Model):
    """
    Records Department Management - Organizational departments for records management
    Provides hierarchical department structure with access control and workflow integration
    """

    _name = "records.department"
    _description = "Records Department"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Department Name",
        required=True,
        tracking=True,
        index=True,
        help="Name of the department",
    )

    code = fields.Char(
        string="Department Code",
        required=True,
        tracking=True,
        index=True,
        help="Unique code for the department",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    user_id = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        tracking=True,
        help="User who created this department",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
        help="Whether this department is active",
    )

    sequence = fields.Integer(
        string="Sequence", 
        default=10, 
        help="Order sequence for sorting departments"
    )

    # ============================================================================
    # DEPARTMENT CLASSIFICATION
    # ============================================================================
    department_type = fields.Selection(
        [
            ("operations", "Operations Department"),
            ("compliance", "Compliance Department"),
            ("customer_service", "Customer Service"),
            ("administrative", "Administrative"),
            ("technical", "Technical Services"),
            ("management", "Management"),
        ],
        string="Department Type",
        required=True,
        default="operations",
        tracking=True,
        help="Type of department for workflow classification",
    )

    description = fields.Text(
        string="Department Description",
        tracking=True,
        help="Detailed description of department responsibilities",
    )

    # ============================================================================
    # ORGANIZATIONAL HIERARCHY
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Organization",
        tracking=True,
        domain=[("is_company", "=", True)],
        help="Parent organization that owns this department",
    )

    parent_department_id = fields.Many2one(
        "records.department",
        string="Parent Department",
        tracking=True,
        help="Parent department in organizational hierarchy",
    )

    child_department_ids = fields.One2many(
        "records.department",
        "parent_department_id",
        string="Child Departments",
        help="Sub-departments under this department",
    )

    department_level = fields.Integer(
        string="Department Level",
        compute="_compute_department_level",
        store=True,
        help="Hierarchical level of the department",
    )

    # ============================================================================
    # DEPARTMENT MANAGEMENT
    # ============================================================================
    department_manager_id = fields.Many2one(
        "res.users",
        string="Department Manager",
        tracking=True,
        help="Manager responsible for this department",
    )

    records_coordinator_id = fields.Many2one(
        "res.users",
        string="Records Coordinator",
        tracking=True,
        help="Records management coordinator for the department",
    )

    assistant_manager_id = fields.Many2one(
        "res.users",
        string="Assistant Manager",
        tracking=True,
        help="Assistant manager for the department",
    )

    # ============================================================================
    # USER ASSIGNMENT AND ROLES
    # ============================================================================
    user_ids = fields.Many2many(
        "res.users",
        "department_user_rel",
        "department_id",
        "user_id",
        string="Department Users",
        help="Users assigned to this department",
    )

    user_count = fields.Integer(
        string="User Count",
        compute="_compute_user_count",
        store=True,
        help="Number of users assigned to department",
    )

    # ============================================================================
    # CONTACT INFORMATION
    # ============================================================================
    email = fields.Char(
        string="Department Email",
        tracking=True,
        help="Primary email address for the department",
    )

    phone = fields.Char(
        string="Department Phone",
        tracking=True,
        help="Primary phone number for the department",
    )

    website = fields.Char(
        string="Department Website", 
        help="Department website or portal URL"
    )

    # ============================================================================
    # LOCATION AND FACILITIES
    # ============================================================================
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street 2")
    city = fields.Char(string="City")
    state_id = fields.Many2one("res.country.state", string="State")
    zip = fields.Char(string="ZIP Code")
    country_id = fields.Many2one("res.country", string="Country")

    # ============================================================================
    # STATE AND WORKFLOW MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current status of the department",
    )

    # ============================================================================
    # OPERATIONAL SETTINGS
    # ============================================================================
    cost_center = fields.Char(
        string="Cost Center",
        tracking=True,
        help="Cost center code for financial reporting",
    )

    budget_limit = fields.Monetary(
        string="Budget Limit",
        currency_field="currency_id",
        help="Annual budget limit for the department",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # ============================================================================
    # CUSTOMER AND SERVICE MANAGEMENT
    # ============================================================================
    customer_ids = fields.Many2many(
        "res.partner",
        "department_customer_rel",
        "department_id",
        "partner_id",
        string="Assigned Customers",
        domain=[("is_company", "=", True)],
        help="Customers assigned to this department",
    )

    customer_count = fields.Integer(
        string="Customer Count",
        compute="_compute_customer_count",
        store=True,
        help="Number of customers assigned to department",
    )

    service_area_ids = fields.Many2many(
        "records.location",
        string="Service Areas",
        help="Geographic service areas covered by this department",
    )

    # ============================================================================
    # PERFORMANCE METRICS
    # ============================================================================
    performance_score = fields.Float(
        string="Performance Score",
        compute="_compute_performance_metrics",
        store=True,
        help="Overall department performance score",
    )

    customer_satisfaction = fields.Float(
        string="Customer Satisfaction",
        compute="_compute_performance_metrics",
        store=True,
        help="Average customer satisfaction rating",
    )

    # ============================================================================
    # ADDITIONAL FIELDS
    # ============================================================================
    notes = fields.Text(string="Notes", help="Additional notes about the department")
    date_created = fields.Date(
        string="Date Created",
        default=fields.Date.today,
        help="Date when department was created",
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
    @api.depends("parent_department_id")
    def _compute_department_level(self):
        """Compute hierarchical level of the department"""
        for department in self:
            level = 0
            parent = department.parent_department_id
            while parent:
                level += 1
                parent = parent.parent_department_id
            department.department_level = level

    @api.depends("user_ids")
    def _compute_user_count(self):
        """Compute number of users assigned to department"""
        for department in self:
            department.user_count = len(department.user_ids)

    @api.depends("customer_ids")
    def _compute_customer_count(self):
        """Compute number of customers assigned to department"""
        for department in self:
            department.customer_count = len(department.customer_ids)

    @api.depends("customer_ids")
    def _compute_performance_metrics(self):
        """Compute performance metrics for the department"""
        for department in self:
            # Placeholder calculation - implement based on business requirements
            if department.customer_ids:
                department.performance_score = 85.0  # Default score
                department.customer_satisfaction = 4.2  # Default satisfaction
            else:
                department.performance_score = 0.0
                department.customer_satisfaction = 0.0

    # ============================================================================
    # CONSTRAINTS AND VALIDATION
    # ============================================================================
    _sql_constraints = [
        (
            "code_company_unique",
            "unique(code, company_id)",
            "Department code must be unique per company!",
        ),
        (
            "name_company_unique",
            "unique(name, company_id)",
            "Department name must be unique per company!",
        ),
    ]

    @api.constrains("parent_department_id")
    def _check_parent_recursion(self):
        """Check for recursive parent relationships"""
        if not self._check_recursion():
            raise ValidationError(_("Error! You cannot create recursive departments."))

    @api.constrains("budget_limit")
    def _check_budget_limit(self):
        """Validate budget limit is positive"""
        for department in self:
            if department.budget_limit and department.budget_limit < 0:
                raise ValidationError(_("Budget limit must be positive"))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate the department"""
        for department in self:
            if department.state != "draft":
                raise UserError(_("Only draft departments can be activated"))

            department.write({"state": "active"})
            department.message_post(body=_("Department activated"))

    def action_deactivate(self):
        """Deactivate the department"""
        for department in self:
            if department.state not in ["active"]:
                raise UserError(_("Only active departments can be deactivated"))

            # Check for active child departments
            active_children = department.child_department_ids.filtered(
                lambda d: d.state == "active"
            )
            if active_children:
                raise UserError(
                    _("Cannot deactivate department with active child departments: %s", ", ".join(active_children.mapped("name")))
                )

            department.write({"state": "inactive"})
            department.message_post(body=_("Department deactivated"))

    def action_archive(self):
        """Archive the department"""
        for department in self:
            if department.state != "inactive":
                raise UserError(_("Only inactive departments can be archived"))

            department.write({"state": "archived", "active": False})
            department.message_post(body=_("Department archived"))

    def action_view_users(self):
        """View users assigned to this department"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Department Users"),
            "res_model": "res.users",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.user_ids.ids)],
            "context": {"default_department_id": self.id},
        }

    def action_view_customers(self):
        """View customers assigned to this department"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Department Customers"),
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.customer_ids.ids)],
            "context": {"default_department_id": self.id},
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_department_hierarchy(self):
        """Get complete department hierarchy"""
        self.ensure_one()

        # Get all parent departments
        parents = []
        current = self.parent_department_id
        while current:
            parents.insert(0, current)
            current = current.parent_department_id

        # Get all child departments recursively
        def get_children(dept):
            children = []
            for child in dept.child_department_ids:
                children.append(child)
                children.extend(get_children(child))
            return children

        children = get_children(self)

        return {
            "parents": parents,
            "current": self,
            "children": children,
            "hierarchy_path": " > ".join([p.name for p in parents] + [self.name]),
        }

    def check_user_access(self, user_id):
        """Check if user has access to this department"""
        self.ensure_one()
        user = self.env["res.users"].browse(user_id)

        # Check direct assignment
        if user in self.user_ids:
            return True

        # Check if user is manager
        if user == self.department_manager_id:
            return True

        # Check if user is coordinator
        if user == self.records_coordinator_id:
            return True

        return False

    def assign_customer(self, partner_id):
        """Assign customer to department"""
        self.ensure_one()
        partner = self.env["res.partner"].browse(partner_id)

        if partner not in self.customer_ids:
            self.customer_ids = [(4, partner_id)]
            self.message_post(
                body=_("Customer %s assigned to department", partner.name)
            )

    def unassign_customer(self, partner_id):
        """Remove customer from department"""
        self.ensure_one()
        partner = self.env["res.partner"].browse(partner_id)

        if partner in self.customer_ids:
            self.customer_ids = [(3, partner_id)]
            self.message_post(
                body=_("Customer %s removed from department", partner.name)
            )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display with hierarchy"""
        result = []
        for department in self:
            if department.parent_department_id:
                name = _(
                    "%s / %s",
                    department.parent_department_id.name,
                    department.name,
                )
            else:
                name = department.name
            result.append((department.id, name))
        return result

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Enhanced search by name or code"""
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                "|",
                ("name", operator, name),
                ("code", operator, name),
                ("description", operator, name),
            ]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def get_departments_by_type(self, department_type):
        """Get all departments of specific type"""
        return self.search(
            [("department_type", "=", department_type), ("state", "=", "active")]
        )

    def get_department_summary(self):
        """Get summary information for reporting"""
        self.ensure_one()

        return {
            "name": self.name,
            "code": self.code,
            "type": self.department_type,
            "state": self.state,
            "manager": (
                self.department_manager_id.name if self.department_manager_id else None
            ),
            "user_count": self.user_count,
            "customer_count": self.customer_count,
            "performance_score": self.performance_score,
            "budget_limit": self.budget_limit,
        }
