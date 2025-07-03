from odoo import models, fields, api, _

class RecordsLocation(models.Model):
    _name = 'records.location'
    _description = 'Records Storage Location'
    _inherit = ['mail.thread']
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'
    
    name = fields.Char('Location Name', required=True, tracking=True)
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', recursive=True, store=True)
    parent_id = fields.Many2one('records.location', 'Parent Location', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('records.location', 'parent_id', 'Child Locations')
    
    box_ids = fields.One2many('records.box', 'location_id', string='Boxes')
    box_count = fields.Integer('Box Count', compute='_compute_box_count')
    capacity = fields.Integer('Maximum Box Capacity')
    used_capacity = fields.Float('Used Capacity (%)', compute='_compute_used_capacity')
    
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
            location.box_count = len(location.box_ids)
    
    @api.depends('box_count', 'capacity')
    def _compute_used_capacity(self):
        for location in self:
            if location.capacity:
                location.used_capacity = (location.box_count / location.capacity) * 100
            else:
                location.used_capacity = 0
                
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