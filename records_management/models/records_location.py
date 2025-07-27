from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsLocation(models.Model):
    _name = 'records.location'
    _description = 'Records Storage Location'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    code = fields.Char('Location Code', required=False, index=True, help='Short code for this location (for barcode, reference, etc.)')
    name = fields.Char('Location Name', required=True)
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', recursive=True, store=True)
    parent_id = fields.Many2one('records.location', 'Parent Location', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('records.location', 'parent_id', string='Child Locations')

    # Location Type for Business Operations
    location_type = fields.Selection([
        ('aisles', 'Aisles - Standard File Boxes (Type 01)'),
        ('pallets', 'Pallets - Standard File Boxes (Type 01)'),
        ('vault', 'Vault - Specialty Boxes (Type 06)'),
        ('map', 'Map Storage - Map Boxes (Type 03)'),
        ('oversize', 'Oversize - Odd-Shaped Boxes (Type 04)'),
        ('refiles', 'Refiles - Staging for Returns/Put-Away'),
    ], string='Location Type', help="""Location type determines what kind of boxes can be stored:,
       • Aisles/Pallets: Standard file boxes (Type 01) - monthly rent
       • Vault: Specialty boxes (Type 06) - secure storage
       • Map: Map boxes (Type 03) - oversized maps/plans
       • Oversize: Odd-shaped boxes (Type 04) - temporary storage during split
       • Refiles: Staging area for returned files before put-away""")

    box_ids = fields.One2many('records.box', 'location_id', string='Boxes')
    box_count = fields.Integer('Physical Box Count', compute='_compute_box_count', compute_sudo=False,
                              help="Actual number of boxes physically stored in this location")
    capacity = fields.Integer('Maximum Box Capacity', help="Maximum number of boxes this location can hold")
    current_utilization = fields.Float('Utilization %', compute='_compute_current_utilization', store=True, compute_sudo=False,
                                      help="Percentage of capacity utilized (box_count / capacity * 100) - shows storage efficiency")
    available_utilization = fields.Float('Available %', compute='_compute_available_utilization', store=True, compute_sudo=False,
                                         help="Percentage of capacity available (100 - current_utilization) - shows remaining space")
    available_spaces = fields.Integer('Available Spaces', compute='_compute_available_spaces', store=True, compute_sudo=False,
                                     help="Number of open spaces available (capacity - box_count) - actual quantity available")

    # Business tracking fields
    customer_id = fields.Many2one(
        'res.partner', 
        string='Customer',
        domain=[('is_company', '=', True)],
        help="Customer associated with this location"
    )
    
    storage_date = fields.Date(
        string='Storage Date',
        help="Date when items were first stored in this location"
    )

    active = fields.Boolean(default=True)
    note = fields.Text('Notes')
    description = fields.Text(
        'Description',
        help='Detailed description of the location and its contents',
    )
    
    access_instructions = fields.Text(
        'Access Instructions',
        help='Instructions for accessing this location (keys, codes, etc.)',
    )
    
    security_level = fields.Selection([
        ('low', 'Low - General Access'),
        ('medium', 'Medium - Restricted Access'),
        ('high', 'High - Secure Access'),
        ('maximum', 'Maximum - Vault Access'),
    ], string='Security Level')

    # Phase 1 Critical Fields - Added by automated script
    
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        """Compute complete hierarchical name"""
        for record in self:
            if record.parent_id:
    pass
                record.complete_name = f"{record.parent_id.complete_name} / {record.name}"
            else:
                record.complete_name = record.name or ''
    
    @api.depends()
    def _compute_box_count(self):
        """Compute number of boxes in this location"""
        for record in self:
            boxes = self.env['records.box'].search([('location_id', '=', record.id)])
            record.box_count = len(boxes)
    
    @api.depends('box_count', 'capacity')
    def _compute_current_utilization(self):
        """Compute current utilization percentage"""
        for record in self:
            if record.capacity and record.capacity > 0:
    pass
                record.current_utilization = (record.box_count / record.capacity) * 100
            else:
                record.current_utilization = 0.0
    
    @api.depends('current_utilization')
    def _compute_available_utilization(self):
        """Compute available utilization percentage"""
        for record in self:
            record.available_utilization = max(0, 100 - record.current_utilization)
    
    @api.depends('capacity', 'box_count')
    def _compute_available_spaces(self):
        """Compute number of available spaces"""
        for record in self:
            record.available_spaces = max(0, (record.capacity or 0) - record.box_count)

    # Action Methods
    def action_view_boxes(self):
        """View all boxes stored in this location"""
        self.ensure_one()
        return {
            'name': _('Boxes in %s') % self.complete_name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.box',
            'view_mode': 'tree,form',
            'domain': [('location_id', '=', self.id)],
            'context': {
                'default_location_id': self.id,
                'search_default_location_id': self.id
            }
        }

    def action_location_report(self):
        """Generate location utilization report"""
        self.ensure_one()
        return {
            'name': _('Location Report - %s') % self.complete_name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.location.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_location_id': self.id,
                'default_location_name': self.complete_name,
                'default_current_utilization': self.current_utilization,
                'default_total_capacity': self.capacity,
                'default_report_date': fields.Date.today()
            }
        }