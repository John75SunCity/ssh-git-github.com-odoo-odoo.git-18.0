# -*- coding: utf-8 -*-
"""
Box Movement History
"""

from odoo import models, fields, api, _


class RecordsBoxMovement(models.Model):
    """
    Records Box Movement History
    Tracks all box location changes and transfers
    """

    _name = "rec.box.move"  # Abbreviated: records.box.movement -> rec.box.move
    _description = "Records Box Movement History"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "move_date desc, name"

    # Core fields
    name = fields.Char(string="Movement Reference", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Movement specific fields
    box_id = fields.Many2one('rec.box', string='Box', required=True, tracking=True)
    from_location_id = fields.Many2one('rec.loc', string='From Location', tracking=True)
    to_location_id = fields.Many2one('rec.loc', string='To Location', required=True, tracking=True)
    move_date = fields.Datetime(string='Movement Date', default=fields.Datetime.now, required=True)
    move_reason = fields.Selection([
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery'),
        ('transfer', 'Internal Transfer'),
        ('storage', 'Storage Assignment'),
        ('retrieval', 'Document Retrieval'),
        ('destruction', 'Destruction'),
        ('audit', 'Audit Check'),
        ('maintenance', 'Maintenance')
    ], string='Movement Reason', required=True, tracking=True)

    # Personnel tracking
    moved_by_id = fields.Many2one('res.users', string='Moved By', default=lambda self: self.env.user)
    authorized_by_id = fields.Many2one('res.users', string='Authorized By')
    
    # Status tracking
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft', tracking=True)

    # Additional details
    description = fields.Text(string='Movement Description')
    notes = fields.Text(string='Internal Notes')
    external_ref = fields.Char(string='External Reference')
    
    # GPS coordinates (if available)
    gps_lat = fields.Float(string='GPS Latitude', digits=(10, 7))
    gps_lng = fields.Float(string='GPS Longitude', digits=(10, 7))
    
    # Timestamps
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now)
    completed_date = fields.Datetime(string='Completed Date')

    @api.model
    def create(self, vals):
        """Generate sequence number for movement reference"""
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('rec.box.move') or 'MOVE/'
        return super().create(vals)

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
