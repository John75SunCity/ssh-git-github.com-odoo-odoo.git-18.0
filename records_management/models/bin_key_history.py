# -*- coding: utf-8 -*-
from odoo import models, fields, api


class BinKeyHistory(models.Model):
    _name = "bin.key.history"
    _description = "Bin Key History"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Reference", required=True, default="New", tracking=True,,
    index=True),
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company,,
    required=True),
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user,,
    tracking=True),
    active = fields.Boolean(string="Active",,
    default=True)
    
    # ============================================================================
    # BUSINESS SPECIFIC FIELDS
    # ============================================================================
    partner_bin_key_id = fields.Many2one(
        "partner.bin.key", 
        string="Partner Bin Key", 
        required=True,
        tracking=True
    
    
    ,
    action_type = fields.Selection([))
        ("created", "Created"),
        ("assigned", "Assigned"),
        ("returned", "Returned"),
        ("lost", "Lost"),
        ("replaced", "Replaced"),
        ("deactivated", "Deactivated"),
    
    
    date = fields.Datetime(string="Date", default=fields.Datetime.now, required=True,,
    tracking=True),
    notes = fields.Text(string="Notes")
    
    # Location tracking
    location_id = fields.Many2one("records.location", string="Location",,
    tracking=True)
    
    # Partner relationship
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record"
    
    
    # Workflow state management
    ,
    state = fields.Selection([))
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    
        help='Current status of the record'
    
    # ============================================================================
    # ADDITIONAL TRACKING FIELDS
    # ============================================================================
    access_level_granted = fields.Char(string='Access Level Granted'),
    assigned_to = fields.Char(string='Assigned To'),
    assignment_date = fields.Date(string='Assignment Date'),
    assignment_location = fields.Char(string='Assignment Location'),
    assignment_reason = fields.Char(string='Assignment Reason'),
    authorization_reason = fields.Char(string='Authorization Reason'),
    authorized_by = fields.Char(string='Authorized By'),
    additional_notes = fields.Text(string='Additional Notes')
    
    # Deposit and return tracking
    deposit_amount = fields.Float(string='Deposit Amount',,
    digits=(12, 2))
    expected_return_date = fields.Date(string='Expected Return Date'),
    return_date = fields.Date(string='Return Date'),
    return_location = fields.Char(string='Return Location'),
    security_deposit_taken = fields.Boolean(string='Security Deposit Taken',,
    default=False)
    
    # Duration and timing
    duration_hours = fields.Float(string='Duration Hours',,
    digits=(8, 2))
    
    # Emergency and special handling
    emergency = fields.Boolean(string='Emergency',,
    default=False),
    witness_signature = fields.Char(string='Witness Signature')
    
    # Key reference
    key_id = fields.Many2one('bin.key',,
    string='Key')
    
    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id",,
    string="Activities"),
    message_follower_ids = fields.One2many("mail.followers", "res_id",,
    string="Followers"),
    message_ids = fields.One2many("mail.message", "res_id",,
    string="Messages")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name") = ()
                    self.env["ir.sequence"].next_by_code("bin.key.history") or "New"
                
        return super().create(vals_list)
    
    def action_activate(self):
        """Activate the history record"""
        self.ensure_one()
        self.write({'state': 'active'})
    
    def action_deactivate(self):
        """Deactivate the history record"""
        self.ensure_one()
        self.write({'state': 'inactive'})
    
    def action_archive(self):
        """Archive the history record"""
        self.ensure_one()
        self.write({'state': 'archived'})
