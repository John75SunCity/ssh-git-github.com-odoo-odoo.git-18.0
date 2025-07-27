# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DestructionItem(models.Model):
    """Model for tracking individual items to be destroyed in shredding services."""
    _name = 'destruction.item'
    _description = 'Destruction Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'item_type, name'
    _rec_name = 'name'

    # Core identification fields
    name = fields.Char(string='Item Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    
    # Required relationship to shredding service
    service_id = fields.Many2one('shredding.service', string='Shredding Service', required=True, ondelete='cascade')
    
    # Item categorization
    item_type = fields.Selection([
        ('document', 'Document',
        ('box', 'Box'),
        ('hard_drive', 'Hard Drive'),
        ('media', 'Electronic Media'),
        ('uniform', 'Uniform/Textile'),
        ('other', 'Other')
    
    # Quantity and measurements), string="Selection Field"
    quantity = fields.Integer(string='Quantity', default=1, required=True)
    unit_of_measure = fields.Selection([
        ('piece', 'Piece'),
        ('box', 'Box'),
        ('pound', 'Pound'),
        ('kilogram', 'Kilogram'),
        ('bag', 'Bag'),
        ('pallet', 'Pallet')
), string="Selection Field"
    weight = fields.Float(string='Weight (lbs)', help='Weight of the item in pounds')
    
    # Destruction tracking
    destroyed = fields.Boolean(string='Destroyed', default=False, tracking=True)
    destruction_date = fields.Datetime(string='Destruction Date')
    destruction_method = fields.Selection([
        ('shred', 'Shredding'),
        ('incinerate', 'Incineration'),
        ('crush', 'Crushing'),
        ('degauss', 'Degaussing'),
        ('other', 'Other')
    
    # Chain of custody), string="Selection Field"
    custodian_id = fields.Many2one('res.users', string='Current Custodian', default=lambda self: self.env.user)
    location_id = fields.Many2one('records.location', string='Current Location')
    
    # Security and compliance
    confidentiality_level = fields.Selection([
        ('public', 'Public',
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
        ('top_secret', 'Top Secret')
    
    # NAID compliance), string="Selection Field"
    naid_compliant = fields.Boolean(string='NAID Compliant', default=True)
    certificate_required = fields.Boolean(string='Certificate Required', default=True)
    certificate_number = fields.Char(string='Certificate Number')
    
    # Documentation
    notes = fields.Text(string='Notes')
    photos = fields.Many2many('ir.attachment', relation='photos_rel', string='Photos',
                             domain="[('res_model', '=', 'destruction.item')  # Fixed: was One2many with missing inverse field]",
                             compute='_compute_photos'
    
    # Standard fields
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible User', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)
    
    # Computed fields
    total_weight = fields.Float(string='Total Weight', compute='_compute_total_weight', store=True)
    
    @api.depends('quantity', 'weight')
    def _compute_total_weight(self):
        """Compute total weight based on quantity and unit weight."""
        for record in self:
            record.total_weight = record.quantity * record.weight
    
    def action_mark_destroyed(self):
        """Mark item as destroyed with timestamp."""
        self.ensure_one()
        self.write({
            'destroyed': True,
            'destruction_date': fields.Datetime.now()
        }
        self.message_post(body=_('Item marked as destroyed'))
    
    def action_generate_certificate(self):
        """Generate destruction certificate for this item."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generate Destruction Certificate'),
            'res_model': 'destruction.certificate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_item_id': self.id}
        }

    @api.depends()
    def _compute_photos(self):
        """Compute photos (attachments) for this destruction item"""
        for record in self:
            record.photos = self.env['ir.attachment'].search\([
                ('res_model', '=', 'destruction.item'),
                ('res_id', '=', record.id)])
            ]
