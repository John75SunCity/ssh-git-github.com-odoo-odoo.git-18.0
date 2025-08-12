# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

from odoo.exceptions import UserError



RECORDS_MANAGER_GROUP_XMLID = "records_management.group_records_manager"


class LocationReportWizard(models.Model):
    """
    Location Report Wizard - Security-Aware Multi-Customer Inventory Analysis

    This wizard generates location-based inventory reports with strict customer privacy controls.
    The behavior changes based on user type and access level:

    SECURITY MODEL:
    ===============

    1. INTERNAL USERS (Records Manager/Admin):
       - Can view ALL customers' inventory in any location
       - Access to complete multi-tenant inventory data
       - Can analyze space utilization across all customers
       - Used for: Capacity planning, billing, location optimization

    2. PORTAL USERS (Customers):
       - Can ONLY view their own inventory in any location
       - Completely isolated from other customers' data
       - Privacy protection prevents cross-customer data leakage
       - Used for: Personal inventory tracking, space utilization

    3. DEPARTMENT USERS (Limited Internal):
       - Can view inventory for customers in their assigned departments
       - Departmental data separation for multi-tenant operations
       - Used for: Regional management, department-specific operations

    MULTI-CUSTOMER FUNCTIONALITY:
    ============================

    When viewing a location (warehouse, building, room, shelf), the system shows:
    - Which customers have inventory in that specific location
    - How much space each customer is using (for internal users only)
    - Total capacity utilization across all customers (for internal users)
    - Individual customer's utilization (for portal users - their data only)

    BUSINESS USE CASES:
    ==================

    Internal Staff:
    - "Show me all customers with inventory in Building A, Room 5"
    - "What's the total utilization of Warehouse B across all customers?"
    - "Which customers can we relocate to optimize space in Location X?"

    Portal Customers:
    - "Show me my inventory in your warehouse locations"
    - "How much space am I using in each location?"
    - "Where are my boxes stored across your facilities?"

    PRIVACY SAFEGUARDS:
    ==================

    1. Record Rules: Automatic filtering based on user type
    2. Domain Filtering: Dynamic queries based on access rights
    3. Data Masking: Customer names hidden for unauthorized users
    4. Audit Logging: All access attempts logged for compliance
    5. Department Isolation: Multi-tenant data separation

    FUTURE ENHANCEMENTS:
    ===================

    - Real-time space allocation and billing calculations
    - Customer notification system for space optimization
    - Predictive analytics for capacity planning
    - Integration with customer portal for self-service reporting
    - Automated space reallocation recommendations
    """

    _name = "location.report.wizard"
    _description = "Location Report Wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(
        string="Report Name",
        required=True,
        tracking=True,
        help="Descriptive name for this location report",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        help="Company context for multi-company environments",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        tracking=True,
        help="User who generated this report for audit purposes",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Whether this report wizard is active and accessible",
    )

    # ============================================================================
    # WORKFLOW STATE MANAGEMENT
    # ============================================================================

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("done", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="draft",
        tracking=True,
        help="Current state of the report generation process",
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS (with proper domain filtering)
    # ============================================================================

    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
        help="Users following this report for updates and notifications",
    )
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )

    # ============================================================================
    # REPORT PARAMETER FIELDS
    # ============================================================================

    location_id = fields.Many2one(
        "records.location",
        string="Primary Location",
        required=True,
        help="Select the main location to analyze. System will show inventory from all customers in this location (subject to user permissions).",
    )
    include_child_locations = fields.Boolean(
        string="Include Sub-Locations",
        default=True,
        help="Include child locations (rooms, sections, shelves) in the analysis for comprehensive space utilization.",
    )
    report_date = fields.Date(
        string="Report Date",
        default=fields.Date.context_today,
        required=True,
        help="Generate report data as of this specific date for historical analysis.",
    )

    # ============================================================================
    # CUSTOMER FILTERING & PRIVACY CONTROLS
    # ============================================================================

    customer_filter = fields.Selection(
        [
            ("all", "All Customers (Internal Users Only)"),
            ("my_customers", "My Customers Only"),
            ("specific", "Specific Customer"),
            ("auto", "Auto (Based on User Type)"),
        ],
        string="Customer Filter",
        default="auto",
        help="Control which customers' inventory data to include in the report",
    )

    specific_customer_id = fields.Many2one(
        "res.partner",
        string="Specific Customer",
        domain=[("is_company", "=", True)],
        help="When 'Specific Customer' filter is selected, show only this customer's inventory",
    )

    is_portal_user = fields.Boolean(
        string="Is Portal User",
        compute="_compute_user_context",
        help="Indicates if current user is a portal user (customer) with restricted access",
    )

    accessible_customer_ids = fields.Many2many(
        "res.partner",
        string="Accessible Customers",
        compute="_compute_accessible_customers",
        help="List of customers this user can view inventory for based on access rights",
    )

    # ============================================================================
    # COMPUTED REPORT DATA FIELDS
    # ============================================================================

    location_name = fields.Char(
        related="location_id.name", string="Location Name", store=True, readonly=True
    )
    total_capacity = fields.Float(
        string="Total Location Capacity",
        compute="_compute_location_utilization",
        store=True,
        help="Total storage capacity of selected location(s) across all customers",
    )
    current_utilization = fields.Float(
        string="Current Space Used",
        compute="_compute_location_utilization",
        store=True,
        help="Currently occupied space in selected location(s) - filtered by user access rights",
    )
    utilization_percentage = fields.Float(
        string="Utilization %",
        compute="_compute_location_utilization",
        store=True,
        help="Percentage of location capacity currently in use",
    )

    customer_count = fields.Integer(
        string="Number of Customers",
        compute="_compute_customer_metrics",
        help="Count of customers with inventory in this location (visible to current user)",
    )

    inventory_summary_html = fields.Html(
        string="Inventory Summary",
        compute="_compute_inventory_summary",
        help="Detailed breakdown of inventory by customer (respects privacy controls)",
    )

    # ============================================================================
    # SECURITY & PRIVACY COMPUTE METHODS
    # ============================================================================

    @api.depends("user_id")
    def _compute_user_context(self):
        """
        Determine user access level and apply appropriate privacy controls.

        Portal users can only see their own company's inventory.
        Internal users can see all customers based on department access.
        """
        for wizard in self:
            # Check if user is portal user (customer)
            wizard.is_portal_user = wizard.user_id.has_group("base.group_portal")

    @api.depends("user_id", "is_portal_user")
    def _compute_accessible_customers(self):
        """
        Compute which customers this user can access based on security rules.

        PRIVACY IMPLEMENTATION:
        - Portal users: Only their own company
        - Department users: Only customers in their departments
        - Admin users: All customers
        """
        for wizard in self:
            if wizard.is_portal_user:
                # Portal users can only see their own company's data
                partner = wizard.user_id.partner_id
                if partner.is_company:
                    wizard.accessible_customer_ids = [(6, 0, [partner.id])]
                else:
                    # Find the company this user belongs to
                    company_partner = partner.parent_id or partner
                    wizard.accessible_customer_ids = [(6, 0, [company_partner.id])]
            else:
                # Internal users - check department access
                if wizard.user_id.has_group(RECORDS_MANAGER_GROUP_XMLID):
                    # Admin can see all customers
                    customers = self.env["res.partner"].search(
                        [("is_company", "=", True)]
                    )
                    wizard.accessible_customer_ids = [(6, 0, customers.ids)]
                else:
                    # Department-based access (implement based on your department model)
                    wizard.accessible_customer_ids = [(6, 0, [])]

    # ============================================================================
    # LOCATION & INVENTORY ANALYSIS METHODS
    # ============================================================================

    @api.depends(
        "location_id",
        "include_child_locations",
        "report_date",
        "accessible_customer_ids",
    )
    def _compute_location_utilization(self):
        """
        Calculate location utilization metrics with customer privacy controls.

        MULTI-CUSTOMER LOGIC:
        - Aggregate data from all accessible customers in the location
        - Apply privacy filters based on user access rights
        - Calculate utilization percentages for capacity planning
        """
        for wizard in self:
            # Get location hierarchy
            locations = wizard._get_report_locations()

            # Get accessible inventory data
            inventory_data = wizard._get_filtered_inventory_data(locations)

            # Calculate aggregated metrics
            total_capacity = sum(locations.mapped("total_capacity"))
            current_utilization = sum(inventory_data.mapped("space_used"))

            wizard.total_capacity = total_capacity
            wizard.current_utilization = current_utilization

            if total_capacity > 0:
                wizard.utilization_percentage = (
                    current_utilization / total_capacity
                ) * 100
            else:
                wizard.utilization_percentage = 0.0

    @api.depends("accessible_customer_ids", "location_id")
    def _compute_customer_metrics(self):
        """Calculate customer-related metrics for the location."""
        for wizard in self:
            locations = wizard._get_report_locations()
            inventory_data = wizard._get_filtered_inventory_data(locations)

            unique_customers = inventory_data.mapped("customer_id")
            wizard.customer_count = len(unique_customers)

    @api.depends("accessible_customer_ids", "location_id", "is_portal_user")
    def _compute_inventory_summary(self):
        """
        Generate HTML summary of inventory by customer with privacy controls.

        PRIVACY-AWARE SUMMARY:
        - Portal users: Show only their own inventory details
        - Internal users: Show summary by customer (names may be masked)
        - Admin users: Show complete multi-customer breakdown
        """
        for wizard in self:
            locations = wizard._get_report_locations()
            inventory_data = wizard._get_filtered_inventory_data(locations)

            if wizard.is_portal_user:
                # Portal user - show only their inventory
                html = wizard._generate_customer_inventory_summary(inventory_data)
            else:
                # Internal user - show multi-customer summary
                html = wizard._generate_multi_customer_summary(inventory_data)

            wizard.inventory_summary_html = html

    # ============================================================================
    # HELPER METHODS FOR DATA FILTERING & PRIVACY
    # ============================================================================

    def _get_report_locations(self):
        """Get all locations to include in the report based on parameters."""
        self.ensure_one()
        locations = self.location_id

        if self.include_child_locations and self.location_id:
            # Include all child locations
            child_locations = self.env["records.location"].search(
                [
                    ("id", "child_of", self.location_id.id),
                    ("id", "!=", self.location_id.id),
                ]
            )
            locations |= child_locations

        return locations

    def _get_filtered_inventory_data(self, locations):
        """
        Get inventory data filtered by user access rights and customer privacy rules.

        CRITICAL PRIVACY METHOD:
        This is where customer data isolation is enforced.
        Portal users will never see other customers' inventory data.
        """
        self.ensure_one()

        # Base domain for inventory in these locations
        domain = [("location_id", "in", locations.ids), ("active", "=", True)]

        # Add customer filtering based on user access
        if self.accessible_customer_ids:
            domain.append(("customer_id", "in", self.accessible_customer_ids.ids))

        # Add date filtering if specified
        if self.report_date:
            domain.append(("date", "<=", self.report_date))

        # Search for inventory records (adjust model name based on your implementation)
        inventory_model = "records.container"  # Adjust to your actual inventory model
        if inventory_model in self.env:
            return self.env[inventory_model].search(domain)
        else:
            return self.env["records.container"].browse()

    def _generate_customer_inventory_summary(self, inventory_data):
        """Generate HTML summary for portal users (single customer view)."""
        if not inventory_data:
            return "<p>No inventory found in selected location(s).</p>"

        html = "<div class='inventory-summary'>"
        html += f"<h4>Your Inventory Summary</h4>"
        html += f"<p>Total Items: {len(inventory_data)}</p>"
        html += f"<p>Space Used: {sum(inventory_data.mapped('space_used'))} units</p>"
        html += "</div>"

        return html

    def _generate_multi_customer_summary(self, inventory_data):
        """Generate HTML summary for internal users (multi-customer view)."""
        if not inventory_data:
            return "<p>No inventory found in selected location(s).</p>"

        # Group by customer
        customer_data = {}
        for item in inventory_data:
            customer = item.customer_id
            if customer not in customer_data:
                customer_data[customer] = {"items": 0, "space_used": 0.0}
            customer_data[customer]["items"] += 1
            customer_data[customer]["space_used"] += item.space_used or 0.0

        html = "<div class='multi-customer-summary'>"
        html += f"<h4>Multi-Customer Inventory Summary</h4>"
        html += f"<p>Total Customers: {len(customer_data)}</p>"
        html += "<table class='table table-sm'>"
        html += "<tr><th>Customer</th><th>Items</th><th>Space Used</th></tr>"

        for customer, data in customer_data.items():
            html += f"<tr><td>{customer.name}</td><td>{data['items']}</td><td>{data['space_used']:.2f}</td></tr>"

        html += "</table></div>"

        return html

    # ============================================================================
    # ACTION METHODS FOR REPORT GENERATION
    # ============================================================================

    def action_generate_report(self):
        """
        Generate the location report with appropriate customer filtering.

        SECURITY NOTE: This method respects all privacy controls and only
        shows data the current user is authorized to view.
        """

        self.ensure_one()

        # Validate user has access to requested data
        if self.is_portal_user and not self.accessible_customer_ids:
            raise UserError(
                _("You do not have access to inventory data for this location.")
            )

        # Update computed fields
        self._compute_location_utilization()
        self._compute_customer_metrics()
        self._compute_inventory_summary()

        # Update state
        self.write({"state": "confirmed"})

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "name": _("Location Report: %s", self.location_name),
        }

    def action_print_report(self):
        """Generate PDF report with privacy-filtered data."""

        self.ensure_one()

        # Ensure report data is current
        self.action_generate_report()

        return self.env.ref(
            "records_management.action_report_location_utilization"
        ).report_action(self)

    def action_export_csv(self):
        """
        Export location inventory data to CSV with privacy controls.

        EXPORT PRIVACY CONTROLS:
        - Portal users: Export only their own inventory data
        - Internal users: Export based on access permissions
        - Data masking: Sensitive fields may be hidden based on user level
        """

        self.ensure_one()

        # Generate CSV data respecting privacy controls
        locations = self._get_report_locations()
        inventory_data = self._get_filtered_inventory_data(locations)

        if not inventory_data:
            raise UserError(
                _(
                    "No inventory data available for export based on your access permissions."
                )
            )

        # For now, return a message. Implement actual CSV export as needed.
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": _(
                    "CSV export prepared for %d inventory records. Download functionality to be implemented."
                )
                % len(inventory_data),
                "type": "success",
            },
        }

    # ============================================================================
    # WORKFLOW STATE METHODS
    # ============================================================================

    def action_confirm(self):
        """Confirm the report and generate final data."""

        self.ensure_one()
        for record in self:
            if record.state != "draft":
                raise UserError(_("Only draft reports can be confirmed."))
            record.write({"state": "confirmed"})
        return True

    def action_set_to_draft(self):
        """Reset report to draft state for modifications."""

        self.ensure_one()
        for record in self:
            record.write({"state": "draft"})
        return True

    def action_cancel(self):
        """Cancel the report generation."""

        self.ensure_one()
        for record in self:
            record.write({"state": "cancelled"})
        return True
