from odoo import models, fields, api

class ResPartnerDepartmentBilling(models.Model):
    _name = 'res.partner.department.billing'
    _description = 'Department Billing for Partners'

    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True
    )

    monthly_storage_fee = fields.Float(
        string='Monthly Storage Fee',
        compute='_compute_billing_totals',
        store=True
    )

    # Add other fields as needed
    # billing_date = fields.Date(string='Billing Date')
    # amount_due = fields.Float(string='Amount Due')

    @api.depends('customer_id')
    def _compute_billing_totals(self):
        for record in self:
            # Replace with your actual logic for computing monthly storage fee
            if record.customer_id:
                record.monthly_storage_fee = 100.0  # Example fixed value
            else:
                record.monthly_storage_fee = 0.0
