from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class PaperBaleInspection(models.Model):
    _name = 'paper.bale.inspection'
    _description = 'Paper Bale Inspection'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    active = fields.Boolean()
    company_id = fields.Many2one()
    state = fields.Selection()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    bale_id = fields.Many2one()
    inspection_date = fields.Datetime()
    inspector_id = fields.Many2one()
    inspection_type = fields.Selection()
    passed = fields.Boolean(string='Passed')
    notes = fields.Text(string='Inspection Notes')
    rejection_reason = fields.Text(string='Rejection Reason')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def create(self, vals_list):
            """Override create to add auto-numbering"""
            for vals in vals_list:
                if vals.get('name', _('New')) == _('New'):
                    vals['name'] = self.env['ir.sequence'].next_by_code('paper.bale.inspection') or _('New')
            return super().create(vals_list)


    def _check_rejection_reason(self):
            for inspection in self:
                if not inspection.passed and not inspection.rejection_reason:
                    raise ValidationError()
                        _("A rejection reason is required for failed inspections."):
                            pass



    def action_pass_inspection(self):
            self.ensure_one()
            self.write({"passed": True, "rejection_reason": ""})


    def action_fail_inspection(self, rejection_reason):
            self.ensure_one()
            if not rejection_reason:
                raise ValidationError(_("A rejection reason must be provided."))
            self.write({"passed": False, "rejection_reason": rejection_reason})
