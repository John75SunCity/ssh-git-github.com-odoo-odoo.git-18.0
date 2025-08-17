from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ShreddingService(models.Model):
    _name = 'shredding.service.photo'
    _description = 'Shredding Service Photo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    reference = fields.Char()
    description = fields.Text()
    sequence = fields.Integer()
    active = fields.Boolean()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    assigned_technician_id = fields.Many2one()
    assigned_team_ids = fields.Many2many()
    state = fields.Selection()
    partner_id = fields.Many2one()
    contact_id = fields.Many2one()
    location_id = fields.Many2one()
    container_type_id = fields.Many2one()
    service_type = fields.Selection()
    material_type = fields.Selection()
    destruction_method = fields.Selection()
    certificate_required = fields.Boolean()
    naid_compliance_required = fields.Boolean()
    container_type = fields.Selection()
    destruction_item_count = fields.Integer()
    estimated_volume = fields.Float()
    actual_volume = fields.Float()
    service_date = fields.Date()
    service_time = fields.Float()
    estimated_duration = fields.Float()
    priority = fields.Selection()
    team_id = fields.Many2one()
    technician_ids = fields.Many2many()
    vehicle_id = fields.Many2one()
    equipment_ids = fields.Many2many()
    equipment_id = fields.Many2one()
    recycling_bale_id = fields.Many2one()
    batch_id = fields.Many2one()
    estimated_volume = fields.Float()
    estimated_weight = fields.Float()
    actual_volume = fields.Float()
    actual_weight = fields.Float()
    container_ids = fields.Many2many()
    bin_ids = fields.Many2many()
    currency_id = fields.Many2one()
    unit_price = fields.Float()
    total_amount = fields.Float()
    travel_charge = fields.Float()
    emergency_charge = fields.Float()
    equipment_charge = fields.Float()
    requires_certificate = fields.Boolean()
    certificate_type = fields.Selection()
    certificate_id = fields.Many2one()
    compliance_level = fields.Selection()
    special_instructions = fields.Text()
    access_requirements = fields.Text()
    security_clearance = fields.Boolean()
    witness_required = fields.Boolean()
    actual_start_time = fields.Datetime()
    actual_end_time = fields.Datetime()
    completion_notes = fields.Text()
    customer_signature = fields.Binary()
    photo_ids = fields.One2many()
    duration_hours = fields.Float()
    shred_bin_id = fields.Many2one('shred.bin')
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    destruction_status = fields.Selection(string='Destruction Status')
    witness_company = fields.Char(string='Witness Company')
    witness_name = fields.Char(string='Witness Name')
    naid_compliance_level = fields.Selection(string='NAID Compliance')
    destruction_method_detail = fields.Text(string='Destruction Method Details')
    pre_destruction_weight = fields.Float(string='Pre-Destruction Weight (lbs)')
    post_destruction_weight = fields.Float(string='Post-Destruction Weight (lbs)')
    group_by_partner = fields.Char(string='Group By Partner')
    group_by_service_type = fields.Selection(string='Group By Service Type')
    group_by_shredding_method = fields.Char(string='Group By Shredding Method')
    group_by_state = fields.Selection(string='Group By State')
    service_type_off_site = fields.Char(string='Service Type Off Site')
    service_type_on_site = fields.Char(string='Service Type On Site')
    shredding_method_strip_cut = fields.Char(string='Shredding Method Strip Cut')
    context = fields.Char(string='Context')
    filter_after = fields.Char(string='Filter After')
    filter_before = fields.Char(string='Filter Before')
    filter_today = fields.Char(string='Filter Today')
    filter_witnessed = fields.Char(string='Filter Witnessed')
    group_date = fields.Date(string='Group Date')
    group_photo_type = fields.Selection(string='Group Photo Type')
    group_service = fields.Char(string='Group Service')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    view_mode = fields.Char(string='View Mode')
    service_id = fields.Many2one()
    sequence = fields.Integer()
    name = fields.Char()
    description = fields.Text()
    photo = fields.Binary()
    taken_date = fields.Datetime()
    destruction_item_ids = fields.One2many('destruction.item')
    witness_ids = fields.Many2many()
    hourly_rate = fields.Float(string='Hourly Rate')
    photo_type = fields.Selection()
    taken_by_id = fields.Many2one()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_total_amount(self):
            """Compute total service amount"""
            for service in self:
                base_amount = service.unit_price * max()
                    service.actual_volume, service.actual_weight

                total = ()
                    base_amount
                    + service.travel_charge
                    + service.emergency_charge
                    + service.equipment_charge

                service.total_amount = total


    def _compute_duration_hours(self):
            """Compute actual service duration"""
            for service in self:
                if service.actual_start_time and service.actual_end_time:
                    delta = service.actual_end_time - service.actual_start_time
                    service.duration_hours = delta.total_seconds() / 3600.0
                else:
                    service.duration_hours = 0.0


    def _compute_destruction_items(self):
            """Compute number of items to be destroyed"""
            for service in self:
                # Count inventory items if available:
                if hasattr(service, 'inventory_item_ids'):
                    service.destruction_item_count = len(service.inventory_item_ids)
                else:
                    # Fallback to estimated count based on volume
                    if service.estimated_volume:
                        # Rough estimate: 1 item per 0.1 cubic feet
                        service.destruction_item_count = int(service.estimated_volume / 0.1)
                    else:
                        service.destruction_item_count = 0

        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def action_schedule(self):
            """Schedule the shredding service"""

            self.ensure_one()
            if self.state != "draft":
                raise UserError(_("Only draft services can be scheduled"))
            self._validate_scheduling_requirements()
            self.write({"state": "scheduled"})
            self.message_post(body=_("Service scheduled for %s", self.service_date)):

    def action_start_service(self):
            """Start the shredding service"""

            self.ensure_one()
            if self.state != "scheduled":
                raise UserError(_("Only scheduled services can be started"))
            self.write({)}
                "state": "in_progress",
                "actual_start_time": fields.Datetime.now(),

            self.message_post(body=_("Service started"))


    def action_complete_service(self):
            """Complete the shredding service"""

            self.ensure_one()
            if self.state != "in_progress":
                raise UserError(_("Only in-progress services can be completed"))
            self._validate_completion_requirements()
            self.write({)}
                "state": "completed",
                "actual_end_time": fields.Datetime.now(),


            # Generate certificate if required:
            if self.requires_certificate:
                self._generate_certificate()

            self.message_post(body=_("Service completed"))


    def action_cancel(self):
            """Cancel the shredding service"""

            self.ensure_one()
            if self.state in ("completed", "invoiced"):
                raise UserError(_("Cannot cancel completed or invoiced services"))
            self.write({"state": "cancelled"})
            self.message_post(body=_("Service cancelled"))


    def action_create_invoice(self):
            """Create invoice for the service""":
            self.ensure_one()
            if self.state != "completed":
                raise UserError(_("Only completed services can be invoiced"))

            # Invoice creation logic would go here
            self.write({"state": "invoiced"})
            self.message_post(body=_("Service invoiced"))


    def action_reschedule(self):
            """Reschedule the service"""

            self.ensure_one()
            if self.state not in ("draft", "scheduled"):
                raise UserError(_("Only draft or scheduled services can be rescheduled"))

            return {}
                "type": "ir.actions.act_window",
                "name": _("Reschedule Service"),
                "res_model": "shredding.service.reschedule.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {"default_service_id": self.id},


        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _validate_scheduling_requirements(self):
            """Validate requirements for scheduling""":
            if not self.partner_id:
                raise UserError(_("Customer is required"))
            if not self.service_date:
                raise UserError(_("Service date is required"))
            if not self.team_id and not self.technician_ids:
                raise UserError(_("Team or technicians must be assigned"))


    def _validate_completion_requirements(self):
            """Validate requirements for completion""":
            if not self.actual_volume and not self.actual_weight:
                raise UserError(_("Actual volume or weight must be recorded"))


    def _generate_certificate(self):
            """Generate destruction certificate"""
            certificate_vals = {}
                "service_id": self.id,
                "partner_id": self.partner_id.id,
                "certificate_type": self.certificate_type,
                "material_type": self.material_type,
                "volume_destroyed": self.actual_volume,
                "weight_destroyed": self.actual_weight,
                "destruction_date": ()
                    self.actual_end_time.date()
                    if self.actual_end_time:
                    else fields.Date.today()

                "compliance_level": self.compliance_level,


            if "shredding.certificate" in self.env:
                certificate = self.env["shredding.certificate").create(certificate_vals]
                self.certificate_id = certificate.id

        # ============================================================================
            # CONSTRAINT METHODS
        # ============================================================================

    def _check_service_date(self):
            """Validate service date is not in the past"""
            for record in self:
                if record.service_date and record.service_date < fields.Date.today():
                    if record.state == "draft":  # Allow past dates for completed services:
                        raise ValidationError(_("Service date cannot be in the past"))


    def _check_estimates(self):
            """Validate estimated values are non-negative"""
            for record in self:
                if record.estimated_volume < 0 or record.estimated_weight < 0:
                    raise ValidationError(_("Estimated values cannot be negative"))


    def _check_actual_times(self):
            """Validate actual start and end times"""
            for record in self:
                if record.actual_start_time and record.actual_end_time:
                    if record.actual_end_time <= record.actual_start_time:
                        raise ValidationError(_("End time must be after start time"))


    def _check_charges(self):
            """Validate charges are non-negative"""
            for record in self:
                charges = []
                    record.unit_price,
                    record.travel_charge,
                    record.emergency_charge,
                    record.equipment_charge

                if any(charge < 0 for charge in charges):
                    raise ValidationError(_("All charges must be non-negative"))

        # ============================================================================
            # ORM OVERRIDES
        # ============================================================================

    def create(self, vals_list):
            """Override create to generate sequence numbers"""
            for vals in vals_list:
                if not vals.get("name") or vals["name"] == "/":
                    vals["name") = (]
                        self.env["ir.sequence"].next_by_code("shredding.service") or "NEW"

            return super().create(vals_list)


    def write(self, vals):
            """Override write to handle state changes"""
            # Log state changes
            if "state" in vals:
                for record in self:
                    if record.state != vals["state"]:
                        record.message_post()
                            body=_("State changed from %s to %s",
                                dict(record._fields["state"].selection)[record.state],
                                dict(record._fields["state"].selection)[vals["state"]]


            return super().write(vals)

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def get_service_summary(self):
            """Get service summary for reporting""":
            self.ensure_one()
            return {}
                "name": self.name,
                "customer": self.partner_id.name,
                "service_type": self.service_type,
                "material_type": self.material_type,
                "service_date": self.service_date,
                "state": self.state,
                "total_amount": self.total_amount,
                "actual_volume": self.actual_volume,
                "actual_weight": self.actual_weight,
                "certificate_required": self.requires_certificate,
                "certificate_generated": bool(self.certificate_id),



    def get_billing_details(self):
            """Get billing details for invoicing""":
            self.ensure_one()
            return {}
                "base_amount": self.unit_price * max(self.actual_volume, self.actual_weight),
                "travel_charge": self.travel_charge,
                "emergency_charge": self.emergency_charge,
                "equipment_charge": self.equipment_charge,
                "total_amount": self.total_amount,
                "currency": self.currency_id.name,



    def get_pending_services(self):
            """Get services pending completion"""
            return self.search([)]
                ("state", "in", ["scheduled", "in_progress"]),
                ("service_date", "<=", fields.Date.today()),



    def get_overdue_services(self):
            """Get overdue services"""
            return self.search([)]
                ("state", "in", ["scheduled"]),
                ("service_date", "<", fields.Date.today()),


    def _compute_actual_duration(self):
            """Calculate actual service duration"""
            for record in self:
                if record.actual_start_time and record.actual_completion_time:
                    delta = record.actual_completion_time - record.actual_start_time
                    record.actual_duration = delta.total_seconds() / 3600.0  # Convert to hours
                else:
                    record.actual_duration = 0.0

    def _compute_total_weight(self):
            """Calculate total weight from items"""
            for record in self:
                record.total_weight = sum(record.destruction_item_ids.mapped('weight'))

    def _compute_total_cost(self):
            """Calculate total service cost"""
            for record in self:
                if record.hourly_rate and record.actual_duration:
                    record.total_cost = record.hourly_rate * record.actual_duration
                else:
                    record.total_cost = 0.0





