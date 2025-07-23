from odoo import models, fields, api, _

class RecordsLocation(models.Model):
    _name = 'records.location'
    _description = 'Records Storage Location'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    code = fields.Char('Location Code', required=False, index=True, help='Short code for this location (for barcode, reference, etc.)')
    name = fields.Char('Location Name', required=True, tracking=True)
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', recursive=True, store=True)
    parent_id = fields.Many2one('records.location', 'Parent Location', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('records.location', 'parent_id', 'Child Locations')

    # Location Type for Business Operations
    location_type = fields.Selection([
        ('aisles', 'Aisles - Standard File Boxes (Type 01)'),
        ('pallets', 'Pallets - Standard File Boxes (Type 01)'),
        ('vault', 'Vault - Specialty Boxes (Type 06)'),
        ('map', 'Map Storage - Map Boxes (Type 03)'),
        ('oversize', 'Oversize - Odd-Shaped Boxes (Type 04)'),
        ('refiles', 'Refiles - Staging for Returns/Put-Away'),
    ], string='Location Type', required=True, default='aisles', tracking=True,
       help="""Location type determines what kind of boxes can be stored:
       • Aisles/Pallets: Standard file boxes (Type 01) - monthly rent
       • Vault: Specialty boxes (Type 06) - secure storage
       • Map: Map boxes (Type 03) - oversized maps/plans
       • Oversize: Odd-shaped boxes (Type 04) - temporary storage during split
       • Refiles: Staging area for returned files before put-away""")

    box_ids = fields.One2many('records.box', 'location_id', string='Boxes')
    box_count = fields.Integer('Box Count', compute='_compute_box_count')
    capacity = fields.Integer('Maximum Box Capacity')
    utilization_percentage = fields.Float('Utilization %', compute='_compute_used_capacity', store=True,
                                         help="Percentage of location capacity currently used")
    current_occupancy = fields.Integer('Current Occupancy', compute='_compute_box_count', store=True,
                                      help="Current number of boxes stored in this location")

    active = fields.Boolean(default=True)
    note = fields.Text('Notes')
    description = fields.Text(
        'Description',
        help='Detailed description of the location and its contents'
    )
    access_instructions = fields.Text(
        'Access Instructions',
        help='Instructions for accessing this location (keys, codes, etc.)'
    )
    security_level = fields.Selection([
        ('low', 'Low - General Access'),
        ('medium', 'Medium - Restricted Access'),
        ('high', 'High - Secure Access'),
        ('maximum', 'Maximum - Vault Access')
    ], string='Security Level', default='medium')

    # Phase 1 Critical Fields - Added by automated script
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    customer_id = fields.Many2one('res.partner', string='Customer')
    state = fields.Selection([('active', 'Active'), ('inactive', 'Inactive')], string='State', default='active')
    storage_date = fields.Date('Storage Date')

    # Phase 2 Audit & Compliance Fields - Added by automated script
    security_audit_ids = fields.One2many('records.security.audit', 'location_id', string='Security Audits')
    last_security_audit = fields.Date('Last Security Audit')
    security_certification = fields.Selection([('none', 'None'), ('basic', 'Basic Security'), ('enhanced', 'Enhanced Security'), ('maximum', 'Maximum Security')], string='Security Certification', default='basic')
    access_control_system = fields.Boolean('Access Control System', default=False)
    surveillance_system = fields.Boolean('Surveillance System', default=False)
    alarm_system = fields.Boolean('Alarm System', default=False)
    fire_detection_system = fields.Boolean('Fire Detection System', default=False)
    environmental_controls_verified = fields.Boolean('Environmental Controls Verified', default=False)
    temperature_controlled = fields.Boolean('Temperature Controlled', default=False)
    humidity_controlled = fields.Boolean('Humidity Controlled', default=False)
    pest_control_program = fields.Boolean('Pest Control Program', default=False)
    hazmat_compliance = fields.Boolean('HAZMAT Compliance', default=False)
    inspection_required = fields.Boolean('Regular Inspection Required', default=True)
    inspection_frequency = fields.Selection([('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly')], string='Inspection Frequency', default='monthly')
    last_inspection_date = fields.Date('Last Inspection Date')
    next_inspection_date = fields.Date('Next Inspection Date', compute='_compute_next_inspection')
    inspection_log_ids = fields.One2many('records.location.inspection', 'location_id', string='Inspection Log')
    compliance_violations_count = fields.Integer('Compliance Violations', compute='_compute_violations_count')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for location in self:
            if location.parent_id:
                location.complete_name = '%s / %s' % (location.parent_id.complete_name, location.name)
            else:
                location.complete_name = location.name

    @api.depends('box_ids')
    def _compute_box_count(self):
        for location in self:
            count = len(location.box_ids)
            location.box_count = count
            location.current_occupancy = count  # Set both fields

    @api.depends('box_count', 'capacity')
    def _compute_used_capacity(self):
        for location in self:
            if location.capacity:
                percentage = (location.box_count / location.capacity) * 100
                location.utilization_percentage = percentage
            else:
                location.utilization_percentage = 0

    def action_view_boxes(self):
        self.ensure_one()
        return {
            'name': _('Boxes'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.box',
            'view_mode': 'tree,form',
            'domain': [('location_id', '=', self.id)],
            'context': {'default_location_id': self.id},
        }

    def action_location_report(self):
        """Generate a utilization and capacity report for this location."""
        self.ensure_one()
        return {
            'name': _('Location Report: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.location.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_location_id': self.id,
                'default_location_name': self.name,
                'default_include_child_locations': True,
            }
        }

    def action_relocate_boxes(self):
        """Relocate boxes from this location"""
        self.ensure_one()
        return {
            'name': _('Relocate Boxes'),
            'type': 'ir.actions.act_window',
            'res_model': 'box.relocation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_source_location_id': self.id},
        }

    def action_check_capacity(self):
        """Check location capacity"""
        self.ensure_one()
        self._compute_utilization_percentage()
        return True

    def action_view_child_locations(self):
        """View child locations"""
        self.ensure_one()
        return {
            'name': _('Child Locations'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.location',
            'view_mode': 'tree,form',
            'domain': [('parent_id', '=', self.id)],
            'context': {'default_parent_id': self.id},
        }

    def action_archive_location(self):
        """Archive this location"""
        self.ensure_one()
        if self.box_count > 0:
            raise ValidationError(_("Cannot archive location with boxes. Please relocate boxes first."))
        self.active = False
        return True

    def action_print_location_label(self):
        """Print location label"""
        self.ensure_one()
        return {
            'name': _('Print Location Label'),
            'type': 'ir.actions.report',
            'report_name': 'records_management.location_label_report',
            'report_type': 'qweb-pdf',
            'report_file': 'records_management.location_label_report',
            'context': {'active_ids': [self.id]},
        }

    def action_view_boxes(self):
        """View boxes in this location"""
        self.ensure_one()
        return {
            'name': _('Boxes in %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.box',
            'view_mode': 'tree,form',
            'domain': [('location_id', '=', self.id)],
            'context': {'default_location_id': self.id},
        }

    def action_location_report(self):
        """Generate location report"""
        self.ensure_one()
        return {
            'name': _('Location Report: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'location.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_location_id': self.id},
        }
