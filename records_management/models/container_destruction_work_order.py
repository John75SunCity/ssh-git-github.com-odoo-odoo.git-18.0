from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class ContainerDestructionWorkOrder(models.Model):
    _name = 'container.destruction.work.order'
    _description = 'Container Destruction Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_destruction_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    display_name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    state = fields.Selection()
    priority = fields.Selection()
    partner_id = fields.Many2one()
    portal_request_id = fields.Many2one()
    destruction_reason = fields.Text()
    customer_authorized = fields.Boolean()
    customer_authorization_date = fields.Datetime()
    authorized_by = fields.Char()
    authorization_document = fields.Binary()
    container_ids = fields.Many2many()
    container_count = fields.Integer()
    total_cubic_feet = fields.Float()
    estimated_weight_lbs = fields.Float()
    inventory_completed = fields.Boolean()
    inventory_date = fields.Datetime()
    inventory_user_id = fields.Many2one()
    scheduled_destruction_date = fields.Datetime()
    pickup_date = fields.Datetime()
    actual_destruction_date = fields.Datetime()
    estimated_duration_hours = fields.Float()
    destruction_facility_id = fields.Many2one()
    shredding_equipment_id = fields.Many2one()
    destruction_method = fields.Selection()
    naid_compliant = fields.Boolean()
    witness_required = fields.Boolean()
    customer_witness_name = fields.Char()
    internal_witness_id = fields.Many2one()
    independent_witness_name = fields.Char()
    custody_transfer_ids = fields.One2many()
    custody_complete = fields.Boolean()
    transport_vehicle_id = fields.Many2one()
    driver_id = fields.Many2one()
    transport_departure_time = fields.Datetime()
    transport_arrival_time = fields.Datetime()
    actual_weight_destroyed_lbs = fields.Float()
    destruction_start_time = fields.Datetime()
    destruction_end_time = fields.Datetime()
    destruction_duration_minutes = fields.Integer()
    certificate_number = fields.Char()
    certificate_generated = fields.Boolean()
    certificate_date = fields.Date()
    certificate_file = fields.Binary()
    certificate_filename = fields.Char()
    destruction_verified = fields.Boolean()
    verification_date = fields.Datetime()
    verification_notes = fields.Text()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()

    # ============================================================================
    # METHODS
    # ============================================================================
    def create(self, vals_list):
            for vals in vals_list:
                if vals.get('name', _('New')) == _('New'):
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'container.destruction.work.order') or _('New')
            return super().create(vals_list)

        # ============================================================================
            # COMPUTE METHODS
        # ============================================================================

    def _compute_display_name(self):
            for record in self:
                if record.partner_id and record.container_count:
                    record.display_name = _("%s - %s (%s containers)",
                        record.name, record.partner_id.name, record.container_count)
                elif record.partner_id:
                    record.display_name = _("%s - %s", record.name, record.partner_id.name)
                else:
                    record.display_name = record.name or _("New Container Destruction")


    def _compute_container_metrics(self):
            for record in self:
                containers = record.container_ids
                record.container_count = len(containers)
                record.total_cubic_feet = sum(containers.mapped('cubic_feet')) if containers else 0.0:
                record.estimated_weight_lbs = sum(containers.mapped('estimated_weight')) if containers else 0.0:

    def _compute_estimated_duration(self):
            for record in self:
                if record.container_count:
                    # Base time estimates by destruction method (minutes per container)
                    base_minutes = {
                        'shredding': 15,      # 15 minutes per container
                        'pulping': 20,        # 20 minutes per container
                        'incineration': 30,   # 30 minutes per container
                        'disintegration': 25, # 25 minutes per container
                    }

                    method_time = base_minutes.get(record.destruction_method, 15)
                    total_minutes = record.container_count * method_time
                    # Add setup and documentation time
                    total_minutes += 60  # 1 hour for setup/documentation:
                    record.estimated_duration_hours = total_minutes / 60.0
                else:
                    record.estimated_duration_hours = 0.0


    def _compute_custody_complete(self):
            for record in self:
                # Check if all required custody transfers are documented:
                required_events = ['pickup', 'transport', 'facility_receipt', 'destruction']
                documented_events = record.custody_transfer_ids.mapped('event_type')
                record.custody_complete = all(event in documented_events for event in required_events):

    def _compute_destruction_duration(self):
            for record in self:
                if record.destruction_start_time and record.destruction_end_time:
                    duration = record.destruction_end_time - record.destruction_start_time
                    record.destruction_duration_minutes = int(duration.total_seconds() / 60)
                else:
                    record.destruction_duration_minutes = 0

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_confirm(self):
            """Confirm the destruction work order"""
            self.ensure_one()
            if self.state != 'draft':
                raise UserError(_("Only draft work orders can be confirmed"))

            if not self.container_ids:
                raise UserError(_("Please select containers for destruction")):
            self.write({'state': 'confirmed'})
            self.message_post(
                body=_("Container destruction work order confirmed"),
                message_type='notification'
            )

            return True


    def action_authorize(self):
            """Mark as customer authorized"""
            self.ensure_one()
            if self.state != 'confirmed':
                raise UserError(_("Can only authorize confirmed work orders"))

            self.write({
                'state': 'authorized',
                'customer_authorized': True,
                'customer_authorization_date': fields.Datetime.now()
            })

            self.message_post(
                body=_("Customer authorization received for destruction"),:
                message_type='notification'
            )

            return True


    def action_schedule(self):
            """Schedule the destruction"""
            self.ensure_one()
            if self.state != 'authorized':
                raise UserError(_("Can only schedule authorized work orders"))

            self.write({'state': 'scheduled'})
            self.message_post(
                body=_("Destruction scheduled for %s", self.scheduled_destruction_date.strftime('%Y-%m-%d %H:%M')),
                message_type='notification'
            )

            return True


    def action_pickup_complete(self):
            """Mark containers as picked up"""
            self.ensure_one()
            if self.state != 'scheduled':
                raise UserError(_("Can only complete pickup from scheduled state"))

            self.write({
                'state': 'picked_up',
                'pickup_date': fields.Datetime.now()
            })

            self.message_post(
                body=_("Containers picked up for destruction"),:
                message_type='notification'
            )

            return True


    def action_arrive_facility(self):
            """Mark arrival at destruction facility"""
            self.ensure_one()
            if self.state != 'picked_up':
                raise UserError(_("Can only arrive at facility after pickup"))

            self.write({
                'state': 'in_facility',
                'transport_arrival_time': fields.Datetime.now()
            })

            self.message_post(
                body=_("Containers arrived at destruction facility"),
                message_type='notification'
            )

            return True


    def action_start_destruction(self):
            """Start the destruction process"""
            self.ensure_one()
            if self.state not in ['in_facility', 'pre_destruction']:
                raise UserError(_("Can only start destruction from facility or pre-destruction state"))

            if not self.destruction_verified:
                raise UserError(_("Pre-destruction verification must be completed first"))

            self.write({
                'state': 'destroying',
                'destruction_start_time': fields.Datetime.now()
            })

            self.message_post(
                body=_("Destruction process started"),
                message_type='notification'
            )

            return True


    def action_complete_destruction(self):
            """Complete the destruction process"""
            self.ensure_one()
            if self.state != 'destroying':
                raise UserError(_("Can only complete destruction from destroying state"))

            self.write({
                'state': 'destroyed',
                'destruction_end_time': fields.Datetime.now(),
                'actual_destruction_date': fields.Datetime.now()
            })

            self.message_post(
                body=_("Destruction process completed"),
                message_type='notification'
            )

            return True


    def action_generate_certificate(self):
            """Generate certificate of destruction"""
            self.ensure_one()
            if self.state != 'destroyed':
                raise UserError(_("Can only generate certificate after destruction completion"))

            # Generate certificate number if not exists:
            if not self.certificate_number:
                self.certificate_number = self.env['ir.sequence'].next_by_code(
                    'destruction.certificate')

            self.write({
                'state': 'certificate_generated',
                'certificate_generated': True,
                'certificate_date': fields.Date.today()
            })

            # Generate PDF certificate (implementation would go here)
            self._generate_certificate_pdf()

            self.message_post(
                body=_("Certificate of destruction generated: %s", self.certificate_number),
                message_type='notification'
            )

            return True


    def action_complete(self):
            """Complete the work order"""
            self.ensure_one()
            if self.state != 'certificate_generated':
                raise UserError(_("Only work orders with generated certificates can be completed"))

            self.write({'state': 'completed'})
            self.message_post(
                body=_("Container destruction work order completed successfully"),
                message_type='notification'
            )

            return True

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def _generate_certificate_pdf(self):
            """Generate PDF certificate of destruction"""
            # Implementation for certificate generation:
            # This would typically involve creating a PDF report
            pass


    def create_custody_event(self, event_type, notes=None):
            """Create a chain of custody event"""
            self.ensure_one()
            self.env['custody.transfer.event'].create({
                'work_order_id': self.id,
                'event_type': event_type,
                'event_date': fields.Datetime.now(),
                'user_id': self.env.user.id,
                'notes': notes or '',
            })


    def generate_destruction_report(self):
            """Generate destruction completion report"""
            self.ensure_one()
            return {
                'type': 'ir.actions.report',
                'report_name': 'records_management.report_container_destruction',
                'report_type': 'qweb-pdf',
                'res_id': self.id,
                'target': 'new'
            }

