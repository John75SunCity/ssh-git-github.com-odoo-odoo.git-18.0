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
    document_ids = fields.One2many('records.document', 'partner_id', string='Related Documents')
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
    total_departments =