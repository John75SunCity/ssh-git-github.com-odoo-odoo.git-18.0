from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class RecordsChainOfCustody(models.Model):
    _name = 'records.chain.of.custody'
    _description = 'Records Chain of Custody'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'custody_date desc, sequence, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    sequence = fields.Integer()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    customer_id = fields.Many2one()
    partner_id = fields.Many2one()
    document_id = fields.Many2one()
    container_id = fields.Many2one()
    related_work_order_id = fields.Many2one()
    custody_event = fields.Selection()
    custody_date = fields.Datetime()
    description = fields.Text()
    custody_from_id = fields.Many2one()
    custody_to_id = fields.Many2one()
    transfer_reason = fields.Selection()
    supervisor_approval = fields.Boolean()
    supervisor_id = fields.Many2one()
    priority = fields.Selection()
    request_type = fields.Selection()
    custody_signature = fields.Binary()
    signature_date = fields.Datetime()
    witness_id = fields.Many2one()
    verification_code = fields.Char()
    chain_integrity = fields.Selection()
    location_from_id = fields.Many2one()
    location_to_id = fields.Many2one()
    physical_condition = fields.Selection()
    container_seal = fields.Char()
    state = fields.Selection()
    key = fields.Char(string='Metadata Key')
    value = fields.Char()
    notes = fields.Text(string='Internal Notes')
    external_reference = fields.Char()
    transfer_date = fields.Datetime(string='Transfer Date')
    verified = fields.Boolean(string='Verified')
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
    compliance_id = fields.Many2one('naid.compliance')
    display_name = fields.Char()
    transfer_summary = fields.Char()
    now_dt = fields.Datetime()
    event_dt = fields.Datetime()
    now_dt = fields.Datetime()
    event_dt = fields.Datetime()
    days_since_event = fields.Integer()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute display name with event details"""
            for record in self:
                parts = []
                if record.name:
                    parts.append(record.name)
                if record.custody_event:
                    event_label = dict(record._fields["custody_event"].selection).get()
                        record.custody_event, record.custody_event

                    parts.append(_("(%s)", event_label))
                if record.custody_date:
                    parts.append(record.custody_date.strftime("%Y-%m-%d %H:%M"))
                record.display_name = " - ".join(parts) if parts else "New Custody Record":

    def _compute_transfer_summary(self):
            """Compute custody transfer summary"""
            for record in self:
                if record.custody_from_id and record.custody_to_id:
                    record.transfer_summary = _("%s # -> %s",
                        record.custody_from_id.name,
                        record.custody_to_id.name

                elif record.custody_event:
                    event_label = dict(record._fields["custody_event").selection).get(]
                        record.custody_event, record.custody_event

                    record.transfer_summary = event_label
                else:
                    record.transfer_summary = "No Transfer"


    def _compute_days_since_event(self):
            """Compute days since custody event, accounting for user timezone""":
            for record in self:
                if record.custody_date:

    def create(self, vals_list):
            """Override create to auto-generate verification code"""
            for vals in vals_list:
                if not vals.get("verification_code"):
                    vals["verification_code") = (]
                        self.env["ir.sequence"].next_by_code("records.chain.custody")
                        or "NEW"


                # Set custody date if not provided:
                if not vals.get("custody_date"):

    def write(self, vals):
            """Override write to log state changes"""
            # Log significant state changes
            if "state" in vals:
                for record in self:
                    if vals["state"] != record.state:
                        old_state_label = dict(record._fields["state"].selection).get()
                            record.state, record.state

                        new_state_label = dict(record._fields["state"].selection).get()
                            vals["state"], vals["state"]

                        record.message_post()
                            body=_("Custody status changed from %s to %s",
                                    old_state_label,
                                    new_state_label


            return super(RecordsChainOfCustody, self).write(vals)

        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def generate_verification_code(self):
            """Generate unique verification code for custody event""":
            self.ensure_one()

            # Create hash based on record data and timestamp
            data_string = _("%s_%s_%s_%s",
                            self.id,
                            self.custody_date,
                            time.time(),
                            self.customer_id.id
            verification_hash = ()
                hashlib.sha256(data_string.encode()).hexdigest()[:12].upper()


            self.verification_code = _("COC-%s", verification_hash)

            return self.verification_code


    def verify_custody_integrity(self):
            """Verify integrity of custody chain"""
            self.ensure_one()

            # Check for previous custody records:
            previous_records = self.search()
                []
                    ("document_id", "=", self.document_id.id),
                    ("custody_date", "<", self.custody_date),

                order="custody_date desc",
                limit=1,


            if previous_records and previous_records.custody_to_id != self.custody_from_id:
                self.chain_integrity = "broken"
                self.message_post()
                    body=_("Chain of custody integrity broken: Previous custodian mismatch"),
                    message_type="comment",

                return False

            self.chain_integrity = "verified"
            return True


    def create_custody_certificate(self):
            """Generate custody transfer certificate"""
            self.ensure_one()

            if not self.verification_code:
                self.generate_verification_code()

            # Create certificate record
            certificate_vals = {}
                "name": _("Custody Certificate - %s", self.name),
                "certificate_type": "custody",
                "customer_id": self.customer_id.id,
                "document_ids": [(6, 0, [self.document_id.id])] if self.document_id else [],:
                "custody_record_id": self.id,
                "verification_code": self.verification_code,
                "issue_date": fields.Date.today(),


            certificate = self.env["naid.certificate"].create(certificate_vals)

            self.message_post()
                body=_("Custody certificate generated: %s", certificate.name),
                message_type="notification",


            return certificate

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_confirm_custody(self):
            """Confirm custody event"""

            self.ensure_one()

            if self.state != "draft":
                raise ValidationError(_("Only draft custody records can be confirmed"))

            self.write()
                {}
                    "state": "confirmed",
                    "signature_date": fields.Datetime.now(),



            # Verify custody integrity
            self.verify_custody_integrity()

            self.message_post()
                body=_("Custody event confirmed by %s", self.env.user.name),
                message_type="notification",



    def action_complete_custody(self):
            """Complete custody transfer"""

            self.ensure_one()

            if self.state not in ["confirmed", "in_progress"]:
                raise ValidationError()
                    _("Only confirmed or in-progress custody records can be completed")


            self.write({"state": "completed"})

            # Auto-generate certificate for certain event types:
            if self.custody_event in ["transferred", "destroyed", "returned"]:
                self.create_custody_certificate()

            self.message_post()
                body=_("Custody transfer completed"),
                message_type="notification"



    def action_verify_custody(self):
            """Verify custody record by supervisor"""

            self.ensure_one()

            if self.state != "completed":
                raise ValidationError()
                    _("Only completed custody records can be verified")


            self.write()
                {}
                    "state": "verified",
                    "supervisor_id": self.env.user.id,
                    "supervisor_approval": True,



            self.message_post()
                body=_("Custody record verified by supervisor: %s", self.env.user.name),
                message_type="notification",



    def action_cancel_custody(self):
            """Cancel custody record"""

            self.ensure_one()

            if self.state in ["completed", "verified"]:
                raise ValidationError()
                    _("Cannot cancel completed or verified custody records")


            self.write({"state": "cancelled"})

            self.message_post()
                body=_("Custody record cancelled by %s", self.env.user.name),
                message_type="comment",



    def action_reset_to_draft(self):
            """Reset custody record to draft"""

            self.ensure_one()

            if self.state == "verified":
                raise ValidationError()
                    _("Cannot reset verified custody records to draft")


            self.write({"state": "draft"})

            self.message_post()
                body=_("Custody record reset to draft"),
                message_type="comment"



    def action_view_custody_history(self):
            """View complete custody history for document""":
            self.ensure_one()

            domain = []
            if self.document_id:
                domain = [("document_id", "=", self.document_id.id)]
            elif self.container_id:
                domain = [("container_id", "=", self.container_id.id)]
            else:
                domain = [("customer_id", "=", self.customer_id.id)]

            return {}
                "type": "ir.actions.act_window",
                "name": _("Custody History"),
                "res_model": "records.chain.of.custody",
                "view_mode": "tree,form",
                "domain": domain,
                "context": {"default_customer_id": self.customer_id.id},


        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_custody_transfer(self):
            """Validate custody transfer users"""
            for record in self:
                if record.custody_from_id and record.custody_to_id:
                    if record.custody_from_id == record.custody_to_id:
                        raise ValidationError()
                            _("Cannot transfer custody from and to the same user")



    def _check_custody_date(self):
            """Validate custody date"""
            for record in self:
                if record.custody_date and record.custody_date > fields.Datetime.now():
                    raise ValidationError(_("Custody date cannot be in the future"))


    def _check_priority_event_combination(self):
            """Validate priority and event type combinations"""
            for record in self:
                if record.custody_event == "destroyed" and record.priority not in [:]
                    "high",
                    "urgent",
                    "critical",

                    raise ValidationError()
                        _("Destruction events must have high, urgent, or critical priority")


        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def name_get(self):
            """Custom name display"""
            result = []
            for record in self:
                name_parts = [record.name]

                if record.custody_event:
                    event_label = dict(record._fields["custody_event"].selection).get()
                        record.custody_event, record.custody_event or "Unknown Event"

                    name_parts.append(_("(%s)", event_label))

                if record.customer_id:
                    name_parts.append(_("- %s", record.customer_id.name))

                result.append((record.id, " ".join(name_parts)))

            return result


    def _search_name_verification_customer(:):
            self, name, args=None, operator="ilike", limit=100, name_get_uid=None

            """Enhanced search by name, customer, or verification code"""
            args = args or []
            domain = []
            if name:
                domain = []
                    "|",
                    "|",
                    "|",
                    ("name", operator, name),
                    ("customer_id.name", operator, name),
                    ("verification_code", operator, name),
                    ("external_reference", operator, name),

            return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


    def get_custody_chain(self, document_id=None, container_id=None, customer_id=None):
            """Get complete custody chain for a document, container, or customer""":
            domain = [("state", "!=", "cancelled")]

            if document_id:
                domain.append(("document_id", "=", document_id))
            elif container_id:
                domain.append(("container_id", "=", container_id))
            elif customer_id:
                domain.append(("customer_id", "=", customer_id))

            return self.search(domain, order="custody_date asc")


    def create_automatic_custody_event(:):
            self, document_id, event_type, user_from=None, user_to=None, description=None

            """Create automatic custody event for system workflows""":
            document = self.env["records.document"].browse(document_id)
            if not document.exists():
                return False

            vals = {}
                "name": _("Auto-%s: %s", event_type.title(), document.name),
                "document_id": document_id,
                "customer_id": document.customer_id.id,
                "custody_event": event_type,
                "custody_date": fields.Datetime.now(),
                "description": description or _("Automatic %s event", event_type),
                "custody_from_id": user_from.id if user_from else False,:
                "custody_to_id": user_to.id if user_to else False,:
                "state": "confirmed",


            custody_record = self.create(vals)
            custody_record.verify_custody_integrity()

            return custody_record

