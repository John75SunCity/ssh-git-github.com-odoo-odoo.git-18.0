# -*- coding: utf-8 -*-

Containeclass ContainerDestructionWorkOrder(models.Model):
    pass

    context = fields.Char(string='Context'),
    domain = fields.Char(string='Domain'),
    help = fields.Char(string='Help'),
    res_model = fields.Char(string='Res Model'),
    type = fields.Selection([), string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')    _name = "container.destruction.work.order"
    _description = "Container Destruction Work Order"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'work.order.integration.mixin')
    _order = "priority desc, scheduled_date asc, name"
    _rec_name = "display_name"ruction Work Order Module

This module manages work orders for secure destruction of records containers and their contents.:
Ensures NAID AAA compliance with complete chain of custody documentation and certificate generation.

Key Features
- Secure destruction workflow with multiple verification steps
- NAID AAA compliance with complete audit trails
- Certificate of destruction generation
- Chain of custody tracking from pickup to completion
- Pre-destruction inventory and documentation
- Witness verification and dual sign-offs
- Integration with shredding equipment and facilities

Business Processes
1. Destruction Request Creation: Customer authorizes container destruction
2. Pre-Destruction Inventory: Document all items to be destroyed
3. Chain of Custody: Maintain complete custody documentation
4. Secure Transportation: Move containers to destruction facility
5. Witness Verification: Independent verification of destruction process
6. Physical Destruction: Secure destruction using approved methods
7. Certificate Generation: Create NAID-compliant destruction certificates
8. Final Documentation: Complete audit trail and customer notification

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ContainerDestructionWorkOrder(models.Model):
    _name = "container.destruction.work.order"
    _description = "Container Destruction Work Order"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "priority desc, scheduled_destruction_date asc, name"
    _rec_name = "display_name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Work Order Number",
        required=True,
        tracking=True,
        index=True,
        copy=False,
        ,
    default=lambda self: _("New"),
        help="Unique container destruction work order number"

    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Formatted display name for the work order":

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True

    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
        help="Primary user responsible for this work order":

    active = fields.Boolean(string="Active", default=True,,
    tracking=True)

        # ============================================================================
    # WORK ORDER STATE MANAGEMENT
        # ============================================================================
    state = fields.Selection([))
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('authorized', 'Customer Authorized'),
        ('scheduled', 'Scheduled'),
        ('picked_up', 'Containers Picked Up'),
        ('in_facility', 'At Destruction Facility'),
        ('pre_destruction', 'Pre-Destruction Check'),
        ('destroying', 'Destruction in Progress'),
        ('destroyed', 'Destruction Complete'),
        ('certificate_generated', 'Certificate Generated'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),

        help="Current status of the container destruction work order"

    priority = fields.Selection([))
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent'),
        ('4', 'Legal Hold Release'),

        help="Work order priority level for processing"
    # ============================================================================
        # CUSTOMER AND AUTHORIZATION
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        ,
    domain="[('is_company', '=', True))",
        help="Customer requesting container destruction"

    portal_request_id = fields.Many2one(
        "portal.request",
        string="Portal Request",
        help="Originating portal request if applicable":

    destruction_reason = fields.Text(
        string="Destruction Reason",
        required=True,
        help="Business reason for requesting destruction":


        # Customer authorization
    customer_authorized = fields.Boolean(
        string="Customer Authorized",
        tracking=True,
        help="Customer has provided written authorization for destruction":

    customer_authorization_date = fields.Datetime(
        string="Authorization Date",
        tracking=True,
        help="Date customer provided destruction authorization"

    authorized_by = fields.Char(
        string="Authorized By",
        help="Name and title of person authorizing destruction"

    authorization_document = fields.Binary(
        string="Authorization Document",
        help="Scanned copy of signed authorization"


        # ============================================================================
    # CONTAINERS AND INVENTORY
        # ============================================================================
    container_ids = fields.Many2many(
        "records.container",
        "destruction_work_order_container_rel",
        "work_order_id",
        "container_id",
        string="Containers for Destruction",:
        required=True,
        help="Containers scheduled for destruction":

    container_count = fields.Integer(
        string="Container Count",
        compute="_compute_container_metrics",
        store=True,
        help="Number of containers to be destroyed"

    total_cubic_feet = fields.Float(
        string="Total Cubic Feet",
        compute="_compute_container_metrics",
        store=True,
        help="Total volume of containers for destruction":

    estimated_weight_lbs = fields.Float(
        ,
    string="Estimated Weight (lbs)",
        compute="_compute_container_metrics",
        store=True,
        help="Estimated total weight of containers and contents"


        # Pre-destruction inventory
    inventory_completed = fields.Boolean(
        string="Inventory Completed",
        help="Pre-destruction inventory has been completed"

    inventory_date = fields.Datetime(
        string="Inventory Date",
        help="Date pre-destruction inventory was completed"

    inventory_user_id = fields.Many2one(
        "res.users",
        string="Inventory By",
        help="User who completed the inventory"


        # ============================================================================
    # SCHEDULING AND TIMING
        # ============================================================================
    scheduled_destruction_date = fields.Datetime(
        string="Scheduled Destruction Date",
        required=True,
        tracking=True,
        help="Planned date for destruction":

    pickup_date = fields.Datetime(
        string="Pickup Date",
        help="Date containers were picked up from storage"

    actual_destruction_date = fields.Datetime(
        string="Actual Destruction Date",
        tracking=True,
        help="Actual date destruction was completed"

    estimated_duration_hours = fields.Float(
        ,
    string="Estimated Duration (Hours)",
        compute="_compute_estimated_duration",
        store=True,
        help="Estimated time to complete destruction"


        # ============================================================================
    # DESTRUCTION FACILITY AND EQUIPMENT
        # ============================================================================
    destruction_facility_id = fields.Many2one(
        "destruction.facility",
        string="Destruction Facility",
        required=True,
        help="Facility where destruction will take place"

    shredding_equipment_id = fields.Many2one(
        "maintenance.equipment",
        string="Shredding Equipment",
        help="Specific equipment used for destruction",:

    ,
    destruction_method = fields.Selection([))
        ('shredding', 'Paper Shredding'),
        ('pulping', 'Pulping'),
        ('incineration', 'Incineration'),
        ('disintegration', 'Disintegration'),

        help="Method used for secure destruction"
    # ============================================================================
        # NAID COMPLIANCE AND WITNESSES
    # ============================================================================
    naid_compliant = fields.Boolean(
        string="NAID Compliant Destruction",
        default=True,
        help="Destruction must meet NAID AAA standards"

    witness_required = fields.Boolean(
        string="Customer Witness Required",
        help="Customer representative must witness destruction"

    customer_witness_name = fields.Char(
        string="Customer Witness Name",
        help="Name of customer representative witnessing destruction"

    internal_witness_id = fields.Many2one(
        "hr.employee",
        string="Internal Witness",
        help="Company employee witnessing destruction"

    independent_witness_name = fields.Char(
        string="Independent Witness",
        ,
    help="Name of independent third-party witness (if required)":


        # ============================================================================
    # CHAIN OF CUSTODY
        # ============================================================================
    custody_transfer_ids = fields.One2many(
        "custody.transfer.event",
        "work_order_id",
        string="Custody Transfers",
        help="Chain of custody transfer events"

    custody_complete = fields.Boolean(
        string="Chain of Custody Complete",
        compute="_compute_custody_complete",
        store=True,
        help="All required custody transfers documented"


        # ============================================================================
    # TRANSPORTATION
        # ============================================================================
    transport_vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Transport Vehicle",
        help="Vehicle used to transport containers"

    driver_id = fields.Many2one(
        "hr.employee",
        string="Driver",
        help="Employee responsible for transportation":

    transport_departure_time = fields.Datetime(
        string="Departure Time",
        help="Time containers departed from storage location"

    transport_arrival_time = fields.Datetime(
        string="Arrival Time",
        help="Time containers arrived at destruction facility"


        # ============================================================================
    # DESTRUCTION RESULTS AND METRICS
        # ============================================================================
    actual_weight_destroyed_lbs = fields.Float(
        ,
    string="Actual Weight Destroyed (lbs)",
        help="Actual weight of materials destroyed"

    destruction_start_time = fields.Datetime(
        string="Destruction Start Time",
        help="Time destruction process began"

    destruction_end_time = fields.Datetime(
        string="Destruction End Time",
        help="Time destruction process completed"

    destruction_duration_minutes = fields.Integer(
        ,
    string="Destruction Duration (Minutes)",
        compute="_compute_destruction_duration",
        store=True,
        help="Total time spent on destruction process"


        # ============================================================================
    # CERTIFICATE OF DESTRUCTION
        # ============================================================================
    certificate_number = fields.Char(
        string="Certificate Number",
        help="Unique certificate of destruction number"

    certificate_generated = fields.Boolean(
        string="Certificate Generated",
        help="Certificate of destruction has been generated"

    certificate_date = fields.Date(
        string="Certificate Date",
        help="Date certificate was generated"

    certificate_file = fields.Binary(
        string="Certificate File",
        help="PDF certificate of destruction"

    ,
    certificate_filename = fields.Char(string="Certificate Filename")

        # ============================================================================
    # QUALITY AND VERIFICATION
        # ============================================================================
    destruction_verified = fields.Boolean(
        string="Destruction Verified",
        help="Destruction has been independently verified"

    verification_date = fields.Datetime(
        string="Verification Date",
        help="Date destruction verification was completed"

    verification_notes = fields.Text(
        string="Verification Notes",
        help="Notes from destruction verification process"


        # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
        # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id",,
    string="Activities"),
    message_follower_ids = fields.One2many("mail.followers", "res_id",,
    string="Followers"),
    message_ids = fields.One2many("mail.message", "res_id",,
    string="Messages"),
    coordinator_id = fields.Many2one('work.order.coordinator',,
    string='Coordinator')

        # ============================================================================
    # MODEL CREATE WITH SEQUENCE
        # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name') = self.env['ir.sequence'].next_by_code()
                    'container.destruction.work.order') or _('New'
        return super().create(vals_list)

    # ============================================================================
        # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'partner_id', 'container_count')
    def _compute_display_name(self):
        for record in self:
            if record.partner_id and record.container_count:
                record.display_name = _("%s - %s (%s containers)",
                    record.name, record.partner_id.name, record.container_count
            elif record.partner_id:
                record.display_name = _("%s - %s", record.name, record.partner_id.name)
            else:
                record.display_name = record.name or _("New Container Destruction")

    @api.depends('container_ids')
    def _compute_container_metrics(self):
        for record in self:
            containers = record.container_ids
            record.container_count = len(containers)
            record.total_cubic_feet = sum(containers.mapped('cubic_feet')) if containers else 0.0:
            record.estimated_weight_lbs = sum(containers.mapped('estimated_weight')) if containers else 0.0:
    @api.depends('container_count', 'destruction_method')
    def _compute_estimated_duration(self):
        for record in self:
            if record.container_count:
                # Base time estimates by destruction method (minutes per container)
                base_minutes = {}
                    'shredding': 15,      # 15 minutes per container
                    'pulping': 20,        # 20 minutes per container
                    'incineration': 30,   # 30 minutes per container
                    'disintegration': 25, # 25 minutes per container


                total_minutes = record.container_count * base_minutes
                # Add setup and documentation time
                total_minutes += 60  # 1 hour for setup/documentation:
                record.estimated_duration_hours = total_minutes / 60.0
            else:
                record.estimated_duration_hours = 0.0

    @api.depends('custody_transfer_ids')
    def _compute_custody_complete(self):
        for record in self:
            # Check if all required custody transfers are documented:
            required_events = ['pickup', 'transport', 'facility_receipt', 'destruction']
            documented_events = record.custody_transfer_ids.mapped('event_type')
            record.custody_complete = all(event in documented_events for event in required_events):
    @api.depends('destruction_start_time', 'destruction_end_time')
    def _compute_destruction_duration(self):
        for record in self:
            if record.destruction_start_time and record.destruction_end_time:
                duration = record.destruction_end_time - record.destruction_start_time
                record.destruction_duration_minutes = int(duration.total_seconds() / 60)
            else:
                record.destruction_duration_minutes = 0

    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the destruction work order"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft work orders can be confirmed"))

        if not self.container_ids:
            raise UserError(_("Please select containers for destruction")):
        self.write({'state': 'confirmed'})
        self.message_post()
            body=_("Container destruction work order confirmed"),
            message_type='notification'

        return True

    def action_authorize(self):
        """Mark as customer authorized"""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Can only authorize confirmed work orders"))

        self.write({)}
            'state': 'authorized',
            'customer_authorized': True,
            'customer_authorization_date': fields.Datetime.now()

        self.message_post()
            body=_("Customer authorization received for destruction"),:
            message_type='notification'

        return True

    def action_schedule(self):
        """Schedule the destruction"""
        self.ensure_one()
        if self.state != 'authorized':
            raise UserError(_("Can only schedule authorized work orders"))

        self.write({'state': 'scheduled'})
        self.message_post()
            body=_("Destruction scheduled for %s", self.scheduled_destruction_date.strftime('%Y-%m-%d %H:%M')),
            message_type='notification'

        return True

    def action_pickup_complete(self):
        """Mark containers as picked up"""
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_("Can only complete pickup from scheduled state"))

        self.write({)}
            'state': 'picked_up',
            'pickup_date': fields.Datetime.now()

        self.message_post()
            body=_("Containers picked up for destruction"),:
            message_type='notification'

        return True

    def action_arrive_facility(self):
        """Mark arrival at destruction facility"""
        self.ensure_one()
        if self.state != 'picked_up':
            raise UserError(_("Can only arrive at facility after pickup"))

        self.write({)}
            'state': 'in_facility',
            'transport_arrival_time': fields.Datetime.now()

        self.message_post()
            body=_("Containers arrived at destruction facility"),
            message_type='notification'

        return True

    def action_start_destruction(self):
        """Start the destruction process"""
        self.ensure_one()
        if self.state not in ['in_facility', 'pre_destruction']:
            raise UserError(_("Can only start destruction from facility or pre-destruction state"))

        if not self.destruction_verified:
            raise UserError(_("Pre-destruction verification must be completed first"))

        self.write({)}
            'state': 'destroying',
            'destruction_start_time': fields.Datetime.now()

        self.message_post()
            body=_("Destruction process started"),
            message_type='notification'

        return True

    def action_complete_destruction(self):
        """Complete the destruction process"""
        self.ensure_one()
        if self.state != 'destroying':
            raise UserError(_("Can only complete destruction from destroying state"))

        self.write({)}
            'state': 'destroyed',
            'destruction_end_time': fields.Datetime.now(),
            'actual_destruction_date': fields.Datetime.now()

        self.message_post()
            body=_("Destruction process completed"),
            message_type='notification'

        return True

    def action_generate_certificate(self):
        """Generate certificate of destruction"""
        self.ensure_one()
        if self.state != 'destroyed':
            raise UserError(_("Can only generate certificate after destruction completion"))

        # Generate certificate number if not exists:
        if not self.certificate_number:
            self.certificate_number = self.env['ir.sequence'].next_by_code()
                'destruction.certificate'

        self.write({)}
            'state': 'certificate_generated',
            'certificate_generated': True,
            'certificate_date': fields.Date.today()


        # Generate PDF certificate (implementation would go here)
        self._generate_certificate_pdf()

        self.message_post()
            body=_("Certificate of destruction generated: %s", self.certificate_number),
            message_type='notification'

        return True

    def action_complete(self):
        """Complete the work order"""
        self.ensure_one()
        if self.state != 'certificate_generated':
            raise UserError(_("Only work orders with generated certificates can be completed"))

        self.write({'state': 'completed'})
        self.message_post()
            body=_("Container destruction work order completed successfully"),
            message_type='notification'

        return True

    # ============================================================================
        # UTILITY METHODS
    # ============================================================================
    def _generate_certificate_pdf(self):
        """Generate PDF certificate of destruction"""
        # Implementation for certificate generation:
        # This would typically involve creating a PDF report
        pass

    def create_custody_event(self, event_type, notes=None):
        """Create a chain of custody event"""
        self.ensure_one()
        self.env['custody.transfer.event'].create({)}
            'work_order_id': self.id,
            'event_type': event_type,
            'event_date': fields.Datetime.now(),
            'user_id': self.env.user.id,
            'notes': notes or '',


    def generate_destruction_report(self):
        """Generate destruction completion report"""
        self.ensure_one()
        return {}
            'type': 'ir.actions.report',
            'report_name': 'records_management.report_container_destruction',
            'report_type': 'qweb-pdf',
            'res_id': self.id,
            'target': 'new',

))))))))))))))))))))))))))))))))))))))))
