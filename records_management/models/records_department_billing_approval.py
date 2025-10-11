# -*- coding: utf-8 -*-
from odoo import models, fields


class RecordsDepartmentBillingApproval(models.Model):
    _name = 'records.department.billing.approval'
    _description = 'Department Billing Approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'approval_date desc'

    billing_contact_id = fields.Many2one(
        comodel_name='records.department.billing.contact',
        string='Billing Contact',
        required=True,
        ondelete='cascade'
    )
    approval_date = fields.Datetime(string='Approval Date', default=fields.Datetime.now)
    charge_amount = fields.Monetary(string='Charge Amount', currency_field='currency_id')
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    service_description = fields.Char(string='Service Description')
    vendor = fields.Char(string='Vendor')
    approval_notes = fields.Text(string='Notes')

    # =========================================================================
    # DEFAULT VIEW FALLBACK (Test Support)
    # =========================================================================
    def _get_default_tree_view(self):  # Odoo core still asks for 'tree' in some test helpers
        """Provide a minimal fallback list (tree) view structure for automated tests.

        Odoo 19 uses <list/> arch tag, but internal test utilities may still request
        a default 'tree' view for x2many placeholders when no explicit list view is
        preloaded. Returning a valid list arch prevents UserError during base tests.
        """
        from lxml import etree
        arch = etree.fromstring(
            "<list string='Billing Approvals'>"
            "<field name='approval_date'/>"
            "<field name='charge_amount'/>"
            "<field name='service_description'/>"
            "<field name='vendor'/>"
            "</list>"
        )
        return arch
