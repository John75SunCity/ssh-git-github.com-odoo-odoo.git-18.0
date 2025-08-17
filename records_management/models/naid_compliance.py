from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class NaidCompliance(models.Model):
    _name = 'naid.compliance'
    _description = 'NAID Compliance Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'certification_date desc, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    code = fields.Char()
    description = fields.Text()
    sequence = fields.Integer()
    active = fields.Boolean()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    compliance_officer_id = fields.Many2one()
    state = fields.Selection()
    naid_level = fields.Selection()
    certification_number = fields.Char()
    certification_date = fields.Date()
    expiration_date = fields.Date()
    renewal_date = fields.Date()
    audit_frequency = fields.Selection()
    last_audit_date = fields.Date()
    next_audit_date = fields.Date()
    audit_due_days = fields.Integer()
    overall_score = fields.Float()
    security_score = fields.Float()
    process_score = fields.Float()
    documentation_score = fields.Float()
    personnel_score = fields.Float()
    equipment_score = fields.Float()
    audit_findings = fields.Text()
    corrective_actions = fields.Text()
    remediation_plan = fields.Text()
    risk_assessment = fields.Text()
    findings_count = fields.Integer()
    security_level = fields.Selection()
    facility_requirements = fields.Text()
    access_control_verified = fields.Boolean()
    surveillance_system_verified = fields.Boolean()
    currency_id = fields.Many2one()
    insurance_coverage = fields.Monetary()
    liability_limit = fields.Monetary()
    bonding_amount = fields.Monetary()
    insurance_verified = fields.Boolean()
    personnel_screening_required = fields.Boolean()
    training_completed = fields.Boolean()
    certification_training_current = fields.Boolean()
    documentation_standard = fields.Selection()
    chain_of_custody_required = fields.Boolean()
    destruction_certificate_required = fields.Boolean()
    witness_required = fields.Boolean()
    regulatory_requirements = fields.Text()
    legal_compliance_verified = fields.Boolean()
    sox_compliance = fields.Boolean()
    hipaa_compliance = fields.Boolean()
    gdpr_compliance = fields.Boolean()
    destruction_volume_ytd = fields.Float()
    customer_satisfaction_score = fields.Float()
    processing_time_avg = fields.Float()
    compliance_incidents = fields.Integer()
    is_expired = fields.Boolean()
    days_until_expiration = fields.Integer()
    compliance_status_color = fields.Integer()
    audit_status_display = fields.Char()
    certificate_ids = fields.One2many()
    audit_log_ids = fields.One2many()
    checklist_ids = fields.One2many()
    destruction_record_ids = fields.One2many()
    chain_custody_ids = fields.One2many()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    action_compliance_report = fields.Char(string='Action Compliance Report')
    action_conduct_audit = fields.Char(string='Action Conduct Audit')
    action_download_certificate = fields.Char(string='Action Download Certificate')
    action_generate_certificate = fields.Char(string='Action Generate Certificate')
    action_renew_certificate = fields.Char(string='Action Renew Certificate')
    action_schedule_audit = fields.Char(string='Action Schedule Audit')
    action_view_audit_details = fields.Char(string='Action View Audit Details')
    action_view_audit_history = fields.Char(string='Action View Audit History')
    action_view_certificates = fields.Char(string='Action View Certificates')
    action_view_destruction_records = fields.Char(string='Action View Destruction Records')
    audit_count = fields.Integer(string='Audit Count')
    audit_date = fields.Date(string='Audit Date')
    audit_history_ids = fields.One2many('naid.audit.log')
    audit_reminder = fields.Char(string='Audit Reminder')
    audit_required = fields.Boolean(string='Audit Required')
    audit_result = fields.Char(string='Audit Result')
    audit_scope = fields.Char(string='Audit Scope')
    audit_type = fields.Selection(string='Audit Type')
    auditor_name = fields.Char(string='Auditor Name')
    audits = fields.Char(string='Audits')
    auto_renewal = fields.Char(string='Auto Renewal')
    background_checks = fields.Char(string='Background Checks')
    benchmark = fields.Char(string='Benchmark')
    button_box = fields.Char(string='Button Box')
    card = fields.Char(string='Card')
    certificate_count = fields.Integer(string='Certificate Count')
    certificate_issued = fields.Char(string='Certificate Issued')
    certificate_number = fields.Char(string='Certificate Number')
    certificate_status = fields.Selection(string='Certificate Status')
    certificate_tracking = fields.Char(string='Certificate Tracking')
    certificate_type = fields.Selection(string='Certificate Type')
    certificate_valid = fields.Char(string='Certificate Valid')
    certificates = fields.Char(string='Certificates')
    certified = fields.Char(string='Certified')
    chain_of_custody = fields.Char(string='Chain Of Custody')
    checklist = fields.Char(string='Checklist')
    client_name = fields.Char(string='Client Name')
    compliance_alerts = fields.Char(string='Compliance Alerts')
    compliance_checklist_ids = fields.One2many('compliance.checklist')
    compliance_officer = fields.Char(string='Compliance Officer')
    compliance_score = fields.Char(string='Compliance Score')
    compliance_status = fields.Selection(string='Compliance Status')
    compliance_trend = fields.Char(string='Compliance Trend')
    compliance_verified = fields.Boolean(string='Compliance Verified')
    context = fields.Char(string='Context')
    days_since_last_audit = fields.Char(string='Days Since Last Audit')
    days_until_expiry = fields.Char(string='Days Until Expiry')
    destruction_count = fields.Integer(string='Destruction Count')
    destruction_date = fields.Date(string='Destruction Date')
    destruction_method = fields.Char(string='Destruction Method')
    destruction_verification = fields.Char(string='Destruction Verification')
    destructions = fields.Char(string='Destructions')
    equipment_certification = fields.Char(string='Equipment Certification')
    escalation_contacts = fields.Char(string='Escalation Contacts')
    expired = fields.Char(string='Expired')
    expiring_soon = fields.Char(string='Expiring Soon')
    expiry_date = fields.Date(string='Expiry Date')
    expiry_notification = fields.Char(string='Expiry Notification')
    facility_manager = fields.Char(string='Facility Manager')
    facility_name = fields.Char(string='Facility Name')
    group_by_expiry = fields.Char(string='Group By Expiry')
    group_by_facility = fields.Char(string='Group By Facility')
    group_by_naid_level = fields.Char(string='Group By Naid Level')
    group_by_officer = fields.Char(string='Group By Officer')
    group_by_status = fields.Selection(string='Group By Status')
    help = fields.Char(string='Help')
    incident_management = fields.Char(string='Incident Management')
    information_handling = fields.Char(string='Information Handling')
    issue_date = fields.Date(string='Issue Date')
    issuing_authority = fields.Char(string='Issuing Authority')
    last_verified = fields.Boolean(string='Last Verified')
    management_alerts = fields.Char(string='Management Alerts')
    material_type = fields.Selection(string='Material Type')
    measurement_date = fields.Date(string='Measurement Date')
    metric_type = fields.Selection(string='Metric Type')
    metrics = fields.Char(string='Metrics')
    naid_a = fields.Char(string='Naid A')
    naid_aa = fields.Char(string='Naid Aa')
    naid_member_id = fields.Many2one('naid.member')
    non_compliant = fields.Char(string='Non Compliant')
    notes = fields.Char(string='Notes')
    notification_recipients = fields.Char(string='Notification Recipients')
    notifications = fields.Char(string='Notifications')
    operational_score = fields.Char(string='Operational Score')
    overall_compliance_score = fields.Char(string='Overall Compliance Score')
    overdue_audit = fields.Char(string='Overdue Audit')
    pending_audit = fields.Char(string='Pending Audit')
    performance_history_ids = fields.One2many('performance.history')
    personnel_screening = fields.Char(string='Personnel Screening')
    physical_security_score = fields.Char(string='Physical Security Score')
    process_verification = fields.Char(string='Process Verification')
    quality_control = fields.Char(string='Quality Control')
    regulatory_notifications = fields.Char(string='Regulatory Notifications')
    renewal_reminder = fields.Char(string='Renewal Reminder')
    requirement_name = fields.Char(string='Requirement Name')
    requirement_type = fields.Selection(string='Requirement Type')
    res_model = fields.Char(string='Res Model')
    responsible_person = fields.Char(string='Responsible Person')
    risk_level = fields.Char(string='Risk Level')
    score = fields.Char(string='Score')
    search_view_id = fields.Many2one('search.view')
    secure_storage = fields.Char(string='Secure Storage')
    security_clearance = fields.Char(string='Security Clearance')
    security_officer = fields.Char(string='Security Officer')
    standards = fields.Char(string='Standards')
    surveillance_system = fields.Char(string='Surveillance System')
    third_party_auditor = fields.Char(string='Third Party Auditor')
    trend = fields.Char(string='Trend')
    valid_certs = fields.Char(string='Valid Certs')
    variance = fields.Char(string='Variance')
    verification_method = fields.Char(string='Verification Method')
    view_mode = fields.Char(string='View Mode')
    witness_present = fields.Char(string='Witness Present')
    today = fields.Date()
    today = fields.Date()
    next_audit = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def relativedelta(months=0):
            return timedelta(days=months * 30)


    def _compute_audit_count(self):
            for record in self:
                record.audit_count = len(record.audit_ids)


    def _compute_certificate_count(self):
            for record in self:
                record.certificate_count = len(record.certificate_ids)


    def _compute_destruction_count(self):
            for record in self:
                record.destruction_count = len(record.destruction_ids)

        # ============================================================================
            # COMPUTE METHODS
        # ============================================================================


    def _compute_expiration_status(self):
            """Compute expiration status and days until expiration"""

    def _compute_audit_timing(self):
            """Compute days until next audit is due"""

    def _compute_compliance_scores(self):
            """Compute overall compliance score from individual category scores."""
            Includes all scores that are not None, including zero, as zero may be a valid assessment.

            for record in self:
                scores = []
                    record.security_score,
                    record.process_score,
                    record.documentation_score,
                    record.personnel_score,
                    record.equipment_score,

                # Include all scores that are not None (including zero)
                valid_scores = [score for score in scores if score is not None]:
                if valid_scores:
                    record.overall_score = sum(valid_scores) / len(valid_scores)
                else:
                    record.overall_score = 0.0


    def _compute_findings_metrics(self):
            """Compute count of open findings from audit logs"""
            for record in self:
                open_findings = record.audit_log_ids.filtered()
                    lambda log: log.state in ["open", "in_progress"]

                record.findings_count = len(open_findings)


    def _compute_status_indicators(self):
            """Compute status display indicators and colors"""
            for record in self:
                # Color coding: 1=red, 2=orange, 3=yellow, 10=green, 4=blue
                if record.is_expired or record.state == "expired":
                    record.compliance_status_color = 1  # Red
                    record.audit_status_display = "Expired - Renewal Required"
                elif record.state == "non_compliant":
                    record.compliance_status_color = 1  # Red
                    record.audit_status_display = "Non-Compliant - Action Required"
                elif record.state == "under_review":
                    record.compliance_status_color = 2  # Orange
                    record.audit_status_display = "Under Review"
                elif record.state == "compliant":
                    if record.overall_score >= 95:
                        record.compliance_status_color = 10  # Green
                        record.audit_status_display = "Excellent Compliance"
                    elif record.overall_score >= 85:
                        record.compliance_status_color = 3  # Yellow
                        record.audit_status_display = "Good Compliance"
                    else:
                        record.compliance_status_color = 2  # Orange
                        record.audit_status_display = "Marginal Compliance"
                else:
                    record.compliance_status_color = 4  # Blue
                    record.audit_status_display = "Pending Review"

        # ============================================================================
            # ACTION METHODS
        # ============================================================================


    def action_complete_audit(self):
            """Complete audit process and update compliance status"""

            self.ensure_one()

            if not self.audit_findings:
                raise UserError()
                    _("Please enter audit findings before completing the audit.")


            # Determine new state based on overall score
            if self.overall_score >= 80:
                new_state = "compliant"
                message = _("Audit completed successfully. Compliance status: COMPLIANT")
            else:
                new_state = "non_compliant"
                message = _()
                    "Audit completed. Compliance status: NON-COMPLIANT. Corrective action required."


            # Calculate next audit date based on frequency
            frequency_map = {}
                "monthly": 1,
                "quarterly": 3,
                "semi_annual": 6,
                "annual": 12,
                "on_demand": 6,  # Default to 6 months

            months = frequency_map.get(self.audit_frequency, 6)

    def action_schedule_next_audit(self):
            """Schedule the next compliance audit based on requirements"""

            self.ensure_one()

            if not self.next_audit_date:
                raise UserError()
                    _("Next audit date is not set. Please complete current audit first.")


            return {}
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {}
                    "title": _("Audit Scheduled"),
                    "message": _("Next audit scheduled for %s", self.next_audit_date),:
                    "type": "success",




    def action_generate_certificate(self):
            """Generate NAID compliance certificate for compliant records""":
            self.ensure_one()

            if self.state != "compliant":
                raise UserError()
                    _("Certificates can only be generated for compliant records."):

            if not self.certification_date:
                raise UserError()
                    _("Certification date must be set before generating certificate.")


            return {}
                "type": "ir.actions.act_window",
                "name": _("Generate NAID Certificate"),
                "res_model": "naid.certificate.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {}
                    "default_compliance_id": self.id,
                    "default_certification_level": self.naid_level,
                    "default_certification_date": self.certification_date,
                    "default_expiration_date": self.expiration_date,



        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================


    def _check_certification_dates(self):
            """Validate certification date logic"""
            for record in self:
                if record.certification_date and record.expiration_date:
                    if record.certification_date >= record.expiration_date:
                        raise ValidationError()
                            _("Certification date must be before expiration date.")



    def _check_score_ranges(self):
            """Ensure all scores are within valid percentage ranges"""
            for record in self:
                score_fields = {}
                    "Overall Score": record.overall_score,
                    "Security Score": record.security_score,
                    "Process Score": record.process_score,
                    "Documentation Score": record.documentation_score,
                    "Personnel Score": record.personnel_score,
                    "Equipment Score": record.equipment_score,

                for field_name, score in score_fields.items(:
                    if score is not None and (score < 0 or score > 100):
                        raise ValidationError()
                            _("%s must be between 0 and 100 percent.", field_name)



    def _check_monetary_amounts(self):
            """Ensure monetary amounts are positive"""
            for record in self:
                if record.insurance_coverage and record.insurance_coverage < 0:
                    raise ValidationError()
                        _("Insurance coverage must be a positive amount.")

                if record.liability_limit and record.liability_limit < 0:
                    raise ValidationError(_("Liability limit must be a positive amount."))
                if record.bonding_amount and record.bonding_amount < 0:
                    raise ValidationError(_("Bonding amount must be a positive amount."))

        # ============================================================================
            # LIFECYCLE METHODS
        # ============================================================================


    def create(self, vals_list):
            """Override create to generate sequence and set defaults"""
            for vals in vals_list:
                if not vals.get("name") or vals["name"] == _("New"):
                    vals["name"] = self.env["ir.sequence"].next_by_code()
                        "naid.compliance"
                    ) or _("New"

                # Set default next audit date based on frequency
                if not vals.get("next_audit_date") and vals.get("audit_frequency"):
                    frequency_map = {}
                        "monthly": 1,
                        "quarterly": 3,
                        "semi_annual": 6,
                        "annual": 12,

                    months = frequency_map.get(vals["audit_frequency"], 3)

    def write(self, vals):
            """Override write to track important changes"""
            # Track state changes
            if "state" in vals:
                for record in self:
                    old_state = record.state
                    new_state = vals["state"]
                    if old_state != new_state:
                        old_state_display = dict(record._fields["state"].selection).get()
                            old_state, old_state

                        new_state_display = dict(record._fields["state"].selection).get()
                            new_state, new_state

                        record.message_post()
                            body=_()
                                "Compliance status changed from %s to %s",
                                old_state_display,
                                new_state_display,



            # Track NAID level changes
            if "naid_level" in vals:
                for record in self:
                    if record.naid_level != vals["naid_level"]:
                        old_level_display = dict()
                            record._fields["naid_level"].selection
                        ).get(record.naid_level, record.naid_level
                        new_level_display = dict()
                            record._fields["naid_level"].selection
                        ).get(vals["naid_level"], vals["naid_level"]
                        record.message_post()
                            body=_()
                                "NAID certification level changed from %s to %s",
                                old_level_display,
                                new_level_display,



            # Update renewal date when expiration changes
            if "expiration_date" in vals and vals["expiration_date"]:
                expiration_date = vals["expiration_date"]
                if isinstance(expiration_date, str):
                    expiration_date = datetime.datetime.strptime()
                        expiration_date, "%Y-%m-%d"
                    ).date(
                vals["renewal_date"] = expiration_date - timedelta(days=60)

            return super().write(vals)


    def unlink(self):
            """Override unlink to prevent deletion of active compliance records"""
            for record in self:
                if record.state == "compliant":
                    raise UserError()
                        _("Cannot delete compliant certification records. Archive instead.")

            return super().unlink()

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================


    def _get_audit_requirements(self):
            """Get specific audit requirements based on NAID level"""
            self.ensure_one()

            base_requirements = {}
                "security": []
                    "Physical access controls",
                    "Surveillance systems",
                    "Personnel screening",

                "process": []
                    "Destruction methods",
                    "Chain of custody",
                    "Witness procedures",

                "documentation": []
                    "Policy compliance",
                    "Record keeping",
                    "Reporting procedures",

                "personnel": []
                    "Training records",
                    "Background checks",
                    "Certification status",

                "equipment": []
                    "Equipment certification",
                    "Maintenance records",
                    "Calibration status",



            # Add specific requirements based on NAID level
            if self.naid_level == "aaa":
                base_requirements["security"].extend(["Biometric access", "Armed security"])
                base_requirements["process"].extend(["Dual witness", "Video recording"])
            elif self.naid_level == "aa":
                base_requirements["security"].extend(["Badge access", "Security guard"])
                base_requirements["process"].extend(["Single witness required"])

            return base_requirements


    def _calculate_compliance_risk(self):
            """Calculate compliance risk score based on various factors"""
            self.ensure_one()

            risk_factors = []

            # Expiration risk
            if self.days_until_expiration <= 30:
                risk_factors.append(25)
            elif self.days_until_expiration <= 60:
                risk_factors.append(15)

            # Score-based risk
            if self.overall_score < 70:
                risk_factors.append(30)
            elif self.overall_score < 85:
                risk_factors.append(15)

            # Findings risk
            if self.findings_count > 5:
                risk_factors.append(20)
            elif self.findings_count > 0:
                risk_factors.append(10)

            # Audit overdue risk
            if self.audit_due_days < 0:
                risk_factors.append(25)

            risk_score = sum(risk_factors)

            if risk_score >= 50:
                risk_level = "high"
            elif risk_score >= 25:
                risk_level = "medium"
            else:
                risk_level = "low"

            return risk_score, risk_level

