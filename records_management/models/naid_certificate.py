from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class NaidCertificate(models.Model):
    _name = 'naid.certificate'
    _description = 'NAID Destruction Certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'certificate_number desc'
    _rec_name = 'certificate_number'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence')
    state = fields.Selection()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    certificate_type = fields.Selection()
    partner_id = fields.Many2one()
    destruction_service_id = fields.Many2one()
    naid_compliance_id = fields.Many2one()
    date_created = fields.Datetime()
    date_modified = fields.Datetime(string='Modified Date')
    date_issued = fields.Datetime(string='Issue Date')
    date_delivered = fields.Datetime(string='Delivery Date')
    expiration_date = fields.Date(string='Expiration Date')
    certificate_data = fields.Binary(string='Certificate Document')
    certificate_filename = fields.Char(string='Certificate Filename')
    template_id = fields.Many2one()
    is_digitally_signed = fields.Boolean(string='Digitally Signed')
    signature_data = fields.Binary(string='Digital Signature')
    signature_hash = fields.Char(string='Signature Hash')
    signature_date = fields.Datetime(string='Signature Date')
    naid_member_id = fields.Char(string='NAID Member ID')
    compliance_level = fields.Selection()
    delivery_method = fields.Selection()
    delivery_status = fields.Selection()
    active = fields.Boolean(string='Active')
    priority = fields.Selection()
    notes = fields.Text(string='Internal Notes')
    display_name = fields.Char()
    is_expired = fields.Boolean(string='Is Expired')
    days_until_expiration = fields.Integer()
    destruction_record_ids = fields.One2many()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    chain_of_custody_id = fields.Many2one('naid.chain.custody')
    custodian_name = fields.Char(string='Custodian Name')
    witness_name = fields.Char(string='Witness Name')
    environmental_compliance = fields.Boolean(string='Environmental Compliance')
    carbon_neutral_destruction = fields.Boolean(string='Carbon Neutral Destruction')
    recycling_percentage = fields.Float(string='Recycling Percentage')
    action_cancel = fields.Char(string='Action Cancel')
    action_draft = fields.Char(string='Action Draft')
    action_issue = fields.Char(string='Action Issue')
    action_send = fields.Char(string='Action Send')
    action_view_destruction_service = fields.Char(string='Action View Destruction Service')
    button_box = fields.Char(string='Button Box')
    compliance_details = fields.Char(string='Compliance Details')
    context = fields.Char(string='Context')
    destroyed_materials = fields.Char(string='Destroyed Materials')
    domain = fields.Char(string='Domain')
    group_by_issue_date = fields.Date(string='Group By Issue Date')
    group_by_partner = fields.Char(string='Group By Partner')
    group_by_state = fields.Selection(string='Group By State')
    help = fields.Char(string='Help')
    my_certificates = fields.Char(string='My Certificates')
    product_id = fields.Many2one('product')
    res_model = fields.Char(string='Res Model')
    search_view_id = fields.Many2one('search.view')
    state_draft = fields.Char(string='State Draft')
    state_issued = fields.Char(string='State Issued')
    total_weight = fields.Float(string='Total Weight')
    type = fields.Selection(string='Type')
    uom_id = fields.Many2one('uom')
    view_mode = fields.Char(string='View Mode')
    weight = fields.Char(string='Weight')
    today = fields.Date()
    today = fields.Date()
    today = fields.Date()
    certificate_number = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    partner_id = fields.Many2one()
    destruction_date = fields.Datetime()
    issue_date = fields.Datetime()
    naid_compliance_level = fields.Selection()
    destruction_method = fields.Selection()
    destruction_item_ids = fields.One2many()
    shredding_service_id = fields.Many2one()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    total_items = fields.Integer()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_total_weight(self):
            for record in self:
                record.total_weight = sum(record.line_ids.mapped('amount'))

        # ============================================================================
            # COMPUTE METHODS
        # ============================================================================

    def _compute_display_name(self):
            """Compute display name with certificate type and customer"""
            for record in self:
                name = record.name or _("New Certificate")
                if record.certificate_type:
                    type_dict = dict(record._fields["certificate_type").selection]
                    name += _(" - %s", type_dict.get(record.certificate_type))
                if record.partner_id:
                    name += _(" (%s)", record.partner_id.name)
                record.display_name = name


    def _compute_is_expired(self):
            """Check if certificate is expired""":

    def _compute_days_until_expiration(self):
            """Calculate days until expiration"""

    def action_generate_certificate(self):
            """Generate certificate document"""

            self.ensure_one()
            if self.state != "draft":
                raise UserError(_("Only draft certificates can be generated"))

            # Certificate generation logic here
            self.write({"state": "generated", "date_modified": fields.Datetime.now()})
            self.message_post(body=_("Certificate generated"))


    def action_issue_certificate(self):
            """Issue the certificate"""

            self.ensure_one()
            if self.state != "generated":
                raise UserError(_("Only generated certificates can be issued"))

            self.write()
                {}
                    "state": "issued",
                    "date_issued": fields.Datetime.now(),
                    "date_modified": fields.Datetime.now(),


            self.message_post(body=_("Certificate issued"))


    def action_deliver_certificate(self):
            """Mark certificate as delivered"""

            self.ensure_one()
            if self.state != "issued":
                raise UserError(_("Only issued certificates can be delivered"))

            self.write()
                {}
                    "state": "delivered",
                    "date_delivered": fields.Datetime.now(),
                    "delivery_status": "delivered",
                    "date_modified": fields.Datetime.now(),


            self.message_post(body=_("Certificate delivered"))


    def action_archive_certificate(self):
            """Archive the certificate"""

            self.ensure_one()
            self.write()
                {}
                    "state": "archived",
                    "active": False,
                    "date_modified": fields.Datetime.now(),


            self.message_post(body=_("Certificate archived"))


    def action_apply_digital_signature(self):
            """Apply digital signature to certificate"""

            self.ensure_one()
            if not self.certificate_data:
                raise UserError(_("Certificate document must be generated before signing"))

            # Digital signature logic here
            decoded_data = base64.b64decode(self.certificate_data)
            signature_hash = hashlib.sha256(decoded_data).hexdigest()

            self.write()
                {}
                    "is_digitally_signed": True,
                    "signature_hash": signature_hash,
                    "signature_date": fields.Datetime.now(),
                    "date_modified": fields.Datetime.now(),


            self.message_post(body=_("Digital signature applied"))


    def action_validate_signature(self):
            """Validate digital signature integrity"""

            self.ensure_one()
            if not self.is_digitally_signed:
                raise UserError(_("Certificate is not digitally signed"))

            # Signature validation logic here
            decoded_data = base64.b64decode(self.certificate_data)
            current_hash = hashlib.sha256(decoded_data).hexdigest()

            if current_hash != self.signature_hash:
                raise ValidationError()
                    _("Certificate has been tampered with - signature invalid")


            self.message_post(body=_("Digital signature validated successfully"))


    def action_send_certificate(self):
            """Send certificate to customer"""

            self.ensure_one()
            if self.state not in ["issued", "delivered"]:
                raise UserError(_("Only issued certificates can be sent"))

            # Certificate sending logic based on delivery method
            if self.delivery_method == "email":
                self._send_certificate_email()
            elif self.delivery_method == "portal":
                self._make_available_in_portal()

            self.write({"delivery_status": "sent", "date_modified": fields.Datetime.now()})
            self.message_post(body=_("Certificate sent via %s", self.delivery_method))


    def _send_certificate_email(self):
            """Send certificate via email"""
            template = self.env.ref()
                "records_management.email_template_naid_certificate", False

            if template:
                template.send_mail(self.id, force_send=True)


    def _make_available_in_portal(self):
            """Make certificate available in customer portal"""
            # Portal integration logic would be implemented here
            # For now, just log the action
            _logger.info()
                "Certificate %s made available in customer portal for %s",:
                self.name,
                self.partner_id.name,


        # ============================================================================
            # OVERRIDE METHODS
        # ============================================================================

    def create(self, vals_list):
            """Override create to set default values and generate certificate number"""
            for vals in vals_list:
                if not vals.get("name"):
                    vals["name"] = self.env["ir.sequence").next_by_code(]
                        "naid.certificate"
                    ) or _("New Certificate"

                # Set expiration date based on certificate type
                if not vals.get("expiration_date") and vals.get("certificate_type"):
                    expiration_days = self._get_expiration_days(vals["certificate_type"])
                    if expiration_days:
                        expiration_date = datetime.now() + timedelta(days=expiration_days)
                        vals["expiration_date"] = expiration_date.date()

            return super().create(vals_list)


    def write(self, vals):
            """Override write to update modification date for relevant changes""":
            relevant_fields = {}
                "state",
                "certificate_data",
                "is_digitally_signed",
                "signature_data",
                "signature_hash",
                "signature_date",
                "delivery_status",
                "expiration_date",

            if any(field in vals for field in relevant_fields):

    def name_get(self):
            """Custom name display"""
            result = []
            for record in self:
                name = record.name or _("New Certificate")
                if record.certificate_type:
                    type_dict = dict(record._fields["certificate_type"].selection)
                    name += _(" - %s", type_dict.get(record.certificate_type))
                if record.partner_id:
                    name += _(" (%s)", record.partner_id.name)
                result.append((record.id, name))
            return result


    def _get_expiration_days(self, certificate_type):
            """Get expiration days based on certificate type"""
            expiration_map = {}
                "destruction": 2555,  # 7 years
                "compliance": 365,  # 1 year
                "chain_custody": 2555,  # 7 years
                "service_completion": 365,  # 1 year
                "annual_compliance": 365,  # 1 year
                "special_handling": 2555,  # 7 years

            return expiration_map.get(certificate_type, 365)

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_expiration_date(self):
            """Validate expiration date is in the future"""
            for record in self:

    def _check_certificate_uniqueness(self):
            """Validate certificate uniqueness for certain types""":
            for record in self:
                if record.certificate_type in ["annual_compliance", "compliance"]:
                    existing = self.search()
                        []
                            ("certificate_type", "=", record.certificate_type),
                            ("partner_id", "=", record.partner_id.id),
                            ("state", "in", ["issued", "delivered"]),
                            ("expiration_date", ">", fields.Date.today()),
                            ("id", "!=", record.id),


                    if existing:
                        type_name = dict(record._fields["certificate_type").selection).get(]
                            record.certificate_type

                        raise ValidationError()
                            _("An active %s certificate already exists for this customer", type_name):



    def _check_naid_member_id(self):
            """Validate NAID member ID format (alphanumeric and dashes allowed)"""
            for record in self:
                if record.naid_member_id and not re.match(:)
                    r"^[A-Za-z0-9\-]+$", record.naid_member_id

                    raise ValidationError()
                        _()
                            "NAID Member ID must contain only alphanumeric characters and dashes"



        # ============================================================================
            # SCHEDULED ACTIONS
        # ============================================================================

    def _check_certificate_expiration(self):
            """Scheduled action to check for expiring certificates""":

    def _compute_total_items(self):
            """Compute total number of items destroyed"""
            for record in self:
                record.total_items = len(record.destruction_item_ids)


    def create(self, vals_list):
            """Generate certificate number on creation"""
            for vals in vals_list:
                if not vals.get("certificate_number"):
                    vals["certificate_number") = self.env[]
                        "ir.sequence"

            return super().create(vals_list)

