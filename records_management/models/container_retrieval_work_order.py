from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class ContainerRetrievalWorkOrder(models.Model):
    _name = 'container.retrieval.work.order'
    _description = 'Container Retrieval Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'work.order.integration.mixin']
    _order = 'priority desc, scheduled_delivery_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    display_name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    state = fields.Selection()
    priority = fields.Selection()
    partner_id = fields.Many2one()
    container_ids = fields.Many2many()
    container_count = fields.Integer()
    total_volume = fields.Float()
    total_weight = fields.Float()
    scheduled_delivery_date = fields.Datetime()
    delivery_window_start = fields.Datetime()
    delivery_window_end = fields.Datetime()
    actual_pickup_date = fields.Datetime()
    actual_delivery_date = fields.Datetime()
    delivery_address_id = fields.Many2one()
    delivery_instructions = fields.Text()
    access_requirements = fields.Text()
    contact_person = fields.Char()
    contact_phone = fields.Char()
    vehicle_id = fields.Many2one()
    driver_id = fields.Many2one()
    route_id = fields.Many2one()
    equipment_needed = fields.Text()
    delivery_receipt_signed = fields.Boolean()
    customer_signature = fields.Binary()
    delivery_photo = fields.Binary()
    delivery_notes = fields.Text()
    customer_satisfaction_rating = fields.Selection()
    duration_hours = fields.Float()
    is_overdue = fields.Boolean()
    days_until_delivery = fields.Integer()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
    coordinator_id = fields.Many2one('work.order.coordinator')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def create(self, vals_list):
            for vals in vals_list:
                if vals.get('name', _('New')) == _('New'):
                    vals['name') = self.env['ir.sequence'].next_by_code()
                        'container.retrieval.work.order') or _('New'
            return super().create(vals_list)

        # ============================================================================
            # COMPUTE METHODS
        # ============================================================================

    def _compute_display_name(self):
            for record in self:
                if record.partner_id and record.container_count:
                    record.display_name = _("%s - %s (%s containers)",
                        record.name, record.partner_id.name, record.container_count
                elif record.partner_id:
                    record.display_name = _("%s - %s", record.name, record.partner_id.name)
                else:
                    record.display_name = record.name or _("New Container Retrieval")


    def _compute_container_metrics(self):
            for record in self:
                containers = record.container_ids
                record.container_count = len(containers)
                record.total_volume = sum(containers.mapped('volume_cf')) if containers else 0.0:
                record.total_weight = sum(containers.mapped('estimated_weight')) if containers else 0.0:

    def _compute_delivery_window(self):
            for record in self:
                if record.scheduled_delivery_date:
                    # Default 2-hour delivery window
                    record.delivery_window_start = record.scheduled_delivery_date - timedelta(hours=1)
                    record.delivery_window_end = record.scheduled_delivery_date + timedelta(hours=1)
                else:
                    record.delivery_window_start = False
                    record.delivery_window_end = False


    def _compute_duration(self):
            for record in self:
                if record.actual_pickup_date and record.actual_delivery_date:
                    delta = record.actual_delivery_date - record.actual_pickup_date
                    record.duration_hours = delta.total_seconds() / 3600.0
                else:
                    record.duration_hours = 0.0


    def _compute_overdue_status(self):
            now = datetime.now()
            for record in self:
                record.is_overdue = ()
                    record.scheduled_delivery_date and
                    record.scheduled_delivery_date < now and
                    record.state not in ['delivered', 'completed', 'cancelled']



    def _compute_days_until_delivery(self):
            today = datetime.now().date()
            for record in self:
                if record.scheduled_delivery_date:
                    delivery_date = record.scheduled_delivery_date.date()
                    delta = delivery_date - today
                    record.days_until_delivery = delta.days
                else:
                    record.days_until_delivery = 0

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_delivery_date(self):
            for record in self:
                if record.scheduled_delivery_date and record.scheduled_delivery_date <= datetime.now():
                    raise ValidationError(_("Scheduled delivery date must be in the future"))


    def _check_containers(self):
            for record in self:
                if not record.container_ids:
                    raise ValidationError(_("At least one container must be selected for retrieval")):

    def _check_delivery_sequence(self):
            for record in self:
                if (record.actual_pickup_date and record.actual_delivery_date and:)
                    record.actual_pickup_date > record.actual_delivery_date
                    raise ValidationError(_("Pickup date cannot be after delivery date"))

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_confirm(self):
            """Confirm the work order"""
            self.ensure_one()
            if self.state != 'draft':
                raise UserError(_("Only draft work orders can be confirmed"))

            # pylint: disable=no-member


            self.write({'state': 'confirmed'})
            self.message_post()
                body=_("Container retrieval work order confirmed for %s", self.partner_id.name),:
                message_type='notification'

            return True


    def action_schedule(self):
            """Schedule the work order"""
            self.ensure_one()
            if self.state != 'confirmed':
                raise UserError(_("Only confirmed work orders can be scheduled"))

            if not self.vehicle_id or not self.driver_id:
                raise UserError(_("Vehicle and driver must be assigned before scheduling"))

            # pylint: disable=no-member


            self.write({'state': 'scheduled'})
            self.message_post()
                body=_("Work order scheduled for delivery on %s", self.scheduled_delivery_date),:
                message_type='notification'

            return True


    def action_start_transit(self):
            """Mark containers as in transit"""
            self.ensure_one()
            if self.state != 'scheduled':
                raise UserError(_("Only scheduled work orders can be started"))

            # pylint: disable=no-member


            self.write({)}
                'state': 'in_transit',
                'actual_pickup_date': fields.Datetime.now()


            # Update container locations to in-transit
            # pylint: disable=no-member

            self.container_ids.write({'location_status': 'in_transit'})

            self.message_post()
                body=_("Containers picked up and in transit to %s", self.partner_id.name),
                message_type='notification'

            return True


    def action_confirm_delivery(self):
            """Confirm delivery completion"""
            self.ensure_one()
            if self.state != 'in_transit':
                raise UserError(_("Only work orders in transit can be marked as delivered"))

            # pylint: disable=no-member


            self.write({)}
                'state': 'delivered',
                'actual_delivery_date': fields.Datetime.now()


            # Update container locations to customer location
            delivery_location = self.delivery_address_id or self.partner_id
            if delivery_location:
                # Find or create customer location record
                # pylint: disable=no-member

                customer_location = self.env['records.location'].search([)]
                    ('partner_id', '=', delivery_location.id),
                    ('location_type', '=', 'customer')


                if not customer_location:
                    # pylint: disable=no-member

                    customer_location = self.env['records.location'].create({)}
                        'name': _("Customer Location - %s", delivery_location.name),
                        'partner_id': delivery_location.id,
                        'location_type': 'customer',
                        'address': delivery_location.contact_address,


                # Update container locations
                # pylint: disable=no-member

                self.container_ids.write({)}
                    'location_id': customer_location.id,
                    'location_status': 'at_customer'


            self.message_post()
                body=_("Containers successfully delivered to %s", self.partner_id.name),
                message_type='notification'

            return True


    def action_complete(self):
            """Complete the work order"""
            self.ensure_one()
            if self.state != 'delivered':
                raise UserError(_("Only delivered work orders can be completed"))

            if not self.delivery_receipt_signed:
                raise UserError(_("Delivery receipt must be signed before completion"))

            # pylint: disable=no-member


            self.write({'state': 'completed'})
            self.message_post()
                body=_("Container retrieval work order completed successfully"),
                message_type='notification'


            # Create activity for follow-up if needed:
            if self.customer_satisfaction_rating and int(self.customer_satisfaction_rating) < 4:
                self.activity_schedule()
                    'mail.mail_activity_data_call',
                    summary=_("Follow up on delivery satisfaction"),
                    note=_("Customer satisfaction rating was %s. Follow up required.",
                            dict(self._fields['customer_satisfaction_rating'].selection)[self.customer_satisfaction_rating]
                    user_id=self.user_id.id


            return True


    def action_cancel(self):
            """Cancel the work order"""
            self.ensure_one()
            if self.state in ['delivered', 'completed']:
                raise UserError(_("Delivered or completed work orders cannot be cancelled"))

            # pylint: disable=no-member


            self.write({'state': 'cancelled'})
            self.message_post()
                body=_("Container retrieval work order cancelled"),
                message_type='notification'

            return True

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def send_delivery_notification(self):
            """Send delivery notification to customer"""
            self.ensure_one()
            template = self.env.ref('records_management.email_template_container_delivery_notification', False)
            if template:
                template.send_mail(self.id, force_send=True)


    def generate_delivery_report(self):
            """Generate delivery report for customer""":
            self.ensure_one()
            return {}
                'type': 'ir.actions.report',
                'report_name': 'records_management.report_container_delivery',
                'report_type': 'qweb-pdf',
                'res_id': self.id,
                'target': 'new',



    def action_reschedule_delivery(self):
            """Open wizard to reschedule delivery"""
            self.ensure_one()
            return {}
                'type': 'ir.actions.act_window',
                'name': _('Reschedule Delivery'),
                'res_model': 'container.delivery.reschedule.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {}
                    'default_work_order_id': self.id,
                    'default_current_date': self.scheduled_delivery_date))))))))))))))))))))))))))

