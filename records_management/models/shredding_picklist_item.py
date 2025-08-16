# -*- coding: utf-8 -*-

Shredding Picklist Item Model

Individual items on shredding picklists for destruction tracking.:
    pass
Manages container-level tracking within shredding operations with
comprehensive audit trails and NAID AAA compliance integration.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ShreddingPicklistItem(models.Model):

        Shredding Picklist Item Management

    Manages individual container items within shredding picklists,
        providing detailed tracking from collection through certified
    destruction with complete NAID compliance audit trails.


    _name = "shredding.picklist.item"
    _description = "Shredding Picklist Item"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "picklist_id, sequence, container_id"
    _rec_name = "display_name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Item Description",
        required=True,
        tracking=True,
        index=True,
        help="Description of the shredding item"
    

    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
        store=True,
        help="Formatted display name for the item":
    

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
        help="User who created this item"
    

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this item"
    

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order sequence for item display":
    

        # ============================================================================
    # RELATIONSHIP FIELDS
        # ============================================================================
    picklist_id = fields.Many2one(
        "shredding.picklist",
        string="Picklist",
        required=True,
        ondelete="cascade",
        index=True,
        help="Parent shredding picklist"
    

    batch_id = fields.Many2one(
        "shredding.inventory.batch",
        string="Inventory Batch",
        help="Batch this item belongs to"
    

    container_id = fields.Many2one(
        "records.container",
        string="Container",
        required=True,
        index=True,
        help="Container to be shredded"
    

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="container_id.partner_id",
        readonly=True,
        store=True,
        help="Container owner"
    

    location_id = fields.Many2one(
        "records.location",
        string="Storage Location",
        related="container_id.location_id",
        readonly=True,
        store=True,
        help="Current container location"
    

        # ============================================================================
    # CONTAINER SPECIFICATIONS
        # ============================================================================
    container_type = fields.Selection(
        related="container_id.container_type_id.standard_type",
        readonly=True,
        store=True,
        string="Container Type",
        help="Type of container being shredded"
    

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
    

        # ============================================================================
    # ITEM DETAILS
        # ============================================================================
    quantity = fields.Float(
        string="Quantity",
        default=1.0,
        required=True,
        digits='Product Unit of Measure',
        help="Quantity of items to be shredded"
    

    weight_kg = fields.Float(
        ,
    string="Weight (kg)",
        digits=(8, 2),
        help="Weight in kilograms"
    

    weight_lbs = fields.Float(
        ,
    string="Weight (lbs)",
        compute='_compute_weight_lbs',
        store=True,
        digits=(8, 2),
        help="Weight in pounds (converted from kg)"
    

    estimated_shred_time = fields.Float(
        ,
    string="Estimated Shred Time (min)",
        digits=(6, 2),
        help="Estimated time to shred this item in minutes"
    

        # ============================================================================
    # STATUS TRACKING
        # ============================================================================
    status = fields.Selection([))
        ('pending', 'Pending Collection'),
        ('collected', 'Collected'),
        ('in_queue', 'In Shred Queue'),
        ('shredding', 'Being Shredded'),
        ('shredded', 'Shredded'),
        ('certified', 'Certified'),
        ('exception', 'Exception')
    

    collection_date = fields.Datetime(
        string="Collection Date",
        tracking=True,
        help="When the item was collected for shredding":
    

    shred_start_time = fields.Datetime(
        string="Shred Start Time",
        help="When shredding of this item started"
    

    shred_completion_time = fields.Datetime(
        string="Shred Completion Time",
        help="When shredding of this item was completed"
    

    certification_date = fields.Datetime(
        string="Certification Date",
        help="When destruction certificate was issued"
    

        # ============================================================================
    # PERSONNEL TRACKING
        # ============================================================================
    collected_by = fields.Many2one(
        "hr.employee",
        string="Collected By",
        help="Employee who collected the item"
    

    shredded_by = fields.Many2one(
        "hr.employee",
        string="Shredded By",
        help="Employee who performed the shredding"
    

    witness_employee_id = fields.Many2one(
        "hr.employee",
        string="Witness",
        help="Employee who witnessed the destruction"
    

        # ============================================================================
    # EQUIPMENT AND PROCESS
        # ============================================================================
    shredding_equipment_id = fields.Many2one(
        "shredding.equipment",
        string="Shredding Equipment",
        help="Equipment used for shredding":
    

    ,
    shred_method = fields.Selection([))
        ('cross_cut', 'Cross Cut'),
        ('strip_cut', 'Strip Cut'),
        ('micro_cut', 'Micro Cut'),
        ('pulverize', 'Pulverize'),
        ('incinerate', 'Incinerate')
    
    security_level = fields.Selection([))
        ('standard', 'Standard'),
        ('confidential', 'Confidential'),
        ('secret', 'Secret'),
        ('top_secret', 'Top Secret')
    

        # ============================================================================
    # COMPLIANCE AND CERTIFICATION
        # ============================================================================
    destruction_certificate_id = fields.Many2one(
        "naid.certificate",
        string="Destruction Certificate",
        readonly=True,
        help="Generated destruction certificate"
    

    naid_compliant = fields.Boolean(
        string="NAID Compliant",
        default=True,
        help="Whether destruction meets NAID AAA standards"
    

    audit_trail_ids = fields.One2many(
        "naid.audit.log",
        "shred_item_id",
        string="Audit Trail",
        readonly=True,
        help="NAID compliance audit trail"
    

    chain_of_custody_id = fields.Many2one(
        "records.chain.of.custody",
        string="Chain of Custody",
        help="Chain of custody record for this item":
    

        # ============================================================================
    # EXCEPTION HANDLING
        # ============================================================================
    exception_reason = fields.Text(
        string="Exception Reason",
        help="Reason for exception status":
    

    resolution_notes = fields.Text(
        string="Resolution Notes",
        help="Notes on how exception was resolved"
    

    exception_resolved = fields.Boolean(
        string="Exception Resolved",
        default=False,
        tracking=True,
        help="Whether exception has been resolved"
    

        # ============================================================================
    # NOTES AND OBSERVATIONS
        # ============================================================================
    collection_notes = fields.Text(
        string="Collection Notes",
        help="Notes from collection process"
    

    shredding_notes = fields.Text(
        string="Shredding Notes",
        help="Notes from shredding process"
    

    quality_notes = fields.Text(
        string="Quality Notes",
        help="Quality control observations"
    

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
    @api.depends('name', 'container_id', 'container_barcode')
    def _compute_display_name(self):
        """Compute display name with container info"""
        for item in self:
            parts = []
            if item.container_id:
                parts.append(item.container_id.name or item.container_barcode)
            if item.name:
                parts.append(item.name)
            else:
                parts.append(_("Shred Item"))

            item.display_name = " - ".join(parts) if parts else _("New Item"):
    @api.depends('weight_kg')
    def _compute_weight_lbs(self):
        """Convert weight from kg to lbs"""
        for item in self:
            if item.weight_kg:
                item.weight_lbs = item.weight_kg * 2.20462  # kg to lbs conversion
            else:
                item.weight_lbs = 0.0

    # ============================================================================
        # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('container_id')
    def _onchange_container_id(self):
        """Update fields when container changes"""
        if self.container_id:
            # Auto-populate container-related fields
            if not self.name:
                self.name = _("Shred: %s", self.container_id.name or self.container_id.barcode)

            # Set estimated weight if available:
            if self.container_id.weight_pounds and not self.weight_kg:
                self.weight_kg = self.container_id.weight_pounds * 0.453592  # lbs to kg

            # Set security level based on container
            if hasattr(self.container_id, 'security_level'):
                self.security_level = self.container_id.security_level

    @api.onchange('status')
    def _onchange_status(self):
        """Update timestamps when status changes"""
        if self.status == 'collected' and not self.collection_date:
    self.collection_date = fields.Datetime.now()
        elif self.status == 'shredding' and not self.shred_start_time:
    self.shred_start_time = fields.Datetime.now()
        elif self.status == 'shredded' and not self.shred_completion_time:
    self.shred_completion_time = fields.Datetime.now()
        elif self.status == 'certified' and not self.certification_date:
    self.certification_date = fields.Datetime.now()

        # ============================================================================
    # ACTION METHODS
        # ============================================================================
    def action_collect_item(self):
        """Mark item as collected"""
        self.ensure_one()
        if self.status != 'pending':
            raise UserError(_("Can only collect pending items"))

        self.write({)}
            'status': 'collected',
            'collection_date': fields.Datetime.now(),
            'collected_by': self.env.user.employee_id.id if self.env.user.employee_id else False:
        

        self._create_audit_log('item_collected')
        self.message_post(body=_("Item collected for shredding")):
    def action_start_shredding(self):
        """Start the shredding process"""
        self.ensure_one()
        if self.status not in ['collected', 'in_queue']:
            raise UserError(_("Can only start shredding collected or queued items"))

        self.write({)}
            'status': 'shredding',
            'shred_start_time': fields.Datetime.now(),
            'shredded_by': self.env.user.employee_id.id if self.env.user.employee_id else False:
        

        self._create_audit_log('shredding_started')
        self.message_post(body=_("Shredding process started"))

    def action_complete_shredding(self):
        """Complete the shredding process"""
        self.ensure_one()
        if self.status != 'shredding':
            raise UserError(_("Can only complete items currently being shredded"))

        # Validate required information
        if not self.shredding_equipment_id:
            raise UserError(_("Please specify the shredding equipment used"))

        if not self.shred_method:
            raise UserError(_("Please specify the shredding method"))

        self.write({)}
            'status': 'shredded',
            'shred_completion_time': fields.Datetime.now()
        

        self._create_audit_log('shredding_completed')
        self._update_container_status()
        self.message_post(body=_("Shredding completed successfully"))

    def action_certify_destruction(self):
        """Certify the destruction and generate certificate"""
        self.ensure_one()
        if self.status != 'shredded':
            raise UserError(_("Can only certify shredded items"))

        # Generate destruction certificate if not exists:
        if not self.destruction_certificate_id:
            self._generate_destruction_certificate()

        self.write({)}
            'status': 'certified',
            'certification_date': fields.Datetime.now()
        

        self._create_audit_log('destruction_certified')
        self.message_post(body=_("Destruction certified"))

    def action_mark_exception(self):
        """Mark item as exception"""
        self.ensure_one()
        if not self.exception_reason:
            raise UserError(_("Please provide an exception reason"))

        self.write({'status': 'exception'})
        self._create_audit_log('exception_marked')
        self.message_post(body=_("Item marked as exception: %s", self.exception_reason))

    def action_resolve_exception(self):
        """Resolve exception and continue process"""
        self.ensure_one()
        if self.status != 'exception':
            raise UserError(_("Can only resolve items with exception status"))

        if not self.resolution_notes:
            raise UserError(_("Please provide resolution notes"))

        self.write({)}
            'status': 'collected',  # Return to collected status
            'exception_resolved': True
        

        self._create_audit_log('exception_resolved')
        self.message_post(body=_("Exception resolved: %s", self.resolution_notes))

    # ============================================================================
        # VALIDATION METHODS
    # ============================================================================
    @api.constrains('quantity')
    def _check_quantity(self):
        """Validate quantity is positive"""
        for item in self:
            if item.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than 0"))

    @api.constrains('weight_kg')
    def _check_weight(self):
        """Validate weight values"""
        for item in self:
            if item.weight_kg < 0:
                raise ValidationError(_("Weight cannot be negative"))
            if item.weight_kg > 1000:  # Reasonable upper limit
                raise ValidationError(_("Weight seems unrealistic. Please verify."))

    @api.constrains('shred_start_time', 'shred_completion_time')
    def _check_shred_times(self):
        """Validate shredding time sequence"""
        for item in self:
            if (item.shred_start_time and item.shred_completion_time and:)
                item.shred_start_time > item.shred_completion_time
                raise ValidationError(_("Shred start time must be before completion time"))

    @api.constrains('collection_date', 'shred_start_time')
    def _check_collection_shred_sequence(self):
        """Validate collection happens before shredding"""
        for item in self:
            if (item.collection_date and item.shred_start_time and:)
                item.collection_date > item.shred_start_time
                raise ValidationError(_("Collection must happen before shredding"))

    # ============================================================================
        # BUSINESS LOGIC METHODS
    # ============================================================================
    def _create_audit_log(self, action_type):
        """Create NAID compliance audit log entry"""
        self.ensure_one()

        audit_vals = {}
            'action_type': action_type,
            'user_id': self.env.user.id,
            'timestamp': fields.Datetime.now(),
            'container_id': self.container_id.id,
            'shred_item_id': self.id,
            'description': _("Shred item %s: %s", self.display_name, action_type),
            'naid_compliant': self.naid_compliant,
        

        return self.env['naid.audit.log'].create(audit_vals)

    def _update_container_status(self):
        """Update container status after shredding"""
        self.ensure_one()
        if self.container_id:
            self.container_id.write({)}
                'status': 'destroyed',
                'destruction_date': fields.Date.today()
            

    def _generate_destruction_certificate(self):
        """Generate destruction certificate for this item""":
        self.ensure_one()

        certificate_vals = {}
            'name': _("Certificate - %s", self.display_name),
            'container_ids': [(6, 0, [self.container_id.id])],
            'destruction_date': fields.Date.today(),
            'destruction_method': self.shred_method,
            'equipment_id': self.shredding_equipment_id.id if self.shredding_equipment_id else False,:
            'witness_id': self.witness_employee_id.id if self.witness_employee_id else False,:
            'naid_compliant': self.naid_compliant,
        

        certificate = self.env['naid.certificate'].create(certificate_vals)
        self.destruction_certificate_id = certificate.id
        return certificate

    def get_process_duration(self):
        """Calculate processing duration metrics"""
        self.ensure_one()

        durations = {}

        if self.collection_date and self.shred_start_time:
            delta = self.shred_start_time - self.collection_date
            durations['queue_time'] = delta.total_seconds() / 3600  # hours

        if self.shred_start_time and self.shred_completion_time:
            delta = self.shred_completion_time - self.shred_start_time
            durations['shred_time'] = delta.total_seconds() / 60  # minutes

        if self.collection_date and self.certification_date:
            delta = self.certification_date - self.collection_date
            durations['total_time'] = delta.total_seconds() / 3600  # hours

        return durations

    # ============================================================================
        # REPORTING METHODS
    # ============================================================================
    @api.model
    def get_shredding_statistics(self, date_from=None, date_to=None):
        """Get shredding statistics for reporting""":
        domain = []
        if date_from:
            domain.append(('collection_date', '>=', date_from))
        if date_to:
            domain.append(('collection_date', '<=', date_to))

        items = self.search(domain)

        stats = {}
            'total_items': len(items),
            'total_weight_kg': sum(items.mapped('weight_kg')),
            'by_status': {},
            'by_container_type': {},
            'by_security_level': {},
        

        # Status distribution
        for status in ['pending', 'collected', 'shredded', 'certified', 'exception']:
            status_items = items.filtered(lambda i: i.status == status)
            stats['by_status'][status] = {}
                'count': len(status_items),
                'weight_kg': sum(status_items.mapped('weight_kg'))
            

        # Container type distribution
        for item in items:
            container_type = item.container_type or 'unknown'
            if container_type not in stats['by_container_type']:
                stats['by_container_type'][container_type] = {}
                    'count': 0,
                    'weight_kg': 0.0
                
            stats['by_container_type'][container_type]['count'] += 1
            stats['by_container_type'][container_type]['weight_kg'] += item.weight_kg or 0

        # Security level distribution
        for item in items:
            security_level = item.security_level or 'standard'
            if security_level not in stats['by_security_level']:
                stats['by_security_level'][security_level] = {}
                    'count': 0,
                    'weight_kg': 0.0
                
            stats['by_security_level'][security_level]['count'] += 1
            stats['by_security_level'][security_level]['weight_kg'] += item.weight_kg or 0

        return stats

    # ============================================================================
        # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set defaults and create audit logs"""
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = _("Shred Item %s", fields.Datetime.now().strftime('%Y%m%d-%H%M%S'))

        items = super().create(vals_list)

        for item in items:
            item._create_audit_log('item_created')

        return items

    def write(self, vals):
        """Override write to track status changes"""
        result = super().write(vals)

        if 'status' in vals:
            for item in self:
                status_label = dict(item._fields['status'].selection)[item.status]
                item.message_post(body=_("Status changed to %s", status_label))

        return result

    def name_get(self):
        """Custom name display"""
        result = []
        for item in self:
            name = item.display_name or item.name
            if item.status != 'pending':
                status_label = dict(item._fields['status'].selection)[item.status]
                name = _("%s [%s]", name, status_label)
            result.append((item.id, name))
        return result

    # ============================================================================
        # INTEGRATION METHODS
    # ============================================================================
    def action_view_container(self):
        """View the related container"""
        self.ensure_one()
        return {}
            'type': 'ir.actions.act_window',
            'name': _('Container Details'),
            'res_model': 'records.container',
            'res_id': self.container_id.id,
            'view_mode': 'form',
            'target': 'current',
        

    def action_view_destruction_certificate(self):
        """View destruction certificate"""
        self.ensure_one()
        if not self.destruction_certificate_id:
            raise UserError(_("No destruction certificate available"))

        return {}
            'type': 'ir.actions.act_window',
            'name': _('Destruction Certificate'),
            'res_model': 'naid.certificate',
            'res_id': self.destruction_certificate_id.id,
            'view_mode': 'form',
            'target': 'current',
        

    def action_print_label(self):
        """Print item label for tracking""":
        self.ensure_one()
        return self.env.ref('records_management.shred_item_label_report').report_action(self)

)))))))))))))))))))))))))))))))))