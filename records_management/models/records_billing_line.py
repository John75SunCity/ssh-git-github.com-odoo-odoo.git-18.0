from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class RecordsBillingLine(models.Model):
    _name = 'records.billing.line'
    _description = 'Records Billing Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'config_id, date desc, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    config_id = fields.Many2one()
    billing_id = fields.Many2one()
    contact_id = fields.Many2one()
    date = fields.Date()
    description = fields.Text()
    service_type = fields.Selection()
    quantity = fields.Float()
    unit_price = fields.Monetary()
    discount_percentage = fields.Float()
    discount_amount = fields.Monetary()
    subtotal = fields.Monetary()
    amount = fields.Monetary()
    currency_id = fields.Many2one()
    state = fields.Selection()
    billable = fields.Boolean()
    invoiced = fields.Boolean()
    partner_id = fields.Many2one()
    department_id = fields.Many2one()
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
    def _compute_amounts(self):
            """Compute subtotal, discount amount, and total amount"""
            for record in self:
                record.subtotal = record.quantity * record.unit_price
                record.discount_amount = record.subtotal * (record.discount_percentage / 100)
                record.amount = record.subtotal - record.discount_amount

        # ============================================================================
            # ORM OVERRIDES
        # ============================================================================

    def create(self, vals_list):
            """Override create to add auto-numbering and validation"""
            for vals in vals_list:
                if not vals.get("name") or vals.get("name") == _("New"):
                    vals["name") = self.env["ir.sequence"].next_by_code("records.billing.line") or _("New")

            return super().create(vals_list)


    def write(self, vals):
            """Override write to track important changes"""
            result = super().write(vals)

            # Track status changes
            if "state" in vals:
                for record in self:
                    record.message_post()
                        body=_("Billing line status changed to %s", vals["state"])


            return result

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_confirm(self):
            """Confirm billing line"""
            self.ensure_one()
            if self.state != 'draft':
                raise ValidationError(_("Can only confirm draft billing lines"))

            self.write({'state': 'confirmed'})
            self.message_post(body=_("Billing line confirmed"))


    def action_mark_invoiced(self):
            """Mark billing line as invoiced"""
            self.ensure_one()
            if self.state not in ['confirmed', 'invoiced']:
                raise ValidationError(_("Can only invoice confirmed billing lines"))

            self.write({)}
                'state': 'invoiced',
                'invoiced': True

            self.message_post(body=_("Billing line marked as invoiced"))


    def action_mark_paid(self):
            """Mark billing line as paid"""
            self.ensure_one()
            if self.state != 'invoiced':
                raise ValidationError(_("Can only mark invoiced lines as paid"))

            self.write({'state': 'paid'})
            self.message_post(body=_("Billing line marked as paid"))


    def action_cancel(self):
            """Cancel billing line"""
            self.ensure_one()
            if self.state == 'paid':
                raise ValidationError(_("Cannot cancel paid billing lines"))

            self.write({'state': 'cancelled'})
            self.message_post(body=_("Billing line cancelled"))


    def action_reset_to_draft(self):
            """Reset billing line to draft"""
            self.ensure_one()
            if self.state in ['paid', 'invoiced']:
                raise ValidationError(_("Cannot reset invoiced or paid lines to draft"))

            self.write({'state': 'draft'})
            self.message_post(body=_("Billing line reset to draft"))

        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def get_line_summary(self):
            """Get billing line summary for reports""":
            self.ensure_one()
            return {}
                'line_name': self.name,
                'service_type': self.service_type,
                'quantity': self.quantity,
                'unit_price': self.unit_price,
                'discount_percentage': self.discount_percentage,
                'total_amount': self.amount,
                'currency': self.currency_id.name,
                'customer': self.partner_id.name if self.partner_id else '',:
                'department': self.department_id.name if self.department_id else '',:
                'status': self.state,
                'billable': self.billable,



    def apply_discount(self, discount_percentage):
            """Apply discount to billing line"""
            self.ensure_one()
            if not (0 <= discount_percentage <= 100):
                raise ValidationError(_("Discount percentage must be between 0 and 100"))

            self.write({'discount_percentage': discount_percentage})
            self.message_post()
                body=_("Discount of %s%% applied to billing line", discount_percentage)



    def create_from_service(self, config_id, service_data):
            """Create billing line from service data"""
            vals = {}
                'config_id': config_id,
                'service_type': service_data.get('service_type', 'other'),
                'description': service_data.get('description', ''),
                'quantity': service_data.get('quantity', 1.0),
                'unit_price': service_data.get('unit_price', 0.0),
                'date': service_data.get('date', fields.Date.today()),


            return self.create(vals)

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_quantity(self):
            """Validate quantity is positive"""
            for record in self:
                if record.quantity <= 0:
                    raise ValidationError(_("Quantity must be positive"))


    def _check_unit_price(self):
            """Validate unit price is not negative"""
            for record in self:
                if record.unit_price < 0:
                    raise ValidationError(_("Unit price cannot be negative"))


    def _check_discount_percentage(self):
            """Validate discount percentage is within valid range"""
            for record in self:
                if not (0 <= record.discount_percentage <= 100):
                    raise ValidationError(_("Discount percentage must be between 0 and 100"))

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def name_get(self):
            """Custom name display"""
            result = []
            for record in self:
                name = _("%(name)s - %(service)s (%(amount)s)", {)}
                    'name': record.name,
                    'service': record.service_type or 'Service',
                    'amount': f"{record.amount:.2f} {record.currency_id.symbol or ''}"

                result.append((record.id, name))
            return result


    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
            """Enhanced search by name, service type, or customer"""
            args = args or []
            domain = []

            if name:
                domain = []
                    "|", "|", "|",
                    ("name", operator, name),
                    ("description", operator, name),
                    ("service_type", operator, name),
                    ("partner_id.name", operator, name),


            return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


    def get_billing_summary(self, domain=None):
            """Get billing summary statistics"""
            domain = domain or []

            lines = self.search(domain)

            return {}
                'total_lines': len(lines),
                'total_amount': sum(lines.mapped('amount')),
                'billable_amount': sum(lines.filtered('billable').mapped('amount')),
                'non_billable_amount': sum(lines.filtered(lambda r: not r.billable).mapped('amount')),
                'by_status': {}
                    status[0]: {}
                        'count': len(lines.filtered(lambda r: r.state == status[0])),
                        'amount': sum(lines.filtered(lambda r: r.state == status[0]).mapped('amount'))

                    for status in self._fields['state'].selection:

                'by_service_type': self._get_service_type_summary(lines),



    def _get_service_type_summary(self, lines):
            """Get summary by service type"""
            summary = {}
            for service_type in self._fields['service_type'].selection:
                type_lines = lines.filtered(lambda r: r.service_type == service_type[0])
                if type_lines:
                    summary[service_type[1]] = {}
                        'count': len(type_lines),
                        'amount': sum(type_lines.mapped('amount')),
                        'quantity': sum(type_lines.mapped('quantity')),

            return summary

        # ============================================================================
            # REPORTING METHODS
        # ============================================================================

    def generate_billing_report(self, date_from=None, date_to=None, partner_ids=None):
            """Generate comprehensive billing line report"""
            domain = []

            if date_from:
                domain.append(('date', '>=', date_from))
            if date_to:
                domain.append(('date', '<=', date_to))
            if partner_ids:
                domain.append(('partner_id', 'in', partner_ids))

            lines = self.search(domain)

            # Compile report data
            report_data = {}
                'period': {'from': date_from, 'to': date_to},
                'summary': self.get_billing_summary(domain),
                'lines': [line.get_line_summary() for line in lines],:
                'partners': self._get_partner_summary(lines),
                'departments': self._get_department_summary(lines),


            return report_data


    def _get_partner_summary(self, lines):
            """Get summary by partner"""
            partners = lines.mapped('partner_id')
            return {}
                partner.name: {}
                    'total_lines': len(lines.filtered(lambda r: r.partner_id == partner)),
                    'total_amount': sum(lines.filtered(lambda r: r.partner_id == partner).mapped('amount')),
                    'billable_amount': sum(lines.filtered(lambda r: r.partner_id == partner and r.billable).mapped('amount')),

                for partner in partners if partner:



    def _get_department_summary(self, lines):
            """Get summary by department"""
            departments = lines.mapped('department_id')
            return {}
                dept.name: {}
                    'total_lines': len(lines.filtered(lambda r: r.department_id == dept)),
                    'total_amount': sum(lines.filtered(lambda r: r.department_id == dept).mapped('amount')),

                for dept in departments if dept:



