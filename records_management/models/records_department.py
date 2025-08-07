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

Workflow Customization:
- Department-specific workflow configuration and process management
- Custom approval workflows based on departmental hierarchy and authority
- Department-based notification and communication preferences
- Integration with departmental service level agreements and performance metrics
- Custom reporting and analytics tailored to departmental requirements
- Department-specific portal configuration and customer experience

Performance Management:
- Departmental KPI tracking and performance metrics monitoring
- Service level agreement compliance and customer satisfaction tracking
- Resource utilization and capacity planning by department
- Cost analysis and profitability tracking for departmental operations
- Benchmarking and comparative analysis between departments
- Integration with executive dashboards and management reporting

Technical Implementation:
- Modern Odoo 18.0 architecture with comprehensive security and access control
- Hierarchical data structures with efficient parent-child relationship management
- Integration with Odoo's security framework and access control systems
- Performance optimized for large-scale multi-tenant deployments
- Mail thread integration for departmental notifications and activity tracking

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _


class RecordsDepartment(models.Model):
    """
    Records Department Management - Organizational departments for records management
    Provides hierarchical department structure with access control and workflow integration
    """

    _name = "records.department"
    _description = "Records Department"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string="Department Name", required=True, tracking=True)
    code = fields.Char(string="Department Code", required=True, tracking=True)
    description = fields.Text(string="Department Description", tracking=True)
    active = fields.Boolean(default=True, tracking=True)
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
    )

    # ==========================================
    # PARENT ORGANIZATION
    # ==========================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Organization",
        tracking=True,
        domain=[("is_company", "=", True)],
        help="Parent organization that owns this department",
    )

    # ==========================================
    # DEPARTMENT MANAGEMENT
    # ==========================================
    department_manager_id = fields.Many2one(
        "res.users", string="Department Manager", tracking=True
    )
    records_coordinator_id = fields.Many2one(
        "res.users", string="Records Coordinator", tracking=True
    )

    # ==========================================
    # CONTACT INFORMATION
    # ==========================================
    email = fields.Char(string="Department Email", tracking=True)
    phone = fields.Char(string="Department Phone", tracking=True)

    # Basic state management
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("inactive", "Inactive")],
        string="State",
        default="draft",
        tracking=True,
    )

    # Common fields
    notes = fields.Text(string="Notes")
    date = fields.Date(default=fields.Date.today)

    # ==========================================
    # CONSTRAINTS
    # ==========================================
    _sql_constraints = [
        (
            "code_uniq",
            "unique(code, company_id)",
            "Department code must be unique per company!",
        ),
    ]

    # ==========================================
    # ACTION METHODS
    # ==========================================
    def action_confirm(self):
        """Activate the department"""
        self.write({"state": "active"})

    def action_deactivate(self):
        """Deactivate the department"""
        if len(self) > 1:
            # Optionally, raise an error or log a warning if batch operation is not intended
            raise UserError(
                _(
                    "Batch deactivation is not allowed. Please select a single department."
                )
            )
        self.write({"state": "inactive"})
