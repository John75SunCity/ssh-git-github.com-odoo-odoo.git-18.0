from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class NAIDCustodyEvent(models.Model):
    _name = 'naid.custody.event'
    _description = 'NAID Custody Event'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'event_datetime desc, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    event_type = fields.Selection()
    event_datetime = fields.Datetime()
    custody_status = fields.Selection()
    authorized_person_id = fields.Many2one()
    witness_person_id = fields.Many2one()
    naid_member_id = fields.Many2one()
    from_location_id = fields.Many2one()
    to_location_id = fields.Many2one()
    gps_latitude = fields.Float(string='GPS Latitude')
    gps_longitude = fields.Float(string='GPS Longitude')
    container_ids = fields.Many2many()
    document_ids = fields.Many2many()
    hard_drive_id = fields.Many2one()
    lot_id = fields.Many2one()
    digital_signature = fields.Binary(string='Digital Signature')
    signature_verified = fields.Boolean()
    signature_verification_date = fields.Datetime()
    barcode_scanned = fields.Char()
    photo_documentation = fields.Binary(string='Photo Documentation')
    biometric_verified = fields.Boolean()
    biometric_data = fields.Binary(string='Biometric Data')
    naid_compliance_id = fields.Many2one()
    audit_trail_verified = fields.Boolean()
    compliance_score = fields.Float(string='Compliance Score')
    certificate_generated = fields.Boolean()
    certificate_number = fields.Char(string='Certificate Number')
    exception_detected = fields.Boolean()
    exception_type = fields.Selection()
    exception_resolved = fields.Boolean()
    exception_resolution_date = fields.Datetime()
    exception_notes = fields.Text(string='Exception Notes')
    state = fields.Selection()
    description = fields.Text(string='Event Description')
    notes = fields.Text(string='Additional Notes')
    internal_notes = fields.Text(string='Internal Notes')
    priority = fields.Selection()
    previous_event_id = fields.Many2one()
    next_event_ids = fields.One2many()
    container_count = fields.Integer()
    document_count = fields.Integer()
    chain_position = fields.Integer()
    duration_hours = fields.Float()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_item_counts(self):
            """Compute counts of related items"""
            for record in self:
                record.container_count = len(record.container_ids)
                record.document_count = len(record.document_ids)


    def _compute_chain_position(self):
            """Compute position in custody chain"""
            for record in self:
                position = 1
                current = record.previous_event_id
                while current:
                    position += 1
                    current = current.previous_event_id
                record.chain_position = position


    def _compute_duration(self):
            """Compute duration since previous event"""
            for record in self:
                if (:)
                    record.previous_event_id
                    and record.previous_event_id.event_datetime

                    delta = ()
                        record.event_datetime
                        - record.previous_event_id.event_datetime

                    record.duration_hours = delta.total_seconds() / 3600
                else:
                    record.duration_hours = 0.0

        # ============================================================================
            # CONSTRAINT VALIDATION
        # ============================================================================

    def _check_event_chronology(self):
            """Ensure events are in chronological order"""
            for record in self:
                if (:)
                    record.previous_event_id
                    and record.previous_event_id.event_datetime

                    if (:)
                        record.event_datetime
                        <= record.previous_event_id.event_datetime

                        raise ValidationError()
                            _()
                                "Event datetime must be after the previous event in the custody chain"




    def _check_location_requirements(self):
            """Validate location requirements for transfer events""":
            for record in self:
                if record.event_type == "transfer":
                    if not record.from_location_id or not record.to_location_id:
                        raise ValidationError()
                            _()
                                "Transfer events require both source and destination locations"


                    if record.from_location_id == record.to_location_id:
                        raise ValidationError()
                            _()
                                "Source and destination locations must be different for transfers":



        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_verify_signatures(self):
            """Verify digital signatures for the custody event""":
            self.ensure_one()
            if not self.digital_signature:
                raise UserError(_("No digital signature found to verify"))

            # Signature verification logic would go here
            # This would integrate with cryptographic verification systems
            self.write()
                {}
                    "signature_verified": True,
                    "signature_verification_date": fields.Datetime.now(),
                    "state": "verified",



            self.message_post(body=_("Digital signature verified successfully"))


    def action_confirm_custody(self):
            """Confirm custody event"""
            self.ensure_one()

            if self.state != "verified":
                raise UserError(_("Can only confirm verified custody events"))

            self.write({"state": "confirmed"})
            self._create_audit_log("custody_confirmed")

            # Create NAID compliance record if not exists:
            self._ensure_naid_compliance()


    def action_complete_custody(self):
            """Complete custody event"""
            self.ensure_one()

            if self.state not in ["confirmed", "verified"]:
                raise UserError()
                    _("Can only complete confirmed or verified events")


            self.write({"state": "done"})
            self._create_audit_log("custody_completed")

            # Generate certificates if required:
            if self.event_type == "destruction":
                self._generate_destruction_certificate()


    def action_flag_exception(self):
            """Flag custody exception"""
            self.ensure_one()

            self.write({"state": "exception", "exception_detected": True})

            self._create_audit_log("exception_flagged")
            self._notify_compliance_officers()


    def action_resolve_exception(self):
            """Resolve custody exception"""
            self.ensure_one()

            if not self.exception_detected:
                raise UserError(_("No exception detected to resolve"))

            self.write()
                {}
                    "state": "resolved",
                    "exception_resolved": True,
                    "exception_resolution_date": fields.Datetime.now(),



            self._create_audit_log("exception_resolved")

        # ============================================================================
            # BUSINESS LOGIC METHODS
        # ============================================================================

    def _create_audit_log(self, action_type):
            """Create audit log entry for custody event""":
            self.env["naid.audit.log"].create()
                {}
                    "name": _("Custody Event: %s", self.name),
                    "action_type": action_type,
                    "model_name": self._name,
                    "record_id": self.id,
                    "user_id": self.env.user.id,
                    "timestamp": fields.Datetime.now(),
                    "description": _("Custody event %s performed", action_type),
                    "ip_address": self.env.context.get("request_ip", "Unknown"),




    def _ensure_naid_compliance(self):
            """Ensure NAID compliance record exists"""
            if not self.naid_compliance_id:
                compliance = self.env["naid.compliance"].create()
                    {}
                        "name": _("Custody Event Compliance: %s", self.name),
                        "model_name": self._name,
                        "record_id": self.id,
                        "compliance_type": "custody_event",
                        "compliance_status": "compliant",
                        "verification_date": fields.Datetime.now(),


                self.naid_compliance_id = compliance.id


    def _generate_destruction_certificate(self):
            """Generate destruction certificate for destruction events""":
            if self.event_type == "destruction" and not self.certificate_generated:
                # This would integrate with the certificate generation system
                certificate_number = self.env["ir.sequence"].next_by_code()
                    "naid.destruction.certificate"


                self.write()
                    {}
                        "certificate_generated": True,
                        "certificate_number": certificate_number,



                self.message_post()
                    body=_()
                        "Destruction certificate %s generated", certificate_number




    def _notify_compliance_officers(self):
            """Notify compliance officers of exceptions"""
            compliance_group = self.env.ref()
                "records_management.group_compliance_officer",
                raise_if_not_found=False,

            if compliance_group:
                for user in compliance_group.users:
                    self.activity_schedule()
                        "mail.mail_activity_data_warning",
                        user_id=user.id,
                        summary=_("Custody Chain Exception"),
                        note=_()
                            "Exception detected in custody event: %s", self.name



        # ============================================================================
            # INTEGRATION METHODS
        # ============================================================================

    def create_custody_chain(:):
            self, containers=None, documents=None, event_type="pickup"

            """Create custody chain for containers and documents""":
            if not containers and not documents:
                raise UserError()
                    _("Must specify containers or documents for custody chain"):


            vals = {}
                "name": _()
                    "Custody Chain - %s",
                    fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

                "event_type": event_type,
                "event_datetime": fields.Datetime.now(),
                "custody_status": "in_custody",
                "authorized_person_id": self.env.user.id,
                "state": "draft",


            event = self.create(vals)

            if containers:
                event.container_ids = [(6, 0, containers.ids)]
            if documents:
                event.document_ids = [(6, 0, documents.ids)]

            return event


    def get_custody_chain(self, container_id=None, document_id=None):
            """Get complete custody chain for container or document""":
            domain = []

            if container_id:
                domain.append(("container_ids", "in", [container_id]))
            if document_id:
                domain.append(("document_ids", "in", [document_id]))

            if not domain:
                return self.browse()

            events = self.search(domain, order="event_datetime asc")
            return events


