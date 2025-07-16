from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Existing fields
    document_ids = fields.One2many(
        'records.document', 'partner_id', string='Related Documents')
    document_count = fields.Integer(compute='_compute_document_count')

    # Records Management Customer Fields
    is_records_customer = fields.Boolean(
        string='Records Management Customer', default=False,
        help="Check if this partner is a records management customer")
    
    # Departmental Billing Preferences
    billing_method = fields.Selection([
        ('consolidated', 'Consolidated Billing - One Invoice with Department Breakdown'),
        ('separate', 'Separate Department Billing - Individual Invoices per Department'),
        ('hybrid', 'Hybrid - Consolidated Storage, Separate Services')
    ], string='Billing Method', default='consolidated',
       help="How to handle billing when customer has multiple departments")
    
    billing_contact_id = fields.Many2one(
        'res.partner', string='Primary Billing Contact',
        domain="[('parent_id', '=', id), ('is_company', '=', False)]",
        help="Primary contact for billing and invoices")
    
    department_billing_contacts = fields.One2many(
        'records.department.billing.contact', 'customer_id',
        string='Department Billing Contacts')
    
    # Billing Preferences
    invoice_delivery_method = fields.Selection([
        ('email', 'Email'),
        ('portal', 'Customer Portal'),
        ('mail', 'Postal Mail'),
        ('both', 'Email + Portal')
    ], string='Invoice Delivery', default='email')
    
    payment_terms_override = fields.Many2one(
        'account.payment.term', string='Payment Terms Override',
        help="Override default payment terms for this customer")
    
    # Customer billing preferences for multi-department companies
    billing_preference = fields.Selection([
        ('consolidated', 'Consolidated - One invoice with '
         'department breakdown'),
        ('separate', 'Separate - Individual invoices per department'),
        ('hybrid', 'Hybrid - Consolidated storage, separate services'),
    ], string='Billing Preference', default='consolidated',
       help="Choose how invoices should be generated for companies with "
            "multiple departments")
    
    minimum_fee_per_department = fields.Boolean(
        string='Apply Minimum Fee Per Department',
        default=False,
        help="If checked, monthly minimum fee applies to each department "
             "separately. Otherwise, minimum applies to total company usage "
             "and is distributed proportionally."
    )
    
    # Department Statistics
    total_departments = fields.Integer(
        string='Total Departments', compute='_compute_department_stats')
    departments_with_storage = fields.Integer(
        string='Departments with Storage', compute='_compute_department_stats')
    monthly_storage_total = fields.Float(
        string='Monthly Storage Total', compute='_compute_department_stats')
    
    # Department billing contacts
    department_billing_contact_ids = fields.One2many(
        'res.partner.department.billing',
        'partner_id',
        string='Department Billing Contact Assignments',
        help="Specific billing contacts for departments "
             "(used with separate billing)"
    )

    @api.depends('child_ids')
    def _compute_department_stats(self):
        for partner in self:
            if partner.is_company:
                departments = self.env['records.department'].search([
                    ('company_id', '=', partner.id)
                ])
                partner.total_departments = len(departments)
                
                # Count departments with active storage
                depts_with_storage = departments.filtered(
                    lambda d: d.total_boxes > 0)
                partner.departments_with_storage = len(depts_with_storage)
                
                # Calculate total monthly storage cost
                partner.monthly_storage_total = sum(depts_with_storage.mapped('monthly_cost'))
            else:
                partner.total_departments = 0
                partner.departments_with_storage = 0
                partner.monthly_storage_total = 0.0

    def _compute_document_count(self):
        for partner in self:
            partner.document_count = len(partner.document_ids)

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': 'Related Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }


class RecordsDepartmentBillingContact(models.Model):
    _name = 'records.department.billing.contact'
    _description = 'Department-Specific Billing Contacts'
    _rec_name = 'contact_id'

    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True, ondelete='cascade')
    department_id = fields.Many2one(
        'records.department', string='Department', required=True)
    contact_id = fields.Many2one(
        'res.partner', string='Billing Contact', required=True,
        domain="[('parent_id', '=', customer_id), ('is_company', '=', False)]")
    
    # Contact preferences
    receives_invoices = fields.Boolean(string='Receives Invoices', default=True)
    receives_statements = fields.Boolean(string='Receives Statements', default=False)
    receives_notifications = fields.Boolean(string='Receives Notifications', default=True)
    
    # Delivery preferences
    delivery_method = fields.Selection([
        ('email', 'Email'),
        ('portal', 'Customer Portal'),
        ('mail', 'Postal Mail')
    ], string='Delivery Method', default='email')
    
    active = fields.Boolean(string='Active', default=True)


class ResPartnerDepartmentBilling(models.Model):
    _name = 'res.partner.department.billing'
    _description = 'Department Billing Contact'
    _rec_name = 'department_name'

    partner_id = fields.Many2one(
        'res.partner', string='Company', required=True, ondelete='cascade')
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        required=True,
        domain="[('company_id', '=', partner_id)]"
    )
    department_name = fields.Char(
        related='department_id.name', string='Department Name', readonly=True)
    billing_contact_id = fields.Many2one(
        'res.partner',
        string='Billing Contact',
        required=True,
        domain="[('is_company', '=', False)]",
        help="Person who should receive invoices for this department"
    )
    billing_email = fields.Char(
        related='billing_contact_id.email', string='Billing Email',
        readonly=True)
    use_separate_po_numbers = fields.Boolean(
        string='Use Separate PO Numbers',
        default=False,
        help="If checked, this department uses separate purchase order "
             "numbers"
    )
    default_po_number = fields.Char(
        string='Default PO Number',
        help="Default purchase order number for this department's invoices"
    )
