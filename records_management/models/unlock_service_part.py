from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class UnlockServicePart(models.Model):
    _name = 'unlock.service.part'
    _description = 'Unlock Service Part Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'service_history_id, sequence, product_id'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    display_name = fields.Char()
    sequence = fields.Integer()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    service_history_id = fields.Many2one()
    partner_id = fields.Many2one()
    technician_id = fields.Many2one()
    product_id = fields.Many2one()
    name = fields.Char()
    product_code = fields.Char()
    product_category_id = fields.Many2one()
    uom_id = fields.Many2one()
    quantity_planned = fields.Float()
    quantity_used = fields.Float()
    quantity = fields.Float()
    quantity_available = fields.Float()
    quantity_reserved = fields.Float()
    unit_cost = fields.Float()
    unit_price = fields.Float()
    markup_percentage = fields.Float()
    service_price = fields.Monetary()
    total_cost = fields.Monetary()
    total_price = fields.Monetary()
    currency_id = fields.Many2one()
    state = fields.Selection()
    is_critical = fields.Boolean()
    is_warranty_covered = fields.Boolean()
    warranty_date = fields.Date()
    vendor_id = fields.Many2one()
    procurement_date = fields.Date()
    batch_number = fields.Char()
    expiry_date = fields.Date()
    usage_notes = fields.Text()
    replacement_reason = fields.Text()
    quality_notes = fields.Text()
    internal_notes = fields.Text()
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
    def _compute_display_name(self):
            """Compute display name for the part record""":
            for record in self:
                if record.product_id and record.service_history_id:
                    record.display_name = _("%s - %s (Qty: %s)",
                                            record.service_history_id.name,
                                            record.product_id.name,
                                            record.quantity or record.quantity_planned
                elif record.product_id:
                    record.display_name = record.product_id.name
                else:
                    record.display_name = _("New Service Part")


    def _compute_quantity(self):
            """Compute final quantity based on actual or planned"""
            for record in self:
                record.quantity = record.quantity_used or record.quantity_planned


    def _compute_service_price(self):
            """Compute service price with markup"""
            for record in self:
                if record.unit_price and record.markup_percentage:
                    record.service_price = record.unit_price * (1 + record.markup_percentage / 100)
                else:
                    record.service_price = record.unit_price


    def _compute_total_amounts(self):
            """Compute total cost and price amounts"""
            for record in self:
                record.total_cost = record.quantity * record.unit_cost
                record.total_price = record.quantity * record.service_price

        # ============================================================================
            # ONCHANGE METHODS
        # ============================================================================


    def _onchange_product_id(self):
            """Update related fields when product changes"""
            if self.product_id:
                # Check stock availability
                if self.product_id.qty_available <= 0:
                    return {}
                        'warning': {}
                            'title': _('Stock Warning'),
                            'message': _('Product %s is out of stock. Available: %s') % ()
                                self.product_id.name, self.product_id.qty_available





    def _onchange_quantity_planned(self):
            """Validate planned quantity against stock"""
            if self.quantity_planned and self.product_id:
                if self.quantity_planned > self.product_id.qty_available:
                    return {}
                        'warning': {}
                            'title': _('Insufficient Stock'),
                            'message': _('Planned quantity %s exceeds available stock %s for %s') % (:)
                                self.quantity_planned, self.product_id.qty_available, self.product_id.name




        # ============================================================================
            # CONSTRAINT METHODS
        # ============================================================================


    def _check_quantities(self):
            """Validate quantity values"""
            for record in self:
                if record.quantity_planned < 0:
                    raise ValidationError(_("Planned quantity cannot be negative"))

                if record.quantity_used < 0:
                    raise ValidationError(_("Used quantity cannot be negative"))

                if record.quantity_used and record.quantity_used > record.quantity_planned:
                    raise ValidationError(_())
                        "Used quantity (%s) cannot exceed planned quantity (%s) for %s":
                    ) % (record.quantity_used, record.quantity_planned, record.product_id.name


    def _check_markup_percentage(self):
            """Validate markup percentage"""
            for record in self:
                if record.markup_percentage < 0:
                    raise ValidationError(_("Markup percentage cannot be negative"))

                if record.markup_percentage > 1000:
                    raise ValidationError(_("Markup percentage cannot exceed 1000%"))


    def _check_dates(self):
            """Validate date fields"""
            for record in self:
                if record.expiry_date and record.expiry_date < fields.Date.today():
                    raise ValidationError(_("Expiry date cannot be in the past"))

                if record.warranty_date and record.warranty_date < fields.Date.today():
                    # Warning only, don't prevent saving'
                    record.message_post()
                        body=_("Warning: Warranty date is in the past for %s") % record.product_id.name,:
                        message_type='comment'


        # ============================================================================
            # ACTION METHODS
        # ============================================================================


    def action_reserve_stock(self):
            """Reserve stock for this service part""":
            self.ensure_one()

            if self.state != 'planned':
                raise UserError(_("Can only reserve stock for planned parts")):
            if self.quantity_planned > self.product_id.qty_available:
                raise UserError(_())
                    "Cannot reserve %s units of %s. Only %s available."
                ) % (self.quantity_planned, self.product_id.name, self.product_id.qty_available

            self.write({)}
                'state': 'reserved',
                'quantity_reserved': self.quantity_planned


            self._create_audit_log('stock_reserved')

            return True


    def action_mark_used(self):
            """Mark part as used in service"""
            self.ensure_one()

            if self.state not in ['planned', 'reserved']:
                raise UserError(_("Part must be planned or reserved to mark as used"))

            # Open wizard to enter actual quantity used
            return {}
                'type': 'ir.actions.act_window',
                'name': _('Mark Part as Used'),
                'res_model': 'unlock.service.part.usage.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {}
                    'default_part_id': self.id,
                    'default_quantity_used': self.quantity_planned




    def action_return_unused(self):
            """Return unused parts to stock"""
            self.ensure_one()

            if self.state != 'reserved':
                raise UserError(_("Can only return reserved parts"))

            unused_quantity = self.quantity_reserved - (self.quantity_used or 0)

            if unused_quantity > 0:
                self.write({)}
                    'state': 'returned',
                    'quantity_reserved': self.quantity_used or 0


                self._create_audit_log('stock_returned', {)}
                    'returned_quantity': unused_quantity


                self.message_post()
                    body=_("Returned %s units of %s to stock") % ()
                        unused_quantity, self.product_id.name



            return True


    def action_cancel_part(self):
            """Cancel this service part"""
            self.ensure_one()

            if self.state == 'used':
                raise UserError(_("Cannot cancel parts that have been used"))

            self.write({'state': 'cancelled'})
            self._create_audit_log('part_cancelled')

            return True

        # ============================================================================
            # BUSINESS LOGIC METHODS
        # ============================================================================


    def _create_audit_log(self, event_type, additional_data=None):
            """Create audit log entry"""
            audit_data = {}
                'event_type': event_type,
                'model_name': self._name,
                'record_id': self.id,
                'user_id': self.env.user.id,
                'company_id': self.company_id.id,
                'description': _('Service part %s: %s') % (self.product_id.name, event_type),
                'additional_data': additional_data or {}


            # Add to related service history audit
            if self.service_history_id:
                audit_data['related_service_id'] = self.service_history_id.id

            return self.env['unlock.service.audit'].create(audit_data)


    def _calculate_total_service_cost(self):
            """Calculate total cost for billing integration""":
            return self.total_price


    def _check_warranty_status(self):
            """Check if part is still under warranty""":
            if self.warranty_date:

    def _get_replacement_recommendations(self):
            """Get recommended replacement parts"""
            # Business logic to suggest alternative parts
            domain = []
                ('categ_id', '=', self.product_category_id.id),
                ('id', '!=', self.product_id.id),
                ('active', '=', True)

            return self.env['product.product'].search(domain, limit=5)

        # ============================================================================
            # INTEGRATION METHODS
        # ============================================================================


    def create_from_service_template(self, service_history_id, template_parts):
            """Create parts from service template"""
            parts = []
            for template_part in template_parts:
                part_vals = {}
                    'service_history_id': service_history_id,
                    'product_id': template_part['product_id'],
                    'quantity_planned': template_part.get('quantity', 1.0),
                    'markup_percentage': template_part.get('markup', 20.0),
                    'is_critical': template_part.get('is_critical', False)

                parts.append(self.create(part_vals))
            return parts


    def export_to_billing(self):
            """Export part costs to billing system"""
            billing_data = {}
                'service_id': self.service_history_id.id,
                'product_id': self.product_id.id,
                'quantity': self.quantity,
                'unit_price': self.service_price,
                'total_amount': self.total_price,
                'description': _('Service part: %s') % self.product_id.name

            return billing_data

        # ============================================================================
            # REPORTING METHODS
        # ============================================================================


    def get_usage_analytics(self, date_from=None, date_to=None):
            """Get parts usage analytics"""
            domain = [('state', '=', 'used')]

            if date_from:
                domain.append(('create_date', '>=', date_from))
            if date_to:
                domain.append(('create_date', '<=', date_to))

            used_parts = self.search(domain)

            analytics = {}
                'total_parts_used': len(used_parts),
                'total_cost': sum(used_parts.mapped('total_cost')),
                'total_revenue': sum(used_parts.mapped('total_price')),
                'most_used_products': self._get_most_used_products(used_parts),
                'cost_by_category': self._get_cost_by_category(used_parts)


            return analytics


    def _get_most_used_products(self, parts):
            """Get most frequently used products"""
            product_usage = {}
            for part in parts:
                if part.product_id.id in product_usage:
                    product_usage[part.product_id.id]['quantity'] += part.quantity
                    product_usage[part.product_id.id]['count'] += 1
                else:
                    product_usage[part.product_id.id] = {}
                        'product': part.product_id.name,
                        'quantity': part.quantity,
                        'count': 1


            return sorted(product_usage.values(), key=lambda x: x['quantity'], reverse=True)[:10]


    def _get_cost_by_category(self, parts):
            """Get cost breakdown by product category"""
            category_costs = {}
            for part in parts:
                category = part.product_category_id.name or 'Uncategorized'
                if category in category_costs:
                    category_costs[category] += part.total_cost
                else:
                    category_costs[category] = part.total_cost

            return category_costs
