from odoo import models, fields, api, _

class RecordsLocation(models.Model):
    _name = 'records.location'
    _description = 'Records Storage Location'
    _inherit = ['mail.thread']
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
