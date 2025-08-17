from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # ============================================================================
    # FIELDS
    # ============================================================================
    work_order_id = fields.Reference()
    work_order_coordinator_id = fields.Many2one()
    work_order_reference = fields.Char()
    work_order_date = fields.Date()
    records_related = fields.Boolean()
    records_service_type = fields.Selection()
    service_category = fields.Selection()
    container_count = fields.Integer()
    container_ids = fields.Many2many()
    container_types = fields.Char()
    document_count = fields.Integer()
    file_count = fields.Integer()
    destruction_service_id = fields.Many2one()
    shredding_weight_lbs = fields.Float()
    shredding_weight_kg = fields.Float()
    destruction_method = fields.Selection()
    certificate_of_destruction_id = fields.Many2one()
    pickup_request_id = fields.Many2one()
    pickup_date = fields.Date()
    delivery_date = fields.Date()
    route_id = fields.Many2one()
    driver_id = fields.Many2one()
    vehicle_id = fields.Many2one()
    storage_location_id = fields.Many2one()
    origin_location_id = fields.Many2one()
    destination_location_id = fields.Many2one()
    storage_period_months = fields.Integer()
    storage_start_date = fields.Date()
    storage_end_date = fields.Date()
    billing_config_id = fields.Many2one()
    base_rate_id = fields.Many2one()
    customer_rate_id = fields.Many2one()
    rate_type = fields.Selection()
    unit_rate = fields.Float()
    rate_unit = fields.Selection()
    naid_audit_required = fields.Boolean()
    naid_compliant = fields.Boolean()
    audit_trail_created = fields.Boolean()
    compliance_notes = fields.Text()
    chain_of_custody_id = fields.Many2one()
    records_department_id = fields.Many2one()
    customer_contact_id = fields.Many2one()
    customer_reference = fields.Char()
    portal_request_id = fields.Many2one()
    service_duration_hours = fields.Float()
    travel_time_hours = fields.Float()
    service_efficiency_score = fields.Float()
    customer_satisfaction_rating = fields.Selection()
    service_notes = fields.Text()
    internal_notes = fields.Text()
    special_instructions = fields.Text()
    inherit_id = fields.Many2one()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_container_types(self):
            """Compute string representation of container types"""
            for line in self:
                if line.container_ids:
                    types = line.container_ids.mapped('container_type')
                    unique_types = list(set(types))
                    line.container_types = ', '.join(unique_types) if unique_types else '':
                else:
                    line.container_types = ''


    def _compute_weight_kg(self):
            """Convert weight from lbs to kg"""
            for line in self:
                if line.shredding_weight_lbs:
                    line.shredding_weight_kg = line.shredding_weight_lbs * 0.453592
                else:
                    line.shredding_weight_kg = 0.0

        # ============================================================================
            # ONCHANGE METHODS
        # ============================================================================

    def _onchange_work_order_id(self):
            """Update related fields when work order changes"""
            if self.work_order_id:
                work_order = self.work_order_id

                # Set basic information
                self.records_related = True
                self.work_order_reference = work_order.name if hasattr(work_order, 'name') else '':
                self.work_order_date = work_order.create_date.date() if hasattr(work_order, 'create_date') else False:
                # Set service type based on work order type
                if 'retrieval' in self.work_order_id._name:
                    self.records_service_type = 'retrieval'
                elif 'destruction' in self.work_order_id._name:
                    self.records_service_type = 'destruction'
                elif 'pickup' in self.work_order_id._name:
                    self.records_service_type = 'pickup'

                # Set partner information
                if hasattr(work_order, 'partner_id') and work_order.partner_id:
                    self.partner_id = work_order.partner_id


    def _onchange_records_service_type(self):
            """Update fields based on service type"""
            if self.records_service_type:
                self.records_related = True

                # Set default NAID audit requirement for certain services:
                if self.records_service_type in ['destruction', 'retrieval']:
                    self.naid_audit_required = True


    def _onchange_destruction_service_id(self):
            """Update fields when destruction service changes"""
            if self.destruction_service_id:
                service = self.destruction_service_id
                self.records_service_type = 'destruction'
                self.shredding_weight_lbs = service.total_weight if hasattr(service, 'total_weight') else 0.0:
                self.destruction_method = service.destruction_method if hasattr(service, 'destruction_method') else False:
                self.naid_audit_required = True


    def _onchange_pickup_request_id(self):
            """Update fields when pickup request changes"""
            if self.pickup_request_id:
                pickup = self.pickup_request_id
                self.records_service_type = 'pickup'
                self.pickup_date = pickup.pickup_date if hasattr(pickup, 'pickup_date') else False:
                self.container_count = len(pickup.container_ids) if hasattr(pickup, 'container_ids') else 0:
        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_create_audit_trail(self):
            """Create NAID audit trail for this invoice line""":
            self.ensure_one()

            if not self.records_related:
                raise UserError(_("Cannot create audit trail for non-records related invoice lines")):
            if self.audit_trail_created:
                raise UserError(_("Audit trail already exists for this invoice line")):
            # Create audit log entry
            audit_vals = {
                'action_type': 'invoice_line_created',
                'user_id': self.env.user.id,
                'timestamp': fields.Datetime.now(),
                'description': _("Invoice line created for %s") % (self.records_service_type,),:
                'invoice_line_id': self.id,
                'amount': self.price_total,
                'naid_compliant': self.naid_compliant,
            }

            if 'naid.audit.log' in self.env:
                self.env['naid.audit.log'].create(audit_vals)

            self.audit_trail_created = True
            self.message_post(body=_("NAID audit trail created for invoice line")):

    def action_view_work_order(self):
            """View the related work order"""
            self.ensure_one()

            if not self.work_order_id:
                raise UserError(_("No work order linked to this invoice line"))

            return {
                'type': 'ir.actions.act_window',
                'name': _('Related Work Order'),
                'res_model': self.work_order_id._name,
                'res_id': self.work_order_id.id,
                'view_mode': 'form',
                'target': 'current',
            }


    def action_view_containers(self):
            """View related containers"""
            self.ensure_one()

            if not self.container_ids:
                raise UserError(_("No containers linked to this invoice line"))

            return {
                'type': 'ir.actions.act_window',
                'name': _('Related Containers'),
                'res_model': 'records.container',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', self.container_ids.ids)],
                'context': {'default_partner_id': self.partner_id.id if self.partner_id else False},:
            }


    def action_view_destruction_certificate(self):
            """View destruction certificate"""
            self.ensure_one()

            if not self.certificate_of_destruction_id:
                raise UserError(_("No destruction certificate available"))

            return {
                'type': 'ir.actions.act_window',
                'name': _('Certificate of Destruction'),
                'res_model': 'naid.certificate',
                'res_id': self.certificate_of_destruction_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_shredding_weight(self):
            """Validate shredding weight"""
            for line in self:
                if line.shredding_weight_lbs and line.shredding_weight_lbs < 0:
                    raise ValidationError(_("Shredding weight cannot be negative"))


    def _check_container_count(self):
            """Validate container count"""
            for line in self:
                if line.container_count and line.container_count < 0:
                    raise ValidationError(_("Container count cannot be negative"))


    def _check_storage_dates(self):
            """Validate storage date sequence"""
            for line in self:
                if (line.storage_start_date and line.storage_end_date and:
                    line.storage_start_date > line.storage_end_date):
                    raise ValidationError(_(
                        "Storage start date cannot be after storage end date"
                    ))


    def _check_pickup_delivery_dates(self):
            """Validate pickup and delivery date sequence"""
            for line in self:
                if (line.pickup_date and line.delivery_date and:
                    line.pickup_date > line.delivery_date):
                    raise ValidationError(_(
                        "Pickup date cannot be after delivery date"
                    ))

        # ============================================================================
            # BUSINESS LOGIC METHODS
        # ============================================================================

    def get_service_summary(self):
            """Get summary information for this service line""":
            self.ensure_one()

            return {
                'service_type': self.records_service_type,
                'service_category': self.service_category,
                'container_count': self.container_count,
                'document_count': self.document_count,
                'weight_processed': self.shredding_weight_lbs,
                'duration_hours': self.service_duration_hours,
                'naid_compliant': self.naid_compliant,
                'audit_trail_created': self.audit_trail_created,
                'customer_satisfaction': self.customer_satisfaction_rating,
            }


    def calculate_efficiency_metrics(self):
            """Calculate service efficiency metrics"""
            self.ensure_one()

            efficiency_score = 100.0  # Base score

            # Adjust based on service duration vs standard
            if self.service_duration_hours and self.container_count:
                standard_time_per_container = 0.5  # 30 minutes per container
                expected_time = self.container_count * standard_time_per_container

                if self.service_duration_hours > expected_time:
                    # Took longer than expected
                    efficiency_score -= ((self.service_duration_hours - expected_time) / expected_time) * 20
                else:
                    # Faster than expected
                    efficiency_score += ((expected_time - self.service_duration_hours) / expected_time) * 10

            # Adjust based on customer satisfaction
            if self.customer_satisfaction_rating:
                rating = int(self.customer_satisfaction_rating)
                efficiency_score += (rating - 3) * 5  # +/-10 points for excellent/poor:
            return max(0.0, min(100.0, efficiency_score))


    def get_records_billing_summary(self, date_from=None, date_to=None):
            """Get billing summary for records management services""":
            domain = [('records_related', '=', True)]

            if date_from:
                domain.append(('move_id.invoice_date', '>=', date_from))
            if date_to:
                domain.append(('move_id.invoice_date', '<=', date_to))

            lines = self.search(domain)

            summary = {
                'total_revenue': sum(lines.mapped('price_total')),
                'total_containers': sum(lines.mapped('container_count')),
                'total_weight_shredded': sum(lines.mapped('shredding_weight_lbs')),
                'service_breakdown': {},
                'compliance_stats': {
                    'naid_compliant_lines': len(lines.filtered('naid_compliant')),
                    'audit_trails_created': len(lines.filtered('audit_trail_created')),
                }
            }

            # Service type breakdown
            for service_type in lines.mapped('records_service_type'):
                if service_type:
                    service_lines = lines.filtered(lambda l: l.records_service_type == service_type)
                    summary['service_breakdown'][service_type] = {
                        'line_count': len(service_lines),
                        'revenue': sum(service_lines.mapped('price_total')),
                        'container_count': sum(service_lines.mapped('container_count')),
                    }

            return summary

        # ============================================================================
            # ORM METHODS
        # ============================================================================

    def create(self, vals_list):
            """Override create to set records management defaults"""
            for vals in vals_list:
                # Auto-detect records management services
                if (vals.get('work_order_id') or:
                    vals.get('pickup_request_id') or
                    vals.get('destruction_service_id')):
                    vals['records_related'] = True

                    # Set NAID audit requirement for compliance services:
                    if vals.get('records_service_type') in ['destruction', 'retrieval']:
                        vals['naid_audit_required'] = True

            return super().create(vals_list)


    def write(self, vals):
            """Override write to maintain audit trails"""
            result = super().write(vals)

            # Create audit trail when certain fields change
            audit_trigger_fields = [
                'records_service_type', 'container_count', 'shredding_weight_lbs',
                'destruction_method', 'naid_compliant'
            ]

            if any(field in vals for field in audit_trigger_fields):
                for line in self.filtered('records_related'):
                    if line.naid_audit_required and not line.audit_trail_created:
                        line.action_create_audit_trail()

            return result


    def name_get(self):
            """Custom name display for records management lines""":
            result = []
            for line in self:
                if line.records_related and line.records_service_type:
                    name = _("%s - %s",
                            line.records_service_type.title(),
                            line.name or 'Service Line')
                    if line.container_count:
                        name += _(" (%d containers)", line.container_count)
                else:
                    name = line.name or _('Invoice Line')
                result.append((line.id, name))
            return result

        # ============================================================================
            # INTEGRATION METHODS
        # ============================================================================

    def sync_with_work_order(self):
            """Synchronize data with related work order"""
            self.ensure_one()

            if not self.work_order_id:
                return

            work_order = self.work_order_id

            # Update container information
            if hasattr(work_order, 'container_ids'):
                self.container_ids = [(6, 0, work_order.container_ids.ids)]
                self.container_count = len(work_order.container_ids)

            # Update billing configuration
            if hasattr(work_order, 'billing_config_id'):
                self.billing_config_id = work_order.billing_config_id

            # Update location information
            if hasattr(work_order, 'pickup_location_id'):
                self.origin_location_id = work_order.pickup_location_id

            if hasattr(work_order, 'delivery_location_id'):
                self.destination_location_id = work_order.delivery_location_id


    def generate_billing_report_data(self):
            """Generate data for billing reports""":
            self.ensure_one()

            return {
                'invoice_line_id': self.id,
                'invoice_number': self.move_id.name if self.move_id else '',:
                'customer': self.partner_id.name if self.partner_id else '',:
                'service_type': self.records_service_type,
                'service_date': self.pickup_date or self.move_id.invoice_date,
                'container_count': self.container_count,
                'weight_processed': self.shredding_weight_lbs,
                'unit_rate': self.unit_rate,
                'total_amount': self.price_total,
                'naid_compliant': self.naid_compliant,
                'audit_trail_created': self.audit_trail_created,
                'customer_satisfaction': self.customer_satisfaction_rating,
            }
