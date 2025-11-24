# -*- coding: utf-8 -*-
"""
Account Move Line Extensions for Work Order Billing Integration

Extends account.move.line model to link invoice lines to work orders and
provides comprehensive Records Management service billing integration
with NAID compliance tracking and audit trails.

Author: Records Management System
Version: 18.0.0.2.29
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMoveLine(models.Model):
    """
    Account Move Line Extensions for Records Management

    Extends the standard account.move.line model to provide comprehensive
    integration with Records Management work orders, billing configurations,
    and NAID compliance requirements for audit trail maintenance.
    """

    _inherit = "account.move.line"

    # ============================================================================
    # WORK ORDER INTEGRATION FIELDS
    # ============================================================================
    work_order_id = fields.Reference(
        selection=[
            ("records.retrieval.order", "Records Retrieval"),  # unified model name
            ("shredding.service", "Shredding Service"),
            ("pickup.request", "Pickup Request"),
        ],
        string="Related Work Order",
        help="Work order that generated this invoice line",
    )

    work_order_coordinator_id = fields.Many2one(
        "res.users",
        string="Work Order Coordinator",
        help="Coordinator for consolidated billing and work order management",
    )

    work_order_reference = fields.Char(string="Work Order Reference", help="Reference number of the related work order")

    work_order_date = fields.Date(string="Work Order Date", help="Date when the work order was created")

    # ============================================================================
    # RECORDS MANAGEMENT SERVICE INTEGRATION
    # ============================================================================
    records_related = fields.Boolean(
        string="Records Related",
        default=False,
        help="Indicates if this invoice line is related to records management services",
    )

    records_service_type = fields.Selection(
        [
            ("storage", "Storage Services"),
            ("retrieval", "Retrieval Services"),
            ("destruction", "Destruction Services"),
            ("pickup", "Pickup Services"),
            ("scanning", "Scanning Services"),
        ],
        string="Records Service Type",
        help="Type of records management service",
    )

    service_category = fields.Selection(
        [
            ("onsite", "On-Site Service"),
            ("offsite", "Off-Site Service"),
            ("portal", "Portal Service"),
        ],
        string="Service Category",
        help="Category of service delivery",
    )

    # ============================================================================
    # CONTAINER AND DOCUMENT TRACKING
    # ============================================================================
    container_count = fields.Integer(string="Container Count", help="Number of containers involved in this service")

    container_ids = fields.Many2many(
        "records.container",
        "account_line_container_rel",
        "line_id",
        "container_id",
        string="Related Containers",
        help="Containers related to this billing line",
    )

    container_types = fields.Char(
        string="Container Types",
        compute="_compute_container_types",
        store=True,
        help="Comma-separated string of unique container type names involved (e.g., TYPE 01, TYPE 02)",
    )

    document_count = fields.Integer(
        string="Document Count", compute="_compute_document_count", store=True, help="Number of documents processed"
    )

    file_count = fields.Integer(string="File Count", help="Number of individual files processed")

    # ============================================================================
    # DESTRUCTION AND SHREDDING SERVICES
    # ============================================================================
    destruction_service_id = fields.Many2one(
        "shredding.service", string="Destruction Service", help="Related destruction service"
    )

    shredding_weight_lbs = fields.Float(
        string="Shredding Weight (lbs)", digits="Stock Weight", help="Weight of materials shredded in pounds"
    )

    shredding_weight_kg = fields.Float(
        string="Shredding Weight (kg)",
        compute="_compute_weight_kg",
        store=True,
        digits="Stock Weight",
        help="Weight of materials shredded in kilograms",
    )

    destruction_method = fields.Selection(
        [
            ("cross_cut", "Cross Cut Shredding"),
            ("strip_cut", "Strip Cut Shredding"),
            ("micro_cut", "Micro Cut Shredding"),
        ],
        string="Destruction Method",
        help="Method used for document destruction",
    )

    certificate_of_destruction_id = fields.Many2one(
        "naid.certificate", string="Certificate of Destruction", help="Generated certificate of destruction"
    )

    # ============================================================================
    # PICKUP AND LOGISTICS
    # ============================================================================
    pickup_request_id = fields.Many2one("pickup.request", string="Pickup Request", help="Related pickup request")

    pickup_date = fields.Date(string="Pickup Date", help="Date when pickup was performed")

    delivery_date = fields.Date(string="Delivery Date", help="Date when delivery was completed")

    route_id = fields.Many2one("pickup.route", string="Pickup Route", help="Route used for pickup/delivery")

    driver_id = fields.Many2one("hr.employee", string="Driver", help="Employee who performed the pickup/delivery")

    vehicle_id = fields.Many2one("fleet.vehicle", string="Vehicle", help="Vehicle used for pickup/delivery")

    # ============================================================================
    # LOCATION AND STORAGE TRACKING
    # ============================================================================
    storage_location_id = fields.Many2one(
        "stock.location", string="Storage Location", help="Primary storage location for records"
    )

    origin_location_id = fields.Many2one(
        "stock.location", string="Origin Location", help="Location where items were picked up from"
    )

    destination_location_id = fields.Many2one(
        "stock.location", string="Destination Location", help="Location where items were delivered to"
    )

    storage_period_months = fields.Integer(
        string="Storage Period (Months)", help="Number of months for storage billing"
    )

    storage_start_date = fields.Date(string="Storage Start Date", help="Date when storage period began")

    storage_end_date = fields.Date(string="Storage End Date", help="Date when storage period ended")

    # ============================================================================
    # BILLING CONFIGURATION AND RATES
    # ============================================================================
    billing_config_id = fields.Many2one(
        "records.billing.config", string="Billing Configuration", help="Billing configuration used for this line"
    )

    base_rate_id = fields.Many2one("base.rates", string="Base Rate", help="Base rate applied to this service")

    customer_rate_id = fields.Many2one(
        "customer.negotiated.rate", string="Customer Rate", help="Customer-specific negotiated rate"
    )

    rate_type = fields.Selection(
        [
            ("standard", "Standard Rate"),
            ("negotiated", "Negotiated Rate"),
        ],
        string="Rate Type",
        help="Type of rate applied",
    )

    unit_rate = fields.Float(string="Unit Rate", digits="Product Price", help="Rate per unit for this service")

    rate_unit = fields.Selection(
        [
            ("container", "Per Container"),
            ("pound", "Per Pound"),
            ("hour", "Per Hour"),
        ],
        string="Rate Unit",
        help="Unit of measurement for billing rate",
    )

    # ============================================================================
    # COMPLIANCE AND AUDIT
    # ============================================================================
    naid_audit_required = fields.Boolean(
        string="NAID Audit Required", default=False, help="Indicates if NAID audit trail is required"
    )

    naid_compliant = fields.Boolean(
        string="NAID Compliant", default=True, help="Whether this service meets NAID AAA standards"
    )

    audit_trail_created = fields.Boolean(
        string="Audit Trail Created", default=False, help="Whether audit trail has been created for this line"
    )

    compliance_notes = fields.Text(
        string="Compliance Notes", help="Notes regarding compliance requirements and fulfillment"
    )

    chain_of_custody_id = fields.Many2one(
        "chain.of.custody", string="Chain of Custody", help="Chain of custody record for this service"
    )

    # ============================================================================
    # CUSTOMER AND DEPARTMENT TRACKING
    # ============================================================================
    records_department_id = fields.Many2one(
        "records.department", string="Records Department", help="Customer department for records management"
    )

    customer_contact_id = fields.Many2one(
        "res.partner", string="Customer Contact", help="Primary customer contact for this service"
    )

    customer_reference = fields.Char(string="Customer Reference", help="Customer's internal reference for this service")

    portal_request_id = fields.Many2one(
        "portal.request", string="Portal Request", help="Portal request that initiated this service"
    )

    # ============================================================================
    # SERVICE METRICS AND ANALYTICS
    # ============================================================================
    service_duration_hours = fields.Float(
        string="Service Duration (Hours)", digits=(6, 2), help="Total time spent on this service"
    )

    travel_time_hours = fields.Float(
        string="Travel Time (Hours)", digits=(6, 2), help="Time spent traveling to/from customer location"
    )

    service_efficiency_score = fields.Float(
        string="Service Efficiency Score", digits=(5, 2), help="Calculated efficiency score for this service"
    )

    customer_satisfaction_rating = fields.Selection(
        [("1", "Poor"), ("2", "Fair"), ("3", "Good"), ("4", "Very Good"), ("5", "Excellent")],
        string="Customer Satisfaction",
        help="Customer satisfaction rating",
    )

    # ============================================================================
    # NOTES AND OBSERVATIONS
    # ============================================================================
    service_notes = fields.Text(string="Service Notes", help="Detailed notes about the service performed")

    internal_notes = fields.Text(string="Internal Notes", help="Internal notes not visible to customer")

    special_instructions = fields.Text(string="Special Instructions", help="Special handling or service instructions")

    # ============================================================================
    # LEGACY COMPATIBILITY
    # ============================================================================
    inherit_id = fields.Many2one(
        "account.move.line", string="Inherited Line", help="Parent accounting line for inheritance tracking"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("container_ids", "container_ids.container_type_id", "container_ids.container_type_id.name")
    def _compute_container_types(self):
        """Compute string representation of container types"""
        for line in self:
            if line.container_ids:
                types = line.container_ids.mapped("container_type_id.name")
                unique_types = sorted(set(types))
                line.container_types = ", ".join(unique_types) if unique_types else ""
            else:
                line.container_types = ""

    @api.depends("shredding_weight_lbs")
    def _compute_weight_kg(self):
        """Convert weight from lbs to kg"""
        for line in self:
            if line.shredding_weight_lbs:
                line.shredding_weight_kg = line.shredding_weight_lbs * 0.453592
            else:
                line.shredding_weight_kg = 0.0

    @api.depends("container_ids", "container_ids.document_count")
    def _compute_document_count(self):
        """Compute total document count from related containers."""
        for line in self:
            if line.container_ids:
                line.document_count = sum(
                    container.document_count
                    for container in line.container_ids
                    if hasattr(container, "document_count") and container.document_count
                )
            else:
                line.document_count = 0

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange("work_order_id")
    def _onchange_work_order_id(self):
        """Update related fields when work order changes"""
        if self.work_order_id:
            work_order = self.work_order_id

            # Set basic information
            self.records_related = True
            self.work_order_reference = work_order.name if hasattr(work_order, "name") else ""
            create_date = getattr(work_order, "create_date", None)
            if create_date and hasattr(create_date, "date"):
                self.work_order_date = create_date.date()
            else:
                self.work_order_date = False

            # Set service type based on work order model using a mapping
            model_service_type_map = {
                "document.retrieval.work.order": "retrieval",
                "shredding.service": "destruction",
                "pickup.request": "pickup",
            }
            model_name = getattr(self.work_order_id, "_name", None)
            service_type = model_service_type_map.get(model_name) if model_name else None
            self.records_service_type = service_type if service_type else False

            # Set partner information
            if hasattr(work_order, "partner_id") and work_order.partner_id:
                self.partner_id = work_order.partner_id

            # Set container_ids and container_count from work order if available
            if hasattr(work_order, "container_ids"):
                container_records = work_order.container_ids
                if container_records:
                    self.container_ids = [(6, 0, container_records.ids)]
                    self.container_count = len(container_records)
                else:
                    self.container_ids = [(5, 0, 0)]
                    self.container_count = 0
            else:
                self.container_ids = [(5, 0, 0)]
                self.container_count = 0

    @api.onchange("records_service_type")
    def _onchange_records_service_type(self):
        """Update fields based on service type"""
        if self.records_service_type:
            self.records_related = True

            # Set default NAID audit requirement for certain services
            if self.records_service_type in ["destruction", "retrieval"]:
                self.naid_audit_required = True
            else:
                self.naid_audit_required = False

    @api.onchange("destruction_service_id")
    def _onchange_destruction_service_id(self):
        """Update fields when destruction service changes"""
        if self.destruction_service_id:
            service = self.destruction_service_id
            self.records_service_type = "destruction"
            self.shredding_weight_lbs = service.total_weight if hasattr(service, "total_weight") else 0.0
            self.destruction_method = service.destruction_method if hasattr(service, "destruction_method") else False
            self.naid_audit_required = True

    @api.onchange("pickup_request_id")
    def _onchange_pickup_request_id(self):
        """Update fields when pickup request changes"""
        if self.pickup_request_id:
            pickup = self.pickup_request_id
            self.records_service_type = "pickup"
            self.pickup_date = pickup.pickup_date if hasattr(pickup, "pickup_date") else False
            if hasattr(pickup, "container_ids") and pickup.container_ids:
                self.container_ids = [(6, 0, pickup.container_ids.mapped("id"))]
                self.container_count = len(pickup.container_ids)
            else:
                self.container_ids = [(5, 0, 0)]
                self.container_count = 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_create_audit_trail(self):
        """Create NAID audit trail for this invoice line."""
        self.ensure_one()

        if not self.records_related:
            raise UserError(_("Cannot create audit trail for non-records related invoice lines."))
        if self.audit_trail_created:
            raise UserError(_("Audit trail already exists for this invoice line."))

        # Create audit log entry
        service_type_desc = self.records_service_type or "unknown service"
        audit_vals = {
            "action_type": "invoice_line_created",
            "user_id": self.env.user.id,
            "timestamp": fields.Datetime.now(),
            "description": _("Invoice line created for %s", service_type_desc),
            "invoice_line_id": self.id,
            "amount": self.price_total,
            "naid_compliant": self.naid_compliant,
        }

        if "naid.audit.log" in self.env:
            self.env["naid.audit.log"].create(audit_vals)

        self.audit_trail_created = True
        self.message_post(body=_("NAID audit trail created for invoice line."))

    def action_view_work_order(self):
        """View the related work order"""
        self.ensure_one()

        if not self.work_order_id:
            raise UserError(_("No work order linked to this invoice line."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Related Work Order"),
            "res_model": self.work_order_id._name,
            "res_id": self.work_order_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_containers(self):
        """View related containers"""
        self.ensure_one()

        if not self.container_ids:
            raise UserError(_("No containers linked to this invoice line."))

        # Get container IDs safely
        container_ids_list = getattr(self.container_ids, "ids", [])

        return {
            "type": "ir.actions.act_window",
            "name": _("Related Containers"),
            "res_model": "records.container",
            "view_mode": "list,form",
            "domain": [("id", "in", container_ids_list)],
            "context": {"default_partner_id": self.partner_id.id if self.partner_id else False},
        }

    def action_view_destruction_certificate(self):
        """View destruction certificate"""
        self.ensure_one()

        if not self.certificate_of_destruction_id:
            raise UserError(_("No destruction certificate available."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Certificate of Destruction"),
            "res_model": "naid.certificate",
            "res_id": self.certificate_of_destruction_id.id,
            "view_mode": "form",
            "target": "current",
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("shredding_weight_lbs")
    def _check_shredding_weight(self):
        """Validate shredding weight"""
        for line in self:
            if line.shredding_weight_lbs and line.shredding_weight_lbs < 0:
                raise ValidationError(_("Shredding weight cannot be negative."))

    @api.constrains("container_count")
    def _check_container_count(self):
        """Validate container count"""
        for line in self:
            if line.container_count and line.container_count < 0:
                raise ValidationError(_("Container count cannot be negative."))

    @api.constrains("storage_start_date", "storage_end_date")
    def _check_storage_dates(self):
        """Validate storage date sequence"""
        for line in self:
            if line.storage_start_date and line.storage_end_date and line.storage_start_date > line.storage_end_date:
                raise ValidationError(_("Storage start date cannot be after storage end date."))

    @api.constrains("pickup_date", "delivery_date")
    def _check_pickup_delivery_dates(self):
        """Validate pickup and delivery date sequence"""
        for line in self:
            if line.pickup_date and line.delivery_date and line.pickup_date > line.delivery_date:
                raise ValidationError(_("Pickup date cannot be after delivery date."))

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def get_service_summary(self):
        """Get summary information for this service line."""
        self.ensure_one()

        return {
            "service_type": self.records_service_type,
            "service_category": self.service_category,
            "container_count": self.container_count,
            "document_count": self.document_count,
            "weight_processed": self.shredding_weight_lbs,
            "duration_hours": self.service_duration_hours,
            "naid_compliant": self.naid_compliant,
            "audit_trail_created": self.audit_trail_created,
            "customer_satisfaction": self.customer_satisfaction_rating,
        }

    def calculate_efficiency_metrics(self):
        """Calculate service efficiency metrics"""
        self.ensure_one()

        efficiency_score = 100.0  # Base score

        # Adjust based on service duration vs standard
        if self.service_duration_hours and self.container_count:
            standard_time_per_container = 0.5  # 30 minutes per container
            expected_time = self.container_count * standard_time_per_container

            if self.service_duration_hours > expected_time:
                # Took longer than expected
                efficiency_score -= ((self.service_duration_hours - expected_time) / expected_time) * 20
            else:
                # Faster than expected
                efficiency_score += ((expected_time - self.service_duration_hours) / expected_time) * 10

        # Adjust based on customer satisfaction
        if self.customer_satisfaction_rating:
            rating = int(self.customer_satisfaction_rating)
            efficiency_score += (rating - 3) * 5  # +/-10 points for excellent/poor

        return max(0.0, min(100.0, efficiency_score))

    @api.model
    def get_records_billing_summary(self, date_from=None, date_to=None):
        """Get billing summary for records management services."""
        domain = [("records_related", "=", True)]

        if date_from:
            domain.append(("move_id.invoice_date", ">=", date_from))
        if date_to:
            domain.append(("move_id.invoice_date", "<=", date_to))

        lines = self.search(domain)

        summary = {
            "total_revenue": sum(lines.mapped("price_total")),
            "total_containers": sum(lines.mapped("container_count")),
            "total_weight_shredded": sum(lines.mapped("shredding_weight_lbs")),
            "service_breakdown": {},
            "compliance_stats": {
                "naid_compliant_lines": len(lines.filtered("naid_compliant")),
                "audit_trails_created": len(lines.filtered("audit_trail_created")),
            },
        }

        # Service type breakdown - Fix cell variable issue by using a helper function
        service_types = lines.mapped("records_service_type")

        for service_type in service_types:
            if service_type:
                # Use a helper function to avoid cell variable issue
                def filter_by_service_type(line):
                    return line.records_service_type == service_type

                service_lines = lines.filtered(filter_by_service_type)
                summary["service_breakdown"][service_type] = {
                    "line_count": len(service_lines),
                    "revenue": sum(service_lines.mapped("price_total")),
                    "container_count": sum(service_lines.mapped("container_count")),
                }

        return summary

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set records management defaults"""
        for vals in vals_list:
            # Auto-detect records management services
            if vals.get("work_order_id") or vals.get("pickup_request_id") or vals.get("destruction_service_id"):
                vals["records_related"] = True

            # Set NAID audit requirement for compliance services
            if vals.get("records_service_type") in ["destruction", "retrieval"]:
                vals["naid_audit_required"] = True
            elif "naid_audit_required" not in vals:
                vals["naid_audit_required"] = False

        return super(AccountMoveLine, self).create(vals_list)

    def write(self, vals):
        """Override write to maintain audit trails"""
        result = super(AccountMoveLine, self).write(vals)

        # Create audit trail when certain fields change
        audit_trigger_fields = [
            "records_service_type",
            "container_count",
            "shredding_weight_lbs",
            "destruction_method",
            "naid_compliant",
        ]

        if any(field in vals for field in audit_trigger_fields):
            for line in self.filtered("records_related"):
                if line.naid_audit_required and not line.audit_trail_created:
                    line.action_create_audit_trail()

        return result

    # Computed display_name to replace deprecated name_get
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)

    @api.depends('name', 'records_related', 'records_service_type', 'container_count')
    def _compute_display_name(self):
        service_type_dict = dict(self._fields["records_service_type"].selection)
        for line in self:
            if line.records_related and line.records_service_type:
                service_type_label = service_type_dict.get(line.records_service_type, "")
                if line.container_count:
                    line.display_name = _("Service Line: %s (%s containers)") % (service_type_label, line.container_count)
                else:
                    line.display_name = _("Service Line: %s") % service_type_label
            else:
                line.display_name = line.name or _("Invoice Line")

    # ============================================================================
    # INTEGRATION METHODS
    # ============================================================================
    def sync_with_work_order(self):
        """Synchronize data with related work order"""
        self.ensure_one()

        if not self.work_order_id:
            return

        work_order = self.work_order_id

        # Update container information
        if hasattr(work_order, "container_ids"):
            self.container_ids = [(6, 0, work_order.container_ids.ids)]
            self.container_count = len(work_order.container_ids)

        # Update billing configuration
        if hasattr(work_order, "billing_config_id"):
            self.billing_config_id = work_order.billing_config_id

        # Update location information
        if hasattr(work_order, "pickup_location_id"):
            self.origin_location_id = work_order.pickup_location_id

        if hasattr(work_order, "delivery_location_id"):
            self.destination_location_id = work_order.delivery_location_id

    def generate_billing_report_data(self):
        """Generate data for billing reports."""
        self.ensure_one()
        return {
            "invoice_line_id": self.id,
            "invoice_number": self.move_id.name if self.move_id else "",
            "customer": self.partner_id.name if self.partner_id else "",
            "service_type": self.records_service_type,
            "service_date": self.pickup_date or self.move_id.invoice_date,
            "container_count": self.container_count,
            "weight_processed": self.shredding_weight_lbs,
        }
