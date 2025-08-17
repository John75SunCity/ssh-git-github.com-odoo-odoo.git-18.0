from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsInstaller(models.Model):
    _name = 'records.installer'
    _description = 'Records Installer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    state = fields.Selection()
    notes = fields.Text(string='Notes')
    installer_display_name = fields.Char()
    partner_id = fields.Many2one()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_installer_display_name(self):
            for record in self:
                record.installer_display_name = record.name or _("New")


    def action_confirm(self):
            """Set the record's state to 'confirmed'."""'

            self.ensure_one()
            self.write({"state": "confirmed"})


    def action_cancel(self):
            """Set the record's state to 'cancelled'."""'

            self.ensure_one()
            self.write({"state": "cancelled"})


    def action_reset_to_draft(self):
            """Reset the record's state to 'draft'."""'

            self.ensure_one()
            self.write({"state": "draft"})
