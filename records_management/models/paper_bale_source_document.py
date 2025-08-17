from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class PaperBaleSourceDocument(models.Model):
    _name = 'paper.bale.source.document'
    _description = 'Paper Bale Source Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'document_reference'
    _order = 'name, create_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    active = fields.Boolean()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    state = fields.Selection()
    bale_id = fields.Many2one()
    document_reference = fields.Char()
    document_type = fields.Char()
    customer_id = fields.Many2one()
    estimated_weight = fields.Float()
    confidentiality_level = fields.Selection()
    destruction_required = fields.Boolean()
    notes = fields.Text()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
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
                    vals['name') = self.env['ir.sequence'].next_by_code('paper.bale.source.document') or _('New')
            return super().create(vals_list)

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_confirm(self):
            """Confirm the source document"""
            self.write({'state': 'confirmed'})
            self.message_post(body=_("Source document confirmed"))


    def action_done(self):
            """Mark source document as done"""
            self.write({'state': 'done'})
            self.message_post(body=_("Source document processing completed"))


    def action_cancel(self):
            """Cancel the source document"""
            self.write({'state': 'cancelled'})
            self.message_post(body=_("Source document cancelled"))
