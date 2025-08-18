# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PaperBaleInspection(models.Model):
    """
    Represents a single inspection event for a paper bale. This model stores
    the results of checks for moisture, contamination, grade, etc., creating a
    quality control history for each bale.
    """
    _name = 'paper.bale.inspection'
    _description = 'Paper Bale Inspection'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'inspection_date desc, name desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(
        string="Inspection Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    bale_id = fields.Many2one(
        'paper.bale',
        string='Paper Bale',
        required=True,
        ondelete='cascade',
        index=True
    )
    inspection_date = fields.Datetime(
        string='Inspection Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    inspector_id = fields.Many2one(
        'res.users',
        string='Inspected By',
        required=True,
        default=lambda self: self.env.user,
        tracking=True
    )
    inspection_type = fields.Selection([
        ('moisture', 'Moisture Content'),
        ('contamination', 'Contamination Check'),
        ('grade', 'Grade Verification'),
        ('visual', 'Visual Inspection'),
        ('other', 'Other'),
    ], string="Inspection Type", required=True, tracking=True)

    passed = fields.Boolean(string='Passed', tracking=True)
    rejection_reason = fields.Text(string='Rejection Reason', tracking=True)
    notes = fields.Text(string='Inspection Notes')

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    active = fields.Boolean(default=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides the create method to assign a unique sequential name to each
        new inspection record upon creation.
        """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('paper.bale.inspection') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================

    @api.constrains('passed', 'rejection_reason')
    def _check_rejection_reason(self):
        """
        Ensures that a rejection reason is provided if and only if the
        inspection has failed.
        """
        for inspection in self:
            if not inspection.passed and not inspection.rejection_reason:
                raise ValidationError(_("A rejection reason is required for failed inspections."))
            if inspection.passed and inspection.rejection_reason:
                raise ValidationError(_("A rejection reason should not be set for passed inspections."))

