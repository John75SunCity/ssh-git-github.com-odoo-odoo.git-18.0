from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsBox(models.Model):
    _name = 'records.box'
    _description = 'Document Storage Box'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char('Box Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    
    # Enhanced container identification (from O'Neil Stratus)
    alternate_code = fields.Char('Alternate Code', copy=False,
                                 help="Alternative box identifier")
    description = fields.Char('Description', required=True,
                              help="Human-readable description of the box")
    
    # Status and workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('destroyed', 'Destroyed')
    ], string='Status', default='draft', tracking=True)
    
    # Enhanced status tracking (from O'Neil Stratus)
    item_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('permanent_out', 'Permanent Out'),
        ('destroyed', 'Destroyed'),
        ('archived', 'Archived')
    ], string='Item Status', default='active', tracking=True)
    
    status_date = fields.Datetime('Status Date', default=fields.Datetime.now,
                                  tracking=True)
    add_date = fields.Datetime('Add Date', default=fields.Datetime.now,
                               readonly=True)
    destroy_date = fields.Date('Destroy Date')
    
    # Access tracking
    access_count = fields.Integer('Access Count', default=0,
                                  help="Number of times this box accessed")
    perm_flag = fields.Boolean('Permanent Flag', default=False,
                               help="Mark as permanent record")

    # Box details
    product_id = fields.Many2one(
        'product.product', string='Box Product',
        default=lambda self: self.env.ref(
            'records_management.product_box', False))
    location_id = fields.Many2one(
        'records.location', string='Storage Location',
        tracking=True, index=True)
    location_code = fields.Char('Location Code', related='location_id.code',
                                readonly=True)
    
    # Enhanced container type and categorization
    container_type = fields.Selection([
        ('standard', 'Standard Box'),
        ('map_box', 'Map Box'),
        ('specialty', 'Specialty Box'),
        ('pallet', 'Pallet'),
        ('other', 'Other')
    ], string='Container Type', default='standard', tracking=True)
    
    # Security and categorization
    security_code = fields.Char('Security Code',
                                help="Security classification code")
    category_code = fields.Char('Category Code',
                                help="Category classification code")
    record_series = fields.Char('Record Series',
                                help="Record series identifier")
    
    # Enhanced object and account codes
    object_code = fields.Char('Object Code',
                              help="Object code for billing/tracking")
    
    # Account hierarchy (Level 1/2/3 from O'Neil Stratus)
    account_level1 = fields.Char('Account Level 1',
                                 help="Top level account code")
    account_level2 = fields.Char('Account Level 2',
                                 help="Second level account code")
    account_level3 = fields.Char('Account Level 3',
                                 help="Third level account code")
    
    # Sequence and date ranges
    sequence_from = fields.Integer('Sequence From',
                                   help="Starting sequence number")
    sequence_to = fields.Integer('Sequence To',
                                 help="Ending sequence number")
    date_from = fields.Date('Date From',
                            help="Starting date for records in this box")
    date_to = fields.Date('Date To',
                          help="Ending date for records in this box")
    
    # User-defined fields (from O'Neil Stratus)
    user_field1 = fields.Char('User Field 1',
                              help="Customizable field 1")
    user_field2 = fields.Char('User Field 2',
                              help="Customizable field 2")
    user_field3 = fields.Char('User Field 3',
                              help="Customizable field 3")
    user_field4 = fields.Char('User Field 4',
                              help="Customizable field 4")
    
    # Custom date field
    custom_date = fields.Date('Custom Date',
                              help="Custom date field for special tracking")
    
    # Storage and billing flags
    charge_for_storage = fields.Boolean('Charge for Storage', default=True,
                                        help="Include in storage billing")
    charge_for_add = fields.Boolean('Charge for Add', default=True,
                                    help="Charge for initial box setup")
    
    capacity = fields.Integer('Capacity (documents)', default=100)
    used_capacity = fields.Float(
        'Used Capacity (%)', compute='_compute_used_capacity')
    barcode = fields.Char('Barcode', copy=False)
    
    # Enhanced barcode configuration
    barcode_length = fields.Integer('Barcode Length', default=12,
                                    help="Expected length of barcode")
    barcode_type = fields.Selection([
        ('code128', 'Code 128'),
        ('code39', 'Code 39'),
        ('upc', 'UPC'),
        ('ean13', 'EAN-13'),
        ('qr', 'QR Code'),
        ('other', 'Other')
    ], string='Barcode Type', default='code128')

    # Document management
    document_ids = fields.One2many(
        'records.document', 'box_id', string='Documents')
    document_count = fields.Integer(
        compute='_compute_document_count', string='Document Count',
        store=True)

    # Additional info
    notes = fields.Html('Notes')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)
    # Hierarchical access fields
    customer_id = fields.Many2one(
        'res.partner', string='Customer',
        domain="[('is_company', '=', True)]",
        tracking=True, index=True)
    department_id = fields.Many2one(
        'records.department', string='Department',
        tracking=True, index=True)
    user_id = fields.Many2one(
        'res.users', string='Responsible',
        default=lambda self: self.env.user, tracking=True)
    create_date = fields.Datetime('Created on', readonly=True)
    destruction_date = fields.Date('Destruction Date')
    color = fields.Integer('Color Index')
    tag_ids = fields.Many2many('records.tag', string='Tags')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('records.box') or
                    _('New'))
        return super().create(vals_list)

    @api.depends('document_ids')
    def _compute_document_count(self):
        for box in self:
            box.document_count = len(box.document_ids)

    @api.depends('document_ids', 'capacity')
    def _compute_used_capacity(self):
        for box in self:
            if box.capacity:
                box.used_capacity = (box.document_count / box.capacity) * 100
            else:
                box.used_capacity = 0

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('box_id', '=', self.id)],
            'context': {'default_box_id': self.id},
        }

    def action_set_active(self):
        self.write({'state': 'active'})

    def action_archive_box(self):
        self.write({'state': 'archived'})

    def action_destroy_box(self):
        self.write({
            'state': 'destroyed',
            'item_status': 'destroyed',
            'destroy_date': fields.Date.today(),
            'status_date': fields.Datetime.now()
        })

    def action_increment_access(self):
        """Increment access count when box is accessed"""
        self.write({
            'access_count': self.access_count + 1
        })

    def action_permanent_out(self):
        """Mark box as permanently out"""
        self.write({
            'item_status': 'permanent_out',
            'state': 'archived',
            'status_date': fields.Datetime.now()
        })

    @api.constrains('barcode', 'barcode_length')
    def _check_barcode_length(self):
        """Validate barcode length if specified"""
        for box in self:
            if (box.barcode and box.barcode_length and
                    len(box.barcode) != box.barcode_length):
                raise ValidationError(
                    _("Barcode length mismatch for box %s. "
                      "Expected %s digits, got %s.") %
                    (box.name, box.barcode_length, len(box.barcode)))

    @api.constrains('sequence_from', 'sequence_to')
    def _check_sequence_range(self):
        """Validate sequence range"""
        for box in self:
            if (box.sequence_from and box.sequence_to and
                    box.sequence_from > box.sequence_to):
                raise ValidationError(
                    _("Invalid sequence range for box %s. "
                      "From (%s) cannot be greater than To (%s).") %
                    (box.name, box.sequence_from, box.sequence_to))

    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        """Validate date range"""
        for box in self:
            if (box.date_from and box.date_to and
                    box.date_from > box.date_to):
                raise ValidationError(
                    _("Invalid date range for box %s. "
                      "From (%s) cannot be greater than To (%s).") %
                    (box.name, box.date_from, box.date_to))

    @api.constrains('document_count', 'capacity')
    def _check_capacity(self):
        for box in self:
            if box.document_count > box.capacity:
                raise ValidationError(
                    _("Box %s is over capacity! Maximum is %s documents.") %
                    (box.name, box.capacity))

    def write(self, vals):
        """Update documents when box customer/department changes"""
        result = super().write(vals)
        if 'customer_id' in vals or 'department_id' in vals:
            for box in self:
                box.document_ids.write({
                    'customer_id': (box.customer_id.id
                                    if box.customer_id else False),
                    'department_id': (box.department_id.id
                                      if box.department_id else False),
                })
        return result
