# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaperBaleMovement(models.Model):
    _name = "paper.bale.movement"
    _description = "Paper Bale Movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "movement_date desc, id desc"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Movement Reference",
        required=True,
        tracking=True,
        index=True,
        default=lambda self: _('New'),
        help="Unique identifier for this movement"
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
        help="Set to false to hide this record"
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        help="Company this movement belongs to"
    )
    
    # ============================================================================
    # BUSINESS SPECIFIC FIELDS  
    # ============================================================================
    bale_id = fields.Many2one(
        "paper.bale", string="Paper Bale", required=True, ondelete="cascade"
    )
    source_location_id = fields.Many2one(
        "stock.location", string="Source Location", required=True
    )
    destination_location_id = fields.Many2one(
        "stock.location", string="Destination Location", required=True
    )
    movement_date = fields.Datetime(
        string="Movement Date", required=True, default=fields.Datetime.now
    )
    responsible_user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_transit", "In Transit"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )
    notes = fields.Text(string="Movement Notes")

    @api.constrains("source_location_id", "destination_location_id")
    def _check_locations(self):
        for movement in self:
            if movement.source_location_id == movement.destination_location_id:
                raise ValidationError(
                    _("Source and destination locations cannot be the same.")
                )

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
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add auto-numbering"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('paper.bale.movement') or _('New')
        return super().create(vals_list)
    
    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection([], string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')
