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
    ], string='Location Type', required=True, default='aisles',
       help="""Location type determines what kind of boxes can be stored:
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