# -*- coding: utf-8 -*-
import hashlib
from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Records Management Fields
    is_records_customer = fields.Boolean(
        string='Records Management Customer', default=False,
        help="Flag if this partner uses records/shredding services (NAID compliant tracking)."
    )
    x_department_ids = fields.One2many(
        'records.department', 'partner_id',
        string='Departments',
        help='Departments for access control and billing (fixes domain errors in security rules).'
    )
    document_ids = fields.One2many('records.document', 'partner_id', string='Related Documents')  # Now valid with inverse in records.document
    document_count = fields.Integer(compute='_compute_document_count', store=True)

    # Billing Preferences (Streamlined for multi-department)
    billing_method = fields.Selection([
        ('consolidated', 'Consolidated - One Invoice with Department Breakdown'),
        ('separate', 'Separate - Individual Invoices per Department'),
        ('hybrid', 'Hybrid - Consolidated Storage, Separate Services')
    ], string='Billing Method', default='consolidated',
       help="Billing for multi-department customers (inspired by suncityshred per-box transparency)."
    )
    billing_contact_id = fields.Many2one(
        'res.partner', string='Primary Billing Contact',
        domain="[('parent_id', '=', id), ('type', '=', 'contact')]",
        help="Main contact for invoices (ISO 27001 access control)."
    )
    invoice_delivery_method = fields.Selection([
        ('email', 'Email'), ('portal', 'Portal'), ('mail', 'Postal Mail'), ('both', 'Email + Portal')
    ], string='Invoice Delivery', default='both', help="Per NAID audit requirements."
    )
    payment_terms_override = fields.Many2one('account.payment.term', string='Payment Terms Override')
    minimum_fee_per_department = fields.Boolean(
        string='Apply Minimum Fee Per Department', default=False,
        help="Apply fees separately (no hidden costs, per suncityshred)."
    )

    # Department Billing Contacts (Merged for simplicity)
    department_billing_contact_ids = fields.One2many(
        'records.department.billing.contact', 'partner_id',
        string='Department Billing Contacts',
        help="Contacts per department (used in separate/hybrid billing)."
    )

    # Computed Stats for Dashboard (Modern UI)
    total_departments = fields.Integer(compute='_compute_department_stats', store=True)
    departments_with_storage = fields.Integer(compute='_compute_department_stats', store=True)
    monthly_storage_total = fields.Float(compute='_compute_department_stats', store=True)
    hashed_storage_hash = fields.Char(compute='_compute_department_stats', store=True, help='Hashed storage total for ISO 27001 secure auditing.')

    @api.depends('x_department_ids', 'x_department_ids.box_ids')
    def _compute_department_stats(self):
        for partner in self:
            depts = partner.x_department_ids
            partner.total_departments = len(depts)
            depts_with_storage = depts.filtered(lambda d: d.box_ids)
            partner.departments_with_storage = len(depts_with_storage)
            total = sum(d.monthly_cost for d in depts_with_storage)  # Assume monthly_cost in department
            partner.monthly_storage_total = total
            # ISO-compliant hashing for integrity (no PII exposure in reports)
            partner.hashed_storage_hash = hashlib.sha256(str(total).encode()).hexdigest() if total else False

    @api.depends('document_ids')
    def _compute_document_count(self):
        for partner in self:
            partner.document_count = len(partner.document_ids)

    def action_view_documents(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Related Documents'),
            'view_mode': 'kanban,tree,form',
            'res_model': 'records.document',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def action_view_departments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Departments'),
            'view_mode': 'tree,form,kanban',
            'res_model': 'records.department',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def action_view_requests(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Related Requests'),
            'view_mode': 'kanban,tree,form',
            'res_model': 'portal.request',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

class RecordsDepartmentBillingContact(models.Model):
    _name = 'records.department.billing.contact'
    _description = 'Department Billing Contact'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True, index=True)
    department_id = fields.Many2one('records.department', string='Department', required=True)
    contact_id = fields.Many2one('res.partner', string='Contact', required=True, domain="[('parent_id', '=', partner_id)]")
    receives_invoices = fields.Boolean(default=True)
    receives_statements = fields.Boolean(default=False)
    receives_notifications = fields.Boolean(default=True)
    delivery_method = fields.Selection([
        ('email', 'Email'), ('portal', 'Portal'), ('mail', 'Postal Mail')
    ], default='email')
    active = fields.Boolean(default=True)
