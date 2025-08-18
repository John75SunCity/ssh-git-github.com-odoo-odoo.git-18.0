from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaperBaleMovement(models.Model):
    _name = 'paper.bale.movement'
    _description = 'Paper Bale Movement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'movement_date desc, id desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Movement Reference", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    bale_id = fields.Many2one('paper.bale', string="Paper Bale", required=True, ondelete='cascade')
    source_location_id = fields.Many2one('stock.location', string="Source Location", required=True)
    destination_location_id = fields.Many2one('stock.location', string="Destination Location", required=True)
    movement_date = fields.Datetime(string="Movement Date", default=fields.Datetime.now, required=True)
    responsible_user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    notes = fields.Text(string='Movement Notes')

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('source_location_id', 'destination_location_id')
    def _check_locations(self):
        for movement in self:
            if movement.source_location_id == movement.destination_location_id:
                raise ValidationError(_("Source and destination locations cannot be the same."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_transit(self):
        self.ensure_one()
        self.write({"state": "in_transit"})
        self.message_post(body=_("Movement has started and is now in transit."))

    def action_complete_movement(self):
        self.ensure_one()
        self.write({"state": "completed"})
        self.bale_id.location_id = self.destination_location_id
        self.message_post(body=_("Movement completed. Bale is now at %s", self.destination_location_id.display_name))

    def action_cancel_movement(self):
        self.ensure_one()
        self.write({"state": "cancelled"})
        self.message_post(body=_("Movement has been cancelled."))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add auto-numbering"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('paper.bale.movement') or _('New')
        return super().create(vals_list)
