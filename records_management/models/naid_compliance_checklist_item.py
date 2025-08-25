from odoo import models, fields, api, _


class NAIDComplianceChecklistItem(models.Model):
    _name = 'naid.compliance.checklist.item'
    _description = 'NAID Compliance Checklist Item'
    _order = 'sequence, id'

    # ============================================================================
    # FIELDS
    # ============================================================================
    checklist_id = fields.Many2one('naid.compliance.checklist', string='Checklist', required=True, ondelete='cascade')
    name = fields.Char(string='Item Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    is_checked = fields.Boolean(string='Checked')
    notes = fields.Text(string='Notes')
    is_required = fields.Boolean(string='Is Required', default=False)

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_mark_non_compliant(self):
        """Mark item as non-compliant"""
        pass

    def _check_deadline(self):
        """Validate deadline is not in the past for new items"""
        pass
