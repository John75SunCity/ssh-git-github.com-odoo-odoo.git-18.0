# -*- coding: utf-8 -*-

Customer Inventory Report Line Model

Individual line items for customer inventory reports with comprehensive:
    pass
tracking, financial integration, and container specification management
for Records Management system operations.""":"
Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CustomerInventoryReportLine(models.Model):

        Customer Inventory Report Line Management

    Manages individual line items within customer inventory reports,
        providing detailed container tracking, document counting, and
    storage cost calculations with full audit trail support.


    _name = "customer.inventory.report.line"
    _description = "Customer Inventory Report Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "report_id, container_id, document_type"
    _rec_name = "name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Line Description",
        required=True,
        tracking=True,
        index=True,
        help="Description of this inventory line item"


    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
        store=True,
        help="Formatted display name for the line":


    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True


    user_id = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        tracking=True,
        help="User who created this line item"


    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this line"


    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order sequence for line display":


        # ============================================================================
    # RELATIONSHIP FIELDS
        # ============================================================================
    report_id = fields.Many2one(
        "customer.inventory.report",
        string="Inventory Report",
        required=True,
        ondelete="cascade",
        index=True,
        help="Parent inventory report"


    container_id = fields.Many2one(
        "records.container",
        string="Container",
        required=True,
        index=True,
        help="Container being reported on"


    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="report_id.partner_id",
        readonly=True,
        store=True,
        help="Customer for this inventory line":


    location_id = fields.Many2one(
        "records.location",
        string="Storage Location",
        related="container_id.location_id",
        readonly=True,
        store=True,
        help="Current storage location"


        # ============================================================================
    # CONTAINER SPECIFICATIONS
        # ============================================================================
    container_type = fields.Selection(
        related="container_id.container_type_id.standard_type",
        readonly=True,
        store=True,
        string="Container Type",
        ,
    help="Type of container (TYPE_01, TYPE_02, etc.)"


    container_barcode = fields.Char(
        string="Container Barcode",
        related="container_id.barcode",
        readonly=True,
        store=True,
        help="Container barcode identifier"


    container_volume_cf = fields.Float(
        ,
    string="Container Volume (CF)",
        related="container_id.cubic_feet",
        readonly=True,
        store=True,
        digits=(8, 3),
        help="Container volume in cubic feet"


    container_weight_lbs = fields.Float(
        ,
    string="Container Weight (lbs)",
        related="container_id.weight",
        readonly=True,
        store=True,
        digits=(8, 2),
        help="Container weight in pounds"


        # ============================================================================
    # DOCUMENT TRACKING
        # ============================================================================
    document_type = fields.Char(
        string="Document Type",
        help="Type of documents in container"


    document_type_id = fields.Many2one(
        "records.document.type",
        string="Document Type Record",
        help="Linked document type record"


    document_count = fields.Integer(
        string="Document Count",
        default=0,
        help="Number of documents in container"


    document_count_verified = fields.Boolean(
        string="Count Verified",
        default=False,
        tracking=True,
        help="Whether document count has been verified"


    verification_date = fields.Date(
        string="Verification Date",
        help="Date when document count was verified"


    verified_by = fields.Many2one(
        "res.users",
        string="Verified By",
        help="User who verified the count"


        # ============================================================================
    # DATE TRACKING
        # ============================================================================
    storage_date = fields.Date(
        string="Storage Date",
        help="Date documents were initially stored"


    last_access_date = fields.Date(
        string="Last Access Date",
        help="Date container was last accessed"


    retention_date = fields.Date(
        string="Retention Date",
        help="Date when documents become eligible for destruction":


    report_date = fields.Date(
        string="Report Date",
        related="report_id.report_date",
        readonly=True,
        store=True,
        help="Date this report was generated"


        # ============================================================================
    # LOCATION AND ACCESS
        # ============================================================================
    location_code = fields.Char(
        string="Location Code",
        related="location_id.code",
        readonly=True,
        store=True,
        help="Storage location identifier"


    bin_location = fields.Char(
        string="Bin Location",
        help="Specific bin or shelf location"


    ,
    access_level = fields.Selection([))
        ('public', 'Public Access'),
        ('restricted', 'Restricted Access'),
        ('confidential', 'Confidential'),
        ('secure', 'Secure Vault')


        # ============================================================================
    # FINANCIAL TRACKING
        # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True


    monthly_storage_cost = fields.Monetary(
        string="Monthly Storage Cost",
        currency_field="currency_id",
        help="Monthly storage cost for this container":


    total_storage_cost = fields.Monetary(
        string="Total Storage Cost",
        currency_field="currency_id",
        compute='_compute_total_storage_cost',
        store=True,
        help="Total storage cost to date"


    storage_months = fields.Integer(
        string="Storage Months",
        compute='_compute_storage_months',
        store=True,
        help="Number of months in storage"


        # ============================================================================
    # STATUS AND WORKFLOW
        # ============================================================================
    ,
    line_status = fields.Selection([))
        ('active', 'Active Storage'),
        ('pending_pickup', 'Pending Pickup'),
        ('retrieved', 'Retrieved'),
        ('destroyed', 'Destroyed'),
        ('transferred', 'Transferred')


    billing_status = fields.Selection([))
        ('unbilled', 'Unbilled'),
        ('billed', 'Billed'),
        ('paid', 'Paid'),
        ('disputed', 'Disputed')


        # ============================================================================
    # NOTES AND DESCRIPTIONS
        # ============================================================================
    description = fields.Text(
        string="Description",
        help="Detailed description of container contents"


    notes = fields.Text(
        string="Notes",
        help="Additional notes or observations"


    special_instructions = fields.Text(
        string="Special Instructions",
        help="Special handling or access instructions"


        # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
        # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        ,
    domain=lambda self: [("res_model", "=", self._name))


    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        ,
    domain=lambda self: [("res_model", "=", self._name))


    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        ,
    domain=lambda self: [("model", "=", self._name))


        # ============================================================================
    # COMPUTE METHODS
        # ============================================================================
    @api.depends('name', 'container_id', 'document_count')
    def _compute_display_name(self):
        """Compute display name with container and document info"""
        for line in self:
            parts = []
            if line.container_id:
                parts.append(line.container_id.name or line.container_id.barcode)
            if line.document_count:
                parts.append(_("(%d docs)", line.document_count))
            if line.document_type:
                parts.append(line.document_type)

            if parts:
                line.display_name = " - ".join(parts)
            else:
                line.display_name = line.name or _("New Line")

    @api.depends('storage_date', 'report_date')
    def _compute_storage_months(self):
        """Calculate number of months in storage"""
        for line in self:
            if line.storage_date and line.report_date:
                # Calculate months between dates
                years = line.report_date.year - line.storage_date.year
                months = line.report_date.month - line.storage_date.month
                total_months = years * 12 + months
                line.storage_months = max(total_months, 0)
            else:
                line.storage_months = 0

    @api.depends('monthly_storage_cost', 'storage_months')
    def _compute_total_storage_cost(self):
        """Calculate total storage cost based on months stored"""
        for line in self:
            if line.monthly_storage_cost and line.storage_months:
                line.total_storage_cost = line.monthly_storage_cost * line.storage_months
            else:
                line.total_storage_cost = 0.0

    # ============================================================================
        # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('container_id')
    def _onchange_container_id(self):
        """Update fields when container changes"""
        if self.container_id:
            # Auto-populate container-related fields
            if not self.name:
                self.name = _("Inventory Line: %s", self.container_id.name or self.container_id.barcode)

            if not self.storage_date and self.container_id.create_date:
                self.storage_date = self.container_id.create_date.date()

            # Get document information from container
            if self.container_id.document_ids:
                self.document_count = len(self.container_id.document_ids)
                # Set document type from first document if available:
                first_doc = self.container_id.document_ids[0]
                if first_doc.document_type_id:
                    self.document_type_id = first_doc.document_type_id
                    self.document_type = first_doc.document_type_id.name

    @api.onchange('document_type_id')
    def _onchange_document_type_id(self):
        """Update document type field when type record changes"""
        if self.document_type_id:
            self.document_type = self.document_type_id.name

    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_verify_document_count(self):
        """Mark document count as verified"""
        self.ensure_one()
        self.write({)}
            'document_count_verified': True,
            'verification_date': fields.Date.today(),
            'verified_by': self.env.user.id

        self.message_post(body=_("Document count verified: %d documents", self.document_count))

    def action_update_from_container(self):
        """Update line data from current container state"""
        self.ensure_one()
        if not self.container_id:
            raise UserError(_("No container linked to update from"))

        # Update document count
        actual_count = len(self.container_id.document_ids)
        if actual_count != self.document_count:
            old_count = self.document_count
            self.document_count = actual_count
            self.document_count_verified = False
            self.message_post(body=_())
                "Document count updated from %d to %d (requires verification)",
                old_count, actual_count


    def action_view_container(self):
        """View the related container"""
        self.ensure_one()
        if not self.container_id:
            raise UserError(_("No container linked to view"))

        return {}
            'type': 'ir.actions.act_window',
            'name': _('Container Details'),
            'res_model': 'records.container',
            'res_id': self.container_id.id,
            'view_mode': 'form',
            'target': 'current',


    def action_view_documents(self):
        """View documents in the container"""
        self.ensure_one()
        if not self.container_id:
            raise UserError(_("No container linked"))

        return {}
            'type': 'ir.actions.act_window',
            'name': _('Container Documents'),
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('container_id', '=', self.container_id.id)],
            'context': {'default_container_id': self.container_id.id},


    # ============================================================================
        # VALIDATION METHODS
    # ============================================================================
    @api.constrains('document_count')
    def _check_document_count(self):
        """Validate document count is non-negative"""
        for line in self:
            if line.document_count < 0:
                raise ValidationError(_("Document count cannot be negative"))

    @api.constrains('monthly_storage_cost')
    def _check_monthly_cost(self):
        """Validate monthly cost is non-negative"""
        for line in self:
            if line.monthly_storage_cost < 0:
                raise ValidationError(_("Monthly storage cost cannot be negative"))

    @api.constrains('storage_date', 'report_date')
    def _check_date_sequence(self):
        """Validate storage date is before report date"""
        for line in self:
            if line.storage_date and line.report_date:
                if line.storage_date > line.report_date:
                    raise ValidationError(_())
                        "Storage date cannot be after report date"


    # ============================================================================
        # BUSINESS LOGIC METHODS
    # ============================================================================
    def get_container_utilization_data(self):
        """Get container utilization statistics"""
        self.ensure_one()

        if not self.container_id:
            return {}

        # Get container specifications based on type
        container_specs = {}
            'type_01': {'volume': 1.2, 'max_weight': 35},
            'type_02': {'volume': 2.4, 'max_weight': 65},
            'type_03': {'volume': 0.875, 'max_weight': 35},
            'type_04': {'volume': 5.0, 'max_weight': 75},
            'type_06': {'volume': 0.42, 'max_weight': 40},


        container_type = self.container_type or 'type_01'
        spec = container_specs.get(container_type, container_specs['type_01'])

        volume_utilization = 0
        weight_utilization = 0

        if spec['volume'] > 0:
            volume_utilization = (self.container_volume_cf / spec['volume']) * 100

        if spec['max_weight'] > 0:
            weight_utilization = (self.container_weight_lbs / spec['max_weight']) * 100

        return {}
            'volume_utilization': min(volume_utilization, 100),
            'weight_utilization': min(weight_utilization, 100),
            'container_spec': spec,
            'is_overutilized': volume_utilization > 100 or weight_utilization > 100


    @api.model
    def get_summary_by_document_type(self, domain=None):
        """Get summary statistics by document type"""
        if domain is None:
            domain = []

        lines = self.search(domain)
        summary = {}

        for line in lines:
            doc_type = line.document_type or _('Unspecified')
            if doc_type not in summary:
                summary[doc_type] = {}
                    'line_count': 0,
                    'container_count': 0,
                    'document_count': 0,
                    'total_cost': 0.0,
                    'container_ids': set()


            summary[doc_type]['line_count'] += 1
            summary[doc_type]['document_count'] += line.document_count
            summary[doc_type]['total_cost'] += line.total_storage_cost
            summary[doc_type]['container_ids'].add(line.container_id.id)

        # Convert container sets to counts
        for doc_type in summary:
            summary[doc_type]['container_count'] = len(summary[doc_type]['container_ids'])
            del summary[doc_type]['container_ids']  # Remove set for JSON serialization:
        return summary

    # ============================================================================
        # REPORTING METHODS
    # ============================================================================
    def generate_line_summary(self):
        """Generate summary information for this line""":
        self.ensure_one()

        utilization_data = self.get_container_utilization_data()

        return {}
            'line_name': self.display_name,
            'container_barcode': self.container_barcode,
            'document_count': self.document_count,
            'document_type': self.document_type,
            'storage_months': self.storage_months,
            'monthly_cost': self.monthly_storage_cost,
            'total_cost': self.total_storage_cost,
            'location_code': self.location_code,
            'access_level': self.access_level,
            'verification_status': 'Verified' if self.document_count_verified else 'Unverified',:
            'utilization': utilization_data,
            'special_notes': bool(self.special_instructions or self.notes)


    # ============================================================================
        # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default name"""
        for vals in vals_list:
            if not vals.get('name'):
                sequence = self.env['ir.sequence'].next_by_code('customer.inventory.report.line')
                vals['name'] = sequence or _('New Line')

        return super().create(vals_list)

    def write(self, vals):
        """Override write for tracking important changes""":
        result = super().write(vals)

        if 'document_count' in vals:
            for line in self:
                if not line.document_count_verified:
                    line.message_post(body=_())
                        "Document count changed to %d (verification required)",
                        line.document_count


        return result

    def name_get(self):
        """Custom name display"""
        result = []
        for line in self:
            name = line.display_name or line.name
            if line.container_id:
                container_info = line.container_id.name or line.container_barcode
                name = _("%s (%s)", name, container_info)
            result.append((line.id, name))
        return result

    # ============================================================================
        # UTILITY METHODS
    # ============================================================================
    def _get_cost_center_allocation(self):
        """Get cost center allocation for financial reporting""":
        self.ensure_one()

        # Allocate costs based on document type and access level
        base_allocation = {}
            'storage_operations': 0.6,  # Base storage cost
            'security_compliance': 0.2,  # Security and compliance
            'customer_service': 0.1,    # Customer service overhead
            'facility_maintenance': 0.1  # Facility costs


        # Adjust allocation based on access level
        if self.access_level in ['confidential', 'secure']:
            base_allocation['security_compliance'] += 0.1
            base_allocation['storage_operations'] -= 0.1

        return base_allocation


    """"))))))))))))))))))))))))))))))
