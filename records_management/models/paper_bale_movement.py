# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PaperBaleMovement(models.Model):
    """
    Tracks the physical movement of a paper bale from a source to a destination
    location. This model is essential for maintaining a clear chain of custody,
    recording who moved a bale, where it went, and when the movement occurred.
    """
    _name = 'paper.bale.movement'
    _description = 'Paper Bale Movement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'movement_date desc, id desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(
        string="Movement Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: "New"
    )
    bale_id = fields.Many2one(
        'paper.bale',
        string="Paper Bale",
        required=True,
        ondelete='cascade',
        index=True
    )
    source_location_id = fields.Many2one(
        'stock.location',
        string="Source Location",
        required=True,
        tracking=True
    )
    destination_location_id = fields.Many2one(
        'stock.location',
        string="Destination Location",
        required=True,
        tracking=True
    )
    movement_date = fields.Datetime(
        string="Movement Date",
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )
    responsible_user_id = fields.Many2one(
        'res.users',
        string="Responsible",
        default=lambda self: self.env.user,
        tracking=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True, required=True)

    notes = fields.Text(string='Movement Notes')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    active = fields.Boolean(default=True)

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('source_location_id', 'destination_location_id')
    def _check_locations(self):
        """Prevents a movement from having the same source and destination."""
        for movement in self:
            if movement.source_location_id == movement.destination_location_id:
                raise ValidationError(_("Source and destination locations cannot be the same."))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides create to assign a unique sequential name and to set the initial
        source location on the bale if it's not already set.
        """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('paper.bale.movement') or _('New')

            # Set the bale's initial location based on the first movement
            if 'bale_id' in vals and 'source_location_id' in vals:
                bale = self.env['paper.bale'].browse(vals['bale_id'])
                if not bale.location_id:
                    bale.write({'location_id': vals['source_location_id']})

        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_transit(self):
        """Sets the movement state to 'in_transit'."""
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_("Only draft movements can be started."))
        self.write({"state": "in_transit"})
        self.message_post(body=_("Movement has started and is now in transit."))

    def action_complete_movement(self):
        """
        Completes the movement, updating the bale's current location and setting
        the movement state to 'completed'.
        """
        self.ensure_one()
        if self.state != 'in_transit':
            raise ValidationError(_("Only movements that are in transit can be completed."))
        self.write({"state": "completed"})
        self.bale_id.write({'location_id': self.destination_location_id.id})
        self.message_post(body=_("Movement completed. Bale is now at: %s", self.destination_location_id.display_name))

    def action_cancel_movement(self):
        """Cancels the movement if it's in a draft state."""
        self.ensure_one()
        if self.state not in ('draft', 'in_transit'):
            raise ValidationError(_("Only draft or in-transit movements can be cancelled."))
        self.write({"state": "cancelled"})
        self.message_post(body=_("Movement has been cancelled."))

