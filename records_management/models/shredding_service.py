"""Odoo model for managing shredding services in the Records Management module.

This model represents a shredding service, which can be linked to document destruction
operations, certificates, and compliance workflows with NAID AAA compliance.
"""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class ShreddingService(models.Model):
    """Represents a shredding service for document destruction with NAID AAA compliance.

    This model manages shredding services including on-site and off-site destruction,
    certificate generation, and compliance tracking.
    """

    _name = 'shredding.service'
    _description = 'Shredding Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, id desc'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(
        string='Service Name',
        required=True,
        tracking=True,
        help="Name of the shredding service"
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help="Uncheck to archive this service"
    )

    service_type = fields.Selection(
        [
            ("onsite", "Mobile Shredding"),
            ("offsite", "Off-site Shredding"),
            ("bulk", "Bulk Destruction"),
            ("hard_drive", "Hard Drive Destruction"),
            ("electronic", "Electronic Media Destruction"),
        ],
        string="Service Type",
        required=True,
        tracking=True,
    )

    description = fields.Text(
        string='Description',
        help="Detailed description of the shredding service"
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        tracking=True,
        help=(
            "Customer for whom this shredding service is performed. Added to align with certificate"
            " and destruction report templates referencing service.partner_id.*"
        )
    )

    # Service Date
    service_date = fields.Date(
        string='Service Date',
        help="Date when the shredding service is scheduled or was performed"
    )

    # Compliance & Certification
    naid_compliant = fields.Boolean(
        string='NAID AAA Compliant',
        default=True,
        help="Whether this service meets NAID AAA compliance standards"
    )

    certificate_template_id = fields.Many2one(
        'ir.ui.view',
        string='Certificate Template',
        domain=[('type', '=', 'qweb')],
        help="Template used for generating destruction certificates"
    )

    # Pricing & Service Details
    base_price = fields.Float(
        string='Base Price',
        digits='Product Price',
        tracking=True,
        help="Base price for this shredding service"
    )

    price_per_container = fields.Float(
        string='Price per Container',
        digits='Product Price',
        help="Additional price per container"
    )

    price_per_lb = fields.Float(
        string='Price per Pound',
        digits='Product Price',
        help="Price per pound of shredded material"
    )

    # Service Provider Information
    def _default_provider_id(self):
        """Default to a sensible service provider.

        Preference order:
        1) Current company's partner if flagged as vendor (supplier_rank > 0)
        2) Any vendor partner (first match)
        3) base.main_partner if present and flagged as vendor

        Returns:
            int | False: res.partner ID or False if none found
        """
        company_partner = self.env.company.sudo().partner_id
        if company_partner and company_partner.supplier_rank and company_partner.supplier_rank > 0:
            return company_partner.id

        vendor = self.env['res.partner'].sudo().search([('supplier_rank', '>', 0)], limit=1)
        if vendor:
            return vendor.id

        main = self.env.ref('base.main_partner', raise_if_not_found=False)
        if main and main.supplier_rank and main.supplier_rank > 0:
            return main.id
        return False

    provider_id = fields.Many2one(
        'res.partner',
        string='Service Provider',
        domain=[('supplier_rank', '>', 0)],
        tracking=True,
        default=_default_provider_id,
        help=(
            "Partner providing this shredding service. By default, this field"
            " auto-fills with your company's partner if it is marked as a vendor"
            " (supplier_rank > 0); otherwise the first available vendor partner"
            " is selected."
        )
    )

    contact_person = fields.Char(
        string='Contact Person',
        help="Primary contact for this service"
    )

    contact_phone = fields.Char(
        string='Contact Phone',
        help="Phone number for service coordination"
    )

    contact_email = fields.Char(
        string='Contact Email',
        help="Email for service coordination"
    )

    # Operational Details
    lead_time_days = fields.Integer(
        string='Lead Time (Days)',
        default=1,
        help="Standard lead time for scheduling this service"
    )

    availability = fields.Selection([
        ('24_7', '24/7 Available'),
        ('business_hours', 'Business Hours Only'),
        ('scheduled', 'Scheduled Only'),
        ('emergency', 'Emergency Only')
    ], string='Availability', default='business_hours')

    # Geographic Coverage
    service_area = fields.Text(
        string='Service Area',
        help="Geographic areas covered by this service"
    )

    # Equipment & Capacity
    equipment_type = fields.Char(
        string='Equipment Type',
        help="Type of shredding equipment used"
    )

    max_capacity_per_day_lbs = fields.Float(
        string='Max Capacity per Day (lbs)',
        help="Maximum daily capacity in pounds"
    )

    # Security Features
    security_level = fields.Selection([
        ('1', 'Level 1 - Strip Cut'),
        ('2', 'Level 2 - Cross Cut'),
        ('3', 'Level 3 - Micro Cut'),
        ('4', 'Level 4 - Ultra Micro Cut'),
        ('5', 'Level 5 - High Security'),
        ('6', 'Level 6 - Top Secret')
    ], string='Security Level', help="DIN 66399 security level")

    chain_of_custody = fields.Boolean(
        string='Chain of Custody Tracking',
        default=True,
        help="Whether this service includes chain of custody tracking"
    )

    witness_destruction = fields.Boolean(
        string='Witness Destruction Available',
        default=False,
        help="Whether customer can witness the destruction process"
    )

    # Related Records
    destruction_request_ids = fields.One2many(
        'portal.request',
        'shredding_service_id',
        string='Destruction Requests',
        help="Destruction requests using this service"
    )

    certificate_ids = fields.One2many(
        'naid.certificate',
        'shredding_service_id',
        string='Certificates',
        help="Destruction certificates generated for this service"
    )

    # Report Convenience Field (referenced in QWeb template report_shredding_service)
    certificate_issued = fields.Boolean(
        string='Certificate Issued',
        compute='_compute_certificate_issued',
        store=True,
        help="Indicates whether at least one destruction certificate has been generated for this service (computed)."
    )

    # Computed Fields
    total_requests = fields.Integer(
        string='Total Requests',
        compute='_compute_totals',
        store=True,
        help="Total number of destruction requests"
    )

    total_destruction_items = fields.Integer(
        string='Total Destruction Items',
        compute='_compute_totals',
        store=True,
        help="Total number of items scheduled for destruction"
    )

    total_certificates = fields.Integer(
        string='Total Certificates',
        compute='_compute_totals',
        store=True,
        help="Total number of destruction certificates generated"
    )

    total_weight = fields.Float(
        string='Total Weight (kg)',
        compute='_compute_totals',
        store=True,
        help="Total weight of items scheduled for destruction"
    )

    last_used_date = fields.Datetime(
        string='Last Used',
        compute='_compute_last_used_date',
        store=True,
        help="Date this service was last used"
    )

    # Status and Notes
    notes = fields.Text(
        string='Internal Notes',
        help="Internal notes about this shredding service"
    )

    # Template Fields for Destruction Certificate Reports
    destruction_method = fields.Selection([
        ('shredding', 'Paper Shredding'),
        ('hard_drive', 'Hard Drive Destruction'),
        ('incineration', 'Incineration'),
        ('pulping', 'Pulping'),
        ('disintegration', 'Disintegration'),
        ('other', 'Other Method')
    ], string='Destruction Method', default='shredding', help="Method used for destruction")

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Equipment Used',
        help="Equipment/machine used for destruction"
    )

    particle_size = fields.Float(
        string='Particle Size (mm)',
        help="Particle size after destruction (in millimeters)"
    )

    technician_id = fields.Many2one(
        'res.users',
        string='Technician',
        help="Technician responsible for the destruction"
    )

    supervisor_id = fields.Many2one(
        'res.users',
        string='Supervisor',
        help="Supervisor overseeing the destruction"
    )

    witness_name = fields.Char(
        string='Witness Name',
        help="Name of the witness present during destruction"
    )

    technician_signature = fields.Binary(
        string='Technician Signature',
        help="Digital signature of the technician"
    )

    supervisor_signature = fields.Binary(
        string='Supervisor Signature',
        help="Digital signature of the supervisor"
    )

    customer_signature = fields.Binary(
        string='Customer Signature',
        help="Digital signature of the customer witness"
    )

    customer_representative = fields.Char(
        string='Customer Representative',
        help="Name of the customer representative who witnessed the destruction"
    )

    completion_time = fields.Datetime(
        string='Completion Time',
        help="Time when the destruction was completed"
    )

    # Computed Methods
    @api.depends('destruction_request_ids', 'certificate_ids')
    def _compute_totals(self):
        """Compute total counts for stat buttons."""
        for record in self:
            record.total_requests = len(record.destruction_request_ids)
            record.total_certificates = len(record.certificate_ids)

            # Count destruction items from related destruction orders
            destruction_orders = self.env['records.destruction'].search([
                ('request_id', 'in', record.destruction_request_ids.ids)
            ])
            record.total_destruction_items = len(destruction_orders.mapped('destruction_item_ids'))
            record.total_weight = sum(item.weight or 0.0 for item in destruction_orders.mapped('destruction_item_ids'))

    @api.depends('destruction_request_ids.create_date')
    def _compute_last_used_date(self):
        """Compute the last time this service was used."""
        for record in self:
            if record.destruction_request_ids:
                record.last_used_date = max(record.destruction_request_ids.mapped('create_date'))
            else:
                record.last_used_date = False

    @api.depends('certificate_ids')
    def _compute_certificate_issued(self):
        """Set certificate_issued True if any certificate exists.

        Kept very lightweight; stored to avoid recomputation in large list views
        and satisfy QWeb report field access (report_shredding_service).
        """
        for record in self:
            record.certificate_issued = bool(record.certificate_ids)

    # Validation
    @api.constrains('base_price', 'price_per_container', 'price_per_lb')
    def _check_prices(self):
        """Validate that at least one price is set."""
        for record in self:
            if not any([record.base_price, record.price_per_container, record.price_per_lb]):
                raise ValidationError(_("At least one pricing field must be set."))

    @api.constrains('lead_time_days')
    def _check_lead_time(self):
        """Validate lead time is positive."""
        for record in self:
            if record.lead_time_days < 0:
                raise ValidationError(_("Lead time must be positive."))

    @api.constrains('max_capacity_per_day_lbs')
    def _check_capacity(self):
        """Validate capacity is positive if set."""
        for record in self:
            if record.max_capacity_per_day_lbs and record.max_capacity_per_day_lbs <= 0:
                raise ValidationError(_("Capacity must be positive if specified."))

    # Business Methods
    def calculate_service_cost(self, container_count=0, weight_lbs=0):
        """Calculate total cost for this service.

        Args:
            container_count (int): Number of containers
            weight_lbs (float): Weight in pounds

        Returns:
            float: Total calculated cost
        """
        self.ensure_one()
        total_cost = self.base_price or 0.0
        total_cost += (container_count * (self.price_per_container or 0.0))
        total_cost += (weight_lbs * (self.price_per_lb or 0.0))
        return total_cost

    def schedule_service(self, requested_date):
        """Check if service can be scheduled on requested date.

        Args:
            requested_date (datetime): Requested service date

        Returns:
            dict: Result with availability and suggested dates
        """
        self.ensure_one()
        # This would integrate with scheduling logic
        return {
            'available': True,
            'suggested_date': requested_date,
            'lead_time_met': True
        }

    def generate_certificate(self, destruction_data):
        """Generate destruction certificate for completed service.

        Args:
            destruction_data (dict): Data about the destruction process

        Returns:
            recordset: Created certificate record
        """
        self.ensure_one()
        if not self.certificate_template_id:
            raise ValidationError(_("No certificate template configured for this service."))

        # Validate required data
        partner_id = destruction_data.get('partner_id')
        if not partner_id:
            raise ValidationError(_("Customer (partner_id) is required to generate a certificate."))

        # Map provided data into NAID certificate fields
        certificate_vals = {
            'partner_id': partner_id,
            'destruction_date': destruction_data.get('service_date') or fields.Datetime.now(),
            'shredding_service_id': self.id,
        }

        return self.env['naid.certificate'].create(certificate_vals)

    # Action Methods
    def action_view_requests(self):
        """Action to view related destruction requests."""
        action = self.env.ref('records_management.action_portal_request').read()[0]
        action['domain'] = [('shredding_service_id', '=', self.id)]
        action['context'] = {'default_shredding_service_id': self.id}
        return action

    def action_view_certificates(self):
        """Action to view related certificates."""
        action = self.env.ref('records_management.action_naid_certificate').read()[0]
        action['domain'] = [('shredding_service_id', '=', self.id)]
        action['context'] = {'default_shredding_service_id': self.id}
        return action

    # Placeholder button from XML (safe stub)
    def action_view_destruction_items(self):
        """View all destruction items related to this shredding service.
        
        This includes container inventory and other items scheduled for
        destruction using this shredding service.
        """
        self.ensure_one()

        # Get all destruction requests using this service
        destruction_requests = self.destruction_request_ids

        # Get related destruction orders from those requests
        destruction_orders = self.env['records.destruction'].search([
            ('request_id', 'in', destruction_requests.ids)
        ])

        # Get all destruction items from those orders
        destruction_items = destruction_orders.mapped('destruction_item_ids')

        return {
            'name': _('Destruction Items - %s') % self.name,
            'view_mode': 'list,form',
            'res_model': 'destruction.item',
            'domain': [('id', 'in', destruction_items.ids)],
            'type': 'ir.actions.act_window',
            'context': {
                'default_destruction_id': destruction_orders.ids[0] if destruction_orders else False,
                'search_default_group_by_destruction': 1,
            },
            'help': "<p class='o_view_nocontent_smiling_face'>No destruction items found</p>"
                    "<p>Items (including container inventory) scheduled for destruction using this service will appear here.</p>"
        }

    # Override Methods
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add logging."""
        records = super().create(vals_list)
        for record in records:
            _logger.info("Created shredding service: %s", record.name)
        return records

    def write(self, vals):
        """Override write to add logging."""
        result = super().write(vals)
        if 'active' in vals and not vals['active']:
            _logger.info("Archived shredding service: %s", self.name)
        return result

    def unlink(self):
        """Override unlink to prevent deletion of used services."""
        for record in self:
            if record.destruction_request_ids:
                raise ValidationError(_(
                    "Cannot delete shredding service '%s' as it has related destruction requests."
                ) % record.name)
        return super().unlink()
