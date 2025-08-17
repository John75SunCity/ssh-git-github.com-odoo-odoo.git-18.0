from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class RecordsBillingContact(models.Model):
    _name = 'records.billing.contact'
    _description = 'Records Billing Contact'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    sequence = fields.Integer()
    email = fields.Char()
    phone = fields.Char(string='Phone', tracking=True)
    mobile = fields.Char(string='Mobile', tracking=True)
    job_title = fields.Char(string='Job Title')
    department = fields.Char(string='Department')
    billing_profile_id = fields.Many2one()
    customer_billing_profile_id = fields.Many2one()
    partner_id = fields.Many2one()
    billing_service_ids = fields.Many2many()
    receive_storage_invoices = fields.Boolean()
    receive_service_invoices = fields.Boolean()
    receive_statements = fields.Boolean()
    receive_overdue_notices = fields.Boolean()
    receive_promotional = fields.Boolean()
    receive_service_updates = fields.Boolean()
    primary_contact = fields.Boolean()
    backup_contact = fields.Boolean()
    contact_type = fields.Selection()
    preferred_method = fields.Selection()
    secondary_method = fields.Selection()
    email_format = fields.Selection()
    delivery_schedule = fields.Selection()
    invoice_delivery_method = fields.Selection()
    invoice_format = fields.Selection()
    consolidated_invoicing = fields.Boolean()
    email_notifications = fields.Boolean()
    notification_frequency = fields.Selection()
    sms_notifications = fields.Boolean()
    urgent_notifications_only = fields.Boolean()
    language = fields.Selection()
    timezone = fields.Selection()
    notes = fields.Text(string='Notes')
    last_contact_date = fields.Datetime()
    last_invoice_sent = fields.Datetime()
    communication_count = fields.Integer()
    currency_id = fields.Many2one()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    display_name = fields.Char()
    invoice_types = fields.Char()
    contact_priority = fields.Integer()
    service_count = fields.Integer()
    state = fields.Selection()
    service_type = fields.Selection()
    billing_profile = fields.Char(string='Billing Profile')
    button_box = fields.Char(string='Button Box')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    high_priority = fields.Selection(string='High Priority')
    inactive = fields.Boolean(string='Inactive')
    primary = fields.Char(string='Primary')
    receive_service = fields.Char(string='Receive Service')
    receive_storage = fields.Char(string='Receive Storage')
    res_model = fields.Char(string='Res Model')
    toggle_active = fields.Boolean(string='Toggle Active')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute display name with additional details"""
            for record in self:
                name_parts = [record.name]
                if record.job_title:
                    name_parts.append(f"({record.job_title})")
                if record.department:
                    name_parts.append(f"- {record.department}")
                record.display_name = " ".join(name_parts)


    def _compute_invoice_types(self):
            """Compute which invoice types this contact receives"""
            for record in self:
                types = []
                if record.receive_storage_invoices:
                    types.append("Storage")
                if record.receive_service_invoices:
                    types.append("Service")
                if record.receive_statements:
                    types.append("Statements")
                record.invoice_types = ", ".join(types) if types else "None":

    def _compute_contact_priority(self):
            """Compute contact priority for sorting and display""":
            for record in self:
                if record.primary_contact or record.contact_type == "primary":
                    record.contact_priority = 1
                elif record.backup_contact or record.contact_type == "backup":
                    record.contact_priority = 2
                elif record.contact_type == "executive":
                    record.contact_priority = 3
                elif record.contact_type == "financial":
                    record.contact_priority = 4
                else:
                    record.contact_priority = 5


    def _compute_service_count(self):
            """Compute number of associated billing services"""
            for record in self:
                record.service_count = len(record.billing_service_ids)


    def create(self, vals_list):
            """Override create to handle primary contact logic"""
            for vals in vals_list:
                # If creating primary contact, ensure only one primary per profile
                if vals.get("primary_contact") and vals.get("billing_profile_id"):
                    self._ensure_single_primary(vals["billing_profile_id"])

            return super().create(vals_list)


    def write(self, vals):
            """Override write to handle primary contact changes"""
            if "primary_contact" in vals and vals["primary_contact"]:
                for record in self:
                    self._ensure_single_primary(record.billing_profile_id.id, record.id)  # pylint: disable=no-member

            return super().write(vals)


    def _ensure_single_primary(self, billing_profile_id, exclude_id=None):
            """Ensure only one primary contact per billing profile"""
            domain = []
                ("billing_profile_id", "=", billing_profile_id),
                ("primary_contact", "=", True),

            if exclude_id:
                domain.append(("id", "!=", exclude_id))

            existing_primary = self.search(domain)
            if existing_primary:
                # pylint: disable=no-member
                existing_primary.write({"primary_contact": False})


    def _get_languages(self):
            """Get available languages"""
            return self.env["res.lang"].get_installed()


    def _get_timezones(self):
            """Get available timezones"""
            return [(tz, tz) for tz in pytz.all_timezones]:

    def send_test_communication(self):
            """Send test communication to verify contact information"""
            self.ensure_one()

            if not self.email and self.preferred_method == "email":
                raise ValidationError()
                    _("No email address specified for email communication."):


            # Update activity tracking
            # pylint: disable=no-member
            self.write()
                {}
                    "last_contact_date": fields.Datetime.now(),
                    "communication_count": self.communication_count + 1,



            # Log the test communication
            self.message_post()
                body=_()
                    "Test communication sent to %s via %s",
                    self.name,
                    dict(self._fields["preferred_method"].selection)[self.preferred_method],



            return True


    def update_invoice_delivery_tracking(self):
            """Update tracking when invoice is delivered to this contact"""
            self.ensure_one()

            # pylint: disable=no-member
            self.write()
                {}
                    "last_invoice_sent": fields.Datetime.now(),
                    "communication_count": self.communication_count + 1,



        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_set_primary(self):
            """Set this contact as primary"""
            self.ensure_one()

            # Remove primary flag from other contacts in same profile
            # pylint: disable=no-member
            other_contacts = self.search()
                []
                    ("billing_profile_id", "=", self.billing_profile_id.id),
                    ("id", "!=", self.id),



            # pylint: disable=no-member
            other_contacts.write({"primary_contact": False})

            # Set this contact as primary
            # pylint: disable=no-member
            self.write()
                {}
                    "primary_contact": True,
                    "contact_type": "primary",



            self.message_post(body=_("Contact set as primary billing contact"))

            return {}
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {}
                    "title": _("Primary Contact Updated"),
                    "message": _("%s is now the primary billing contact.", self.name),
                    "type": "success",




    def action_test_email(self):
            """Send test email to verify contact information"""
            self.ensure_one()

            if not self.email:
                raise ValidationError(_("No email address specified for this contact.")):
            # Send test communication
            self.send_test_communication()

            return {}
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {}
                    "title": _("Test Email Sent"),
                    "message": _("Test email sent to %s", self.email),
                    "type": "success",




    def action_view_communications(self):
            """View all communications sent to this contact"""
            self.ensure_one()

            return {}
                "type": "ir.actions.act_window",
                "name": _("Communications: %s", self.name),
                "res_model": "mail.message",
                "view_mode": "tree,form",
                "domain": []
                    ("model", "=", self._name),
                    ("res_id", "=", self.id),

                "context": {"default_model": self._name, "default_res_id": self.id},



    def action_view_billing_services(self):
            """View associated billing services"""
            self.ensure_one()

            return {}
                "type": "ir.actions.act_window",
                "name": _("Billing Services: %s", self.name),
                "res_model": "records.billing.service",
                "view_mode": "tree,form",
                "domain": [("id", "in", self.billing_service_ids.ids)],  # pylint: disable=no-member
                "context": {}
                    "default_contact_id": self.id,
                    "search_default_group_by_service_type": 1,




    def action_update_preferences(self):
            """Open wizard to update communication preferences"""
            self.ensure_one()

            return {}
                "type": "ir.actions.act_window",
                "name": _("Update Communication Preferences"),
                "res_model": "records.billing.contact",
                "res_id": self.id,
                "view_mode": "form",
                "target": "new",
                "context": {}
                    "default_id": self.id,
                    "focus_preferences": True,




    def action_deactivate_contact(self):
            """Deactivate billing contact"""
            self.ensure_one()

            # If this is a primary contact, promote backup contact
            if self.primary_contact:
                # pylint: disable=no-member
                backup_contacts = self.search()
                    []
                        ("billing_profile_id", "=", self.billing_profile_id.id),
                        ("backup_contact", "=", True),
                        ("active", "=", True),
                        ("id", "!=", self.id),

                    limit=1,


                if backup_contacts:
                    # pylint: disable=no-member
                    backup_contacts.write()
                        {}
                            "primary_contact": True,
                            "backup_contact": False,
                            "contact_type": "primary",



                    self.message_post()
                        body=_("Primary contact role transferred to %s", backup_contacts[0].name)


            # pylint: disable=no-member
            self.write({"active": False})

            return {}
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {}
                    "title": _("Contact Deactivated"),
                    "message": _("Billing contact has been deactivated"),
                    "type": "warning",



        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_primary_contact_unique(self):
            """Ensure only one primary contact per billing profile"""
            for record in self:
                if record.primary_contact:
                    # pylint: disable=no-member
                    existing = self.search()
                        []
                            ("billing_profile_id", "=", record.billing_profile_id.id),
                            ("primary_contact", "=", True),
                            ("id", "!=", record.id),  # pylint: disable=no-member



                    if existing:
                        raise ValidationError()
                            _()
                                "Only one primary contact is allowed per billing profile. "
                                "Please uncheck the primary contact flag for %s first.",:
                                existing[0].name,




    def _check_email_format(self):
            """Validate email format using regex pattern"""
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            for record in self:
                if record.email:
                    if not re.match(email_pattern, record.email):
                        raise ValidationError(_("Invalid email format: %s", record.email))


    def _check_communication_method(self):
            """Validate communication method requirements"""
            for record in self:
                if record.preferred_method == "email" and not record.email:
                    raise ValidationError()
                        _()
                            "Email address is required when email is the preferred communication method"



                if record.preferred_method == "phone" and not (:)
                    record.phone or record.mobile

                    raise ValidationError()
                        _()
                            "Phone number is required when phone is the preferred communication method"



        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def name_get(self):
            """Custom name display"""
            result = []
            for record in self:
                name_parts = [record.name]

                if record.primary_contact:
                    name_parts.append("(Primary)")
                elif record.backup_contact:
                    name_parts.append("(Backup)")

                if record.job_title:
                    name_parts.append(f"- {record.job_title}")

                result.append((record.id, " ".join(name_parts)))  # pylint: disable=no-member

            return result


    def _search_name():
            self, name, args=None, operator="ilike", limit=100, name_get_uid=None

            """Enhanced search by name, email, or job title"""
            args = args or []
            domain = []
            if name:
                domain = []
                    "|",
                    "|",
                    "|",
                    ("name", operator, name),
                    ("email", operator, name),
                    ("job_title", operator, name),
                    ("department", operator, name),

            return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


    def get_primary_contact(self, billing_profile_id):
            """Get primary contact for billing profile""":
            # pylint: disable=no-member
            return self.search()
                []
                    ("billing_profile_id", "=", billing_profile_id),
                    ("primary_contact", "=", True),
                    ("active", "=", True),

                limit=1,



    def get_contacts_for_invoice_type(self, billing_profile_id, invoice_type="storage"):
            """Get contacts that should receive specific invoice type"""
            domain = []
                ("billing_profile_id", "=", billing_profile_id),
                ("active", "=", True),


            if invoice_type == "storage":
                domain.append(("receive_storage_invoices", "=", True))
            elif invoice_type == "service":
                domain.append(("receive_service_invoices", "=", True))
            elif invoice_type == "statement":
                domain.append(("receive_statements", "=", True))
            elif invoice_type == "overdue":
                domain.append(("receive_overdue_notices", "=", True))

            return self.search(domain, order="contact_priority, sequence, name")


    def get_contacts_for_service(self, service_id):
            """Get contacts associated with specific billing service"""
            # pylint: disable=no-member
            return self.search()
                []
                    ("billing_service_ids", "in", [service_id]),
                    ("active", "=", True),

                order="contact_priority, sequence, name")))))))))))))))))))))))))

