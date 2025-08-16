# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaperBaleInspection(models.Model):
    _name = "paper.bale.inspection"
    _description = "Paper Bale Inspection"
    _inherit = ["mail.thread", "mail.activity.mixin"]

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        index=True,
        ,
    default=lambda self: _('New'),
        help='Unique identifier for this record':
            pass
    
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Set to false to hide this record'
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        help='Company this record belongs to'
    
    ,
    state = fields.Selection([))
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    

        # ============================================================================
    # MAIL FRAMEWORK FIELDS (REQUIRED for mail.thread inheritance):
        # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        ,
    domain=lambda self: [("res_model", "=", self._name))
    
    
    message_follower_ids = fields.One2many(
        "mail.followers", 
        "res_id",
        string="Followers",
        ,
    domain=lambda self: [("res_model", "=", self._name))
    
    
    message_ids = fields.One2many(
        "mail.message",
        "res_id", 
        string="Messages",
        ,
    domain=lambda self: [("model", "=", self._name))
    
        # ============================================================================
    # ORM METHODS
        # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add auto-numbering"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('paper.bale.inspection') or _('New')
        return super().create(vals_list)

    bale_id = fields.Many2one(
        "paper.bale", string="Paper Bale", required=True, ondelete="cascade"
    
    inspection_date = fields.Datetime(
        string="Inspection Date", required=True, default=fields.Datetime.now
    
    inspector_id = fields.Many2one(
        "res.users", string="Inspector", default=lambda self: self.env.user
    
    ,
    inspection_type = fields.Selection(
        [)
            ("visual", "Visual"),
            ("contamination", "Contamination Check"),
            ("moisture", "Moisture Content"),
            ("full", "Full Inspection"),
        
        string="Inspection Type",
        required=True,
        default="visual",
    
    passed = fields.Boolean(string="Passed",,
    default=False),
    notes = fields.Text(string="Inspection Notes"),
    rejection_reason = fields.Text(string="Rejection Reason"),
    context = fields.Char(string='Context'),
    domain = fields.Char(string='Domain'),
    help = fields.Char(string='Help'),
    res_model = fields.Char(string='Res Model'),
    type = fields.Selection([), string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')

    @api.constrains("passed", "rejection_reason")
    def _check_rejection_reason(self):
        for inspection in self:
            if not inspection.passed and not inspection.rejection_reason:
                raise ValidationError()
                    _("A rejection reason is required for failed inspections."):
                

    def action_pass_inspection(self):
        self.ensure_one()
        self.write({"passed": True, "rejection_reason": ""})

    def action_fail_inspection(self, rejection_reason):
        self.ensure_one()
        if not rejection_reason:
            raise ValidationError(_("A rejection reason must be provided."))
        self.write({"passed": False, "rejection_reason": rejection_reason})
))))