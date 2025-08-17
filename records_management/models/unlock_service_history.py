from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class UnlockServiceHistory(models.Model):
    _name = 'unlock.service.reschedule.wizard'
    _description = 'Unlock Service Reschedule Wizard'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    active = fields.Boolean()
    company_id = fields.Many2one()
    technician_id = fields.Many2one()
    customer_id = fields.Many2one()
    partner_bin_key_id = fields.Many2one()
    service_type = fields.Selection()
    date = fields.Datetime()
    scheduled_date = fields.Datetime()
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    duration = fields.Float()
    location_id = fields.Many2one()
    reason = fields.Text()
    resolution = fields.Text()
    notes = fields.Text()
    priority = fields.Selection()
    state = fields.Selection()
    currency_id = fields.Many2one()
    cost = fields.Monetary()
    billable = fields.Boolean()
    invoice_id = fields.Many2one()
    billing_status = fields.Selection()
    equipment_used_ids = fields.Many2many()
    parts_used_ids = fields.One2many()
    quality_check = fields.Boolean()
    quality_rating = fields.Selection()
    customer_signature = fields.Binary()
    verification_code = fields.Char()
    follow_up_required = fields.Boolean()
    follow_up_date = fields.Date()
    warranty_expiry = fields.Date()
    repeat_service = fields.Boolean()
    partner_id = fields.Many2one()
    display_name = fields.Char()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')
    service_id = fields.Many2one()
    new_date = fields.Datetime()
    reason = fields.Text()
    notify_customer = fields.Boolean()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute display name for service""":
            for record in self:
                if record.name and record.service_type:
                    service_type_display = dict()
                        record._fields["service_type"].selection
                    ).get(record.service_type, ""
                    customer_name = record.customer_id.name or "Unknown"
                    record.display_name = ()
                        f"{record.name} - {service_type_display} ({customer_name})"

                else:
                    record.display_name = record.name or _("New Service")


    def _compute_duration(self):
            """Compute service duration in minutes"""
            for record in self:
                if record.start_time and record.end_time:
                    duration_seconds = ()
                        record.end_time - record.start_time
                    ).total_seconds(
                    record.duration = duration_seconds / 60.0
                else:
                    record.duration = 0.0

        # ============================================================================
            # ORM OVERRIDES
        # ============================================================================

    def create(self, vals_list):
            """Override create to generate sequence numbers"""
            for vals in vals_list:
                if vals.get("name", "New") == "New":
                    vals["name") = (]
                        self.env["ir.sequence"].next_by_code("unlock.service.history")
                        or "USH-NEW"

            return super().create(vals_list)


    def write(self, vals):
            """Override write to handle state changes"""
            result = super().write(vals)
            if "state" in vals:
                for record in self:
                    if vals["state"] == "completed":
                        record._handle_service_completion()
                    elif vals["state"] == "cancelled":
                        record._handle_service_cancellation()
            return result

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_start_service(self):
            """Start the unlock service"""
            self.ensure_one()
            if self.state != "scheduled":
                raise UserError(_("Only scheduled services can be started"))
            self.write()
                {"state": "in_progress", "start_time": fields.Datetime.now()}

            self.message_post(body=_("Service started"))


    def action_complete_service(self):
            """Complete the unlock service"""
            self.ensure_one()
            if self.state != "in_progress":
                raise UserError(_("Only in-progress services can be completed"))
            self.write({"state": "completed", "end_time": fields.Datetime.now()})
            self.message_post(body=_("Service completed successfully"))
            self._handle_service_completion()


    def action_cancel_service(self):
            """Cancel the unlock service"""
            self.ensure_one()
            if self.state in ["completed", "cancelled"]:
                raise UserError()
                    _("Completed or cancelled services cannot be cancelled")

            self.write({"state": "cancelled"})
            self.message_post(body=_("Service cancelled"))
            self._handle_service_cancellation()


    def action_reschedule_service(self):
            """Reschedule the service"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Reschedule Service"),
                "res_model": "unlock.service.reschedule.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {"default_service_id": self.id},



    def action_create_invoice(self):
            """Create invoice for billable service""":
            self.ensure_one()
            if not self.billable:
                raise UserError(_("Service is not billable"))
            if not self.customer_id:
                raise UserError(_("Customer is required for billing")):
            if self.invoice_id:
                raise UserError(_("Invoice already exists for this service")):
            invoice_vals = self._prepare_invoice_values()
            invoice = self.env["account.move"].create(invoice_vals)
            self.write({"invoice_id": invoice.id, "billing_status": "billed"})
            self.message_post(body=_("Invoice created: %s", invoice.name))

            return {}
                "type": "ir.actions.act_window",
                "name": _("Invoice"),
                "res_model": "account.move",
                "res_id": invoice.id,
                "view_mode": "form",



    def action_send_completion_notification(self):
            """Send service completion notification to customer"""
            self.ensure_one()
            if self.state != "completed":
                raise UserError()
                    _("Only completed services can send notifications")

            template = self.env.ref()
                "records_management.unlock_service_completion_email_template",
                raise_if_not_found=False,

            if template:
                template.send_mail(self.id, force_send=True)
                self.message_post(body=_("Completion notification sent to customer"))


    def action_schedule_follow_up(self):
            """Schedule follow-up service"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Schedule Follow-up"),
                "res_model": "unlock.service.history",
                "view_mode": "form",
                "target": "new",
                "context": {}
                    "default_partner_bin_key_id": self.partner_bin_key_id.id,
                    "default_customer_id": self.customer_id.id,
                    "default_location_id": self.location_id.id,
                    "default_service_type": "maintenance",
                    "default_reason": _("Follow-up service for %s", self.name),:



        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def _handle_service_completion(self):
            """Handle tasks when service is completed"""
            self.ensure_one()
            if self.partner_bin_key_id:
                self.partner_bin_key_id.write()
                    {}
                        "last_service_date": self.date,
                        "service_count": self.partner_bin_key_id.service_count + 1,


            if self.follow_up_required and self.follow_up_date:
                self.activity_schedule()
                    "mail.mail_activity_data_todo",
                    date_deadline=self.follow_up_date,
                    summary=_("Follow-up service for %s", self.name),:
                    note=_()
                        "Scheduled follow-up service based on completion requirements."

                    user_id=self.technician_id.id,

            if self.billable and not self.invoice_id and self.customer_id:
                try:
                    self.action_create_invoice()
                except Exception as e
                    self.message_post(body=_("Auto-billing failed: %s", str(e)))


    def _handle_service_cancellation(self):
            """Handle tasks when service is cancelled"""
            self.ensure_one()
            activities = self.activity_ids.filtered(lambda a: a.res_model == self._name)
            activities.action_done()
            if self.billing_status == "not_billed":
                self.write({"billing_status": "cancelled"})


    def _prepare_invoice_values(self):
            """Prepare values for invoice creation""":
            self.ensure_one()
            product = self.env["product.product").search(]
                [("default_code", "=", "UNLOCK_SERVICE")], limit=1

            if not product:
                product = self.env["product.product").create(]
                    {}
                        "name": "Unlock Service",
                        "default_code": "UNLOCK_SERVICE",
                        "type": "service",
                        "list_price": 50.0,
                        "invoice_policy": "order",


            invoice_line_vals = {}
                "product_id": product.id,
                "name": _("Unlock Service - %s", self.name),
                "quantity": 1,
                "price_unit": self.cost or product.list_price,

            return {}
                "partner_id": self.customer_id.id,
                "move_type": "out_invoice",
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [(0, 0, invoice_line_vals)],



    def get_service_summary(self):
            """Get service summary for reporting""":
            self.ensure_one()
            return {}
                "name": self.name,
                "service_type": self.service_type,
                "customer": self.customer_id.name if self.customer_id else None,:
                "technician": self.technician_id.name,
                "date": self.date,
                "duration": self.duration,
                "cost": self.cost,
                "state": self.state,
                "billing_status": self.billing_status,


        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_service_times(self):
            """Validate service times"""
            for record in self:
                if record.start_time and record.end_time:
                    if record.end_time <= record.start_time:
                        raise ValidationError(_("End time must be after start time"))


    def _check_cost(self):
            """Validate service cost"""
            for record in self:
                if record.cost < 0:
                    raise ValidationError(_("Service cost cannot be negative"))


    def _check_follow_up_date(self):
            """Validate follow-up date"""
            for record in self:
                if record.follow_up_required and record.follow_up_date:

    def action_reschedule(self):
            """Execute the reschedule"""
            self.ensure_one()
            self.service_id.write()
                {"scheduled_date": self.new_date, "date": self.new_date}

            self.service_id.message_post()
                body=_()
                    "Service rescheduled to %s. Reason: %s",
                    self.new_date.strftime("%Y-%m-%d %H:%M"),
                    self.reason,


            if self.notify_customer and self.service_id.customer_id:
                template = self.env.ref()
                    "records_management.unlock_service_reschedule_email_template",
                    raise_if_not_found=False,

                if template:
                    template.send_mail(self.service_id.id, force_send=True)
            return {"type": "ir.actions.act_window_close"}


    def _check_new_date(self):
            """Validate new service date"""
            for record in self:
