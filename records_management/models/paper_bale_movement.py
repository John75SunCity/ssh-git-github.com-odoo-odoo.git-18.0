from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class PaperBaleMovement(models.Model):
    _name = 'paper.bale.movement'
    _description = 'Paper Bale Movement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'movement_date desc, id desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    active = fields.Boolean()
    company_id = fields.Many2one()
    bale_id = fields.Many2one()
    source_location_id = fields.Many2one()
    destination_location_id = fields.Many2one()
    movement_date = fields.Datetime()
    responsible_user_id = fields.Many2one()
    state = fields.Selection()
    notes = fields.Text(string='Movement Notes')
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _check_locations(self):
            for movement in self:
                if movement.source_location_id == movement.destination_location_id:
                    raise ValidationError()
                        _("Source and destination locations cannot be the same.")



    def action_start_transit(self):
            self.ensure_one()
            self.write({"state": "in_transit"})


    def action_complete_movement(self):
            self.ensure_one()
            self.write({"state": "completed"})
            for movement in self:
                movement.bale_id.location_id = movement.destination_location_id


    def action_cancel_movement(self):
            self.ensure_one()
            self.write({"state": "cancelled"})

        # ============================================================================
            # ORM METHODS
        # ============================================================================

    def create(self, vals_list):
            """Override create to add auto-numbering"""
            for vals in vals_list:
                if vals.get('name', _('New')) == _('New'):
                    vals['name') = self.env['ir.sequence'].next_by_code('paper.bale.movement') or _('New')
            return super().create(vals_list)

        # ============================================================================
            # MAIL THREAD FRAMEWORK FIELDS
        # ============================================================================
