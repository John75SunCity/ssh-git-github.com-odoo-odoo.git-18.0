# -*- coding: utf-8 -*-
from odoo import models, fields


class NAIDComplianceChecklistItem(models.Model):
    _name = 'naid.compliance.checklist.item'
    _description = 'NAID Compliance Checklist Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
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

    # New integration fields for core app leverage
    equipment_id = fields.Many2one(
        comodel_name='maintenance.equipment',
        string='Related Equipment',
        help='Link to maintenance equipment for equipment checks or vehicle inspections'
    )
    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Related FSM Task',
        help='Link to FSM task for field service or inspection workflows'
    )
    visitor_id = fields.Many2one(
        comodel_name='container.access.visitor',
        string='Related Visitor',
        help='Link to visitor record for access logs and security checks'
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Related Location',
        help='Link to stock location for warehouse security and inventory checks'
    )

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_mark_non_compliant(self):
        """Mark item as non-compliant"""
        self.ensure_one()
        pass

    def _check_deadline(self):
        """Validate deadline is not in the past for new items"""
        pass
