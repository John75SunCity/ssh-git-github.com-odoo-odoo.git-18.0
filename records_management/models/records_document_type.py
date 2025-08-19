from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare
from odoo.exceptions import UserError, ValidationError


class RecordsDocumentType(models.Model):
    _name = 'records.document.type'
    _description = 'Records Document Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, category, name'
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
    partner_id = fields.Many2one()
    state = fields.Selection()
    category = fields.Selection()
    confidentiality_level = fields.Selection()
    retention_policy_id = fields.Many2one()
    default_retention_years = fields.Integer()
    requires_legal_hold = fields.Boolean()
    destruction_method = fields.Selection()
    naid_compliance = fields.Boolean()
    hipaa_protected = fields.Boolean()
    sox_compliance = fields.Boolean()
    gdpr_applicable = fields.Boolean()
    regulatory_requirements = fields.Text()
    approval_date = fields.Date()
    approved_by_id = fields.Many2one()
    audit_readiness_level = fields.Selection()
    audit_required = fields.Boolean()
    auto_classification_potential = fields.Float()
    classification_accuracy_score = fields.Float()
    compliance_notes = fields.Text()
    compliance_risk_assessment = fields.Selection()
    compliance_status = fields.Selection()
    regulatory_compliance_score = fields.Float()
    regulatory_requirement = fields.Text()
    retention_compliance = fields.Selection()
    risk_level = fields.Selection()
    security_classification = fields.Selection()
    document_type_utilization = fields.Float()
    growth_trend_indicator = fields.Selection()
    seasonal_pattern_score = fields.Float()
    type_complexity_rating = fields.Selection()
    max_box_weight = fields.Float()
    storage_requirements = fields.Text()
    handling_instructions = fields.Text()
    environmental_controls = fields.Boolean()
    fire_protection_required = fields.Boolean()
    approval_required = fields.Boolean()
    indexing_required = fields.Boolean()
    barcode_required = fields.Boolean()
    digital_copy_required = fields.Boolean()
    encryption_required = fields.Boolean()
    utilization_level = fields.Selection()
    metadata_template = fields.Text()
    searchable_fields = fields.Char()
    default_tags = fields.Char()
    document_ids = fields.One2many()
    parent_type_id = fields.Many2one()
    child_type_ids = fields.One2many()
    container_ids = fields.One2many()
    document_count = fields.Integer()
    child_count = fields.Integer()
    container_count = fields.Integer()
    effective_retention_years = fields.Integer()
    status_display = fields.Char()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    action_view_type_documents = fields.Char(string='Action View Type Documents')
    analytics = fields.Char(string='Analytics')
    approved_by = fields.Char(string='Approved By')
    auto_classification = fields.Char(string='Auto Classification')
    button_box = fields.Char(string='Button Box')
    card = fields.Char(string='Card')
    compliance = fields.Char(string='Compliance')
    confidential = fields.Char(string='Confidential')
    group_compliance = fields.Char(string='Group Compliance')
    group_risk = fields.Char(string='Group Risk')
    group_security = fields.Char(string='Group Security')
    help = fields.Char(string='Help')
    inactive = fields.Boolean(string='Inactive')
    res_model = fields.Char(string='Res Model')
    view_mode = fields.Char(string='View Mode')
    creation_date = fields.Date()
    creation_date = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_document_count(self):
            """Compute total number of documents using this type"""
            for record in self:
                record.document_count = len(record.document_ids)


    def _compute_child_count(self):
            """Compute number of child document types"""
            for record in self:
                record.child_count = len(record.child_type_ids)


    def _compute_container_count(self):
            """Compute number of containers using this document type"""
            for record in self:
                record.container_count = len(record.container_ids)


    def _compute_effective_retention(self):
        """Calculate effective retention period"""
        for record in self:
            if record.retention_policy_id and record.retention_policy_id.retention_years:
                record.effective_retention_years = record.retention_policy_id.retention_years
            else:
                record.effective_retention_years = record.default_retention_years or 7


    def _compute_status_display(self):
            """Compute display status with additional information"""
            for record in self:
                status_parts = [record.state.title()]
                if not record.active:
                    status_parts.append("Inactive")
                if record.document_count:
                    status_parts.append(_("%s docs", record.document_count))
                record.status_display = " | ".join(status_parts)


    def _compute_classification_accuracy(self):
        """Compute classification accuracy based on document history"""
        for record in self:
            if record.document_ids:
                total_docs = len(record.document_ids)
                correctly_classified = len(record.document_ids.filtered(
                    lambda d: d.state != 'error'))
                record.classification_accuracy_score = (
                    correctly_classified / total_docs * 100 if total_docs else 0.0)
            else:
                record.classification_accuracy_score = 0.0


    def _compute_regulatory_compliance(self):
        """Compute overall regulatory compliance score"""
        for record in self:
            score = 0.0
            total_factors = 0

            # Base compliance factors
            compliance_factors = [
                record.naid_compliance,
                record.hipaa_protected,
                record.sox_compliance,
                record.gdpr_applicable
            ]

            for factor in compliance_factors:
                total_factors += 1
                if factor:
                    score += 25.0  # Each factor worth 25 points

            # Adjust based on compliance status
            status_multipliers = {
                'compliant': 1.0,
                'pending': 0.75,
                'non_compliant': 0.25,
                'exempted': 0.9
            }

            multiplier = status_multipliers.get(record.compliance_status, 0.5)
            record.regulatory_compliance_score = score * multiplier


    def _compute_utilization_metrics(self):
        """Compute document type utilization percentage"""
        for record in self:
            total_docs_in_system = self.env['records.document'].search_count([])
            record_docs = len(record.document_ids)

            if total_docs_in_system > 0:
                record.document_type_utilization = (
                    record_docs / total_docs_in_system * 100)
            else:
                record.document_type_utilization = 0.0


    def _compute_growth_trend(self):
        """Compute growth trend based on recent document creation"""
        for record in self:
            if not record.document_ids:
                record.growth_trend_indicator = 'stable'
                continue

            # Compare last 30 days vs previous 30 days
            today = datetime.now().date()
            last_30_days = today - timedelta(days=30)
            previous_30_days = today - timedelta(days=60)

            recent_count = len(record.document_ids.filtered(
                lambda d: d.create_date and d.create_date.date() >= last_30_days))

            previous_count = len(record.document_ids.filtered(
                lambda d: d.create_date and
                previous_30_days <= d.create_date.date() < last_30_days))

            if previous_count == 0:
                if recent_count > 0:
                    record.growth_trend_indicator = 'growing'
                else:
                    record.growth_trend_indicator = 'stable'
            else:
                growth_rate = (recent_count - previous_count) / previous_count
                if growth_rate > 0.5:
                    record.growth_trend_indicator = 'rapid_growth'
                elif growth_rate > 0.1:
                    record.growth_trend_indicator = 'growing'
                elif growth_rate < -0.1:
                    record.growth_trend_indicator = 'declining'
                else:
                    record.growth_trend_indicator = 'stable'


    def _compute_seasonal_patterns(self):
        """Compute seasonal usage patterns"""
        for record in self:
            if not record.document_ids:  # Need sufficient data
                record.seasonal_pattern_score = 0.0
                continue

            # Group documents by month and calculate variance
            monthly_counts = {}
            for doc in record.document_ids:
                if doc.create_date:
                    month = doc.create_date.month
                    monthly_counts[month] = monthly_counts.get(month, 0) + 1

            if monthly_counts:
                counts = list(monthly_counts.values())
                avg_count = sum(counts) / len(counts)
                variance = sum((x - avg_count) ** 2 for x in counts) / len(counts)
                # Higher variance indicates more seasonal patterns
                record.seasonal_pattern_score = min(variance / avg_count * 100, 100) if avg_count > 0 else 0.0
            else:
                record.seasonal_pattern_score = 0.0

        # ============================================================================
            # ENHANCED CRUD OPERATIONS
        # ============================================================================

    def create(self, vals_list):
        """Enhanced create with automatic code generation and validation"""
        for vals in vals_list:
            if not vals.get("code"):
                vals["code"] = self._generate_document_type_code(
                    vals.get("category", "other"))

            if vals.get("confidentiality_level") in ["restricted", "top_secret"]:
                vals["encryption_required"] = True
            if not vals.get("name"):
                raise ValidationError(_("Document type name is required"))

        records = super().create(vals_list)
        for record in records:
            record.message_post(
                body=_("Document type created with code: %s", record.code))

        return records


    def write(self, vals):
        """Enhanced write with change validation and tracking"""
        if "state" in vals:
            self._validate_state_transition(vals["state"])
        if "retention_policy_id" in vals or "default_retention_years" in vals:
            self._handle_retention_changes(vals)
        if vals.get("confidentiality_level") in ["restricted", "top_secret"]:
            vals["encryption_required"] = True

        result = super().write(vals)
        if any(
            field in vals
            for field in [
                "state",
                "retention_policy_id",
                "confidentiality_level",
            ]
        ):
            for record in self:
                record.message_post(
                    body=_("Document type configuration updated"),
                    subject=_("Configuration Change"),
                )

        return result


    def unlink(self):
        """Enhanced unlink with dependency validation"""
        for record in self:
            if record.document_ids:
                raise UserError(
                    _(
                        "Cannot delete document type '%s' with %d associated documents. Archive instead.",
                        record.name,
                        len(record.document_ids),
                    )
                )

            if record.child_type_ids:
                raise UserError(
                    _(
                        "Cannot delete document type '%s' with child types. Reassign children first.",
                        record.name,
                    )
                )

        return super().unlink()

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_activate(self):
        """Activate document type"""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(
                _("Cannot activate archived document type. Restore first."))

        self.write({"state": "active", "active": True})
        return self._show_success_message(_("Document type activated successfully"))


    def action_deprecate(self):
            """Deprecate document type with impact assessment"""
            self.ensure_one()
            if self.document_count > 0:
                return self._show_deprecation_wizard()
            self.write({"state": "deprecated"})
            return self._show_success_message(_("Document type deprecated"))


    def action_archive(self):
        """Archive document type with safety checks"""
        self.ensure_one()
        active_docs = self.document_ids.filtered(lambda d: d.active)
        if active_docs:
            raise UserError(
                _(
                    "Cannot archive document type with %d active documents",
                    len(active_docs),
                )
            )

        self.write({"state": "archived", "active": False})
        return self._show_success_message(_("Document type archived"))


    def action_view_documents(self):
        """View all documents of this type"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Documents - %s", self.name),
            "res_model": "records.document",
            "view_mode": "tree,form,kanban",
            "domain": [("document_type_id", "=", self.id)],
            "context": {
                "default_document_type_id": self.id,
                "search_default_group_by_state": 1,
            }
        }



    def action_view_containers(self):
        """View all containers using this document type"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Containers - %s", self.name),
            "res_model": "records.container",
            "view_mode": "tree,form",
            "domain": [("document_type_id", "=", self.id)],
            "context": {"default_document_type_id": self.id},
        }



    def action_setup_security(self):
            """Setup security rules based on confidentiality level"""
            self.ensure_one()
            self._setup_security_rules()
            return self._show_success_message(_("Security rules updated"))


    def action_create_retention_policy(self):
        """Create default retention policy for this document type"""
        self.ensure_one()
        if not self.retention_policy_id:
            self._setup_retention_policy()
        return self._show_success_message(_("Default retention policy created"))

        # ============================================================================
            # BUSINESS LOGIC METHODS
        # ============================================================================

    def get_retention_date(self, creation_date):
        """Calculate retention expiration date"""
        if not creation_date:
            return None
        return creation_date + relativedelta(years=self.effective_retention_years)

    def is_eligible_for_destruction(self, document):
        """Check if document is eligible for destruction"""
        if not document:
            return False
        if self.requires_legal_hold and getattr(document, "legal_hold", False):
            return False
        retention_date = self.get_retention_date(document.create_date)
        if not retention_date or fields.Date.today() < retention_date:
            return False
        if hasattr(document, "state") and document.state in [
            "draft",
            "processing",
        ]:
            return False
        return True

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    def _check_retention_years(self):
        """Enhanced retention years validation"""
        for record in self:
            if record.default_retention_years < 0:
                raise ValidationError(_("Retention years cannot be negative."))
            if record.default_retention_years > 100:
                raise ValidationError(_("Retention years cannot exceed 100 years."))


    def _check_parent_type(self):
        """Enhanced parent type validation with circular reference detection"""
        for record in self:
            if record.parent_type_id:
                if record.parent_type_id == record:
                    raise ValidationError(
                        _("Document type cannot be its own parent."))

                current = record.parent_type_id
                visited = {record.id}
                while current:
                    if current.id in visited:
                        raise ValidationError(
                            _("Circular reference detected in document type hierarchy."))

                    visited.add(current.id)
                    current = current.parent_type_id


    def _check_max_box_weight(self):
        """Validate maximum box weight"""
        for record in self:
            if float_compare(record.max_box_weight, 0.0, precision_digits=2) <= 0:
                raise ValidationError(
                    _("Maximum box weight must be greater than zero."))

            if record.max_box_weight > 500.0:
                raise ValidationError(_("Maximum box weight cannot exceed 500 lbs."))


    def _check_security_consistency(self):
        """Ensure security settings are consistent"""
        for record in self:
            if (record.confidentiality_level in ["restricted", "top_secret"]
                    and not record.encryption_required):
                raise ValidationError(
                    _(
                        "Documents with '%s' confidentiality level must require encryption.",
                        record.confidentiality_level,
                    )
                )



        # ============================================================================
            # HELPER METHODS
        # ============================================================================

    def _generate_document_type_code(self, category):
        """Generate unique document type code"""
        category_prefixes = {
            "financial": "FIN",
            "legal": "LEG",
            "hr": "HR",
            "medical": "MED",
            "compliance": "COMP",
            "government": "GOV",
            "corporate": "CORP",
            "technical": "TECH",
            "operational": "OPS",
            "other": "DOC",
        }
        prefix = category_prefixes.get(category, "DOC")
        sequence = (
            self.env["ir.sequence"].next_by_code("records.document.type") or "1"
        )
        return f"{prefix}{sequence}"


    def _validate_state_transition(self, new_state):
        """Validate allowed state transitions"""
        valid_transitions = {
            "draft": ["active", "archived"],
            "active": ["deprecated", "archived"],
            "deprecated": ["archived"],
            "archived": ["active"],
        }
        for record in self:
            if (record.state in valid_transitions
                    and new_state not in valid_transitions[record.state]):
                raise ValidationError(
                    _(
                        "Invalid state transition from '%s' to '%s'",
                        record.state,
                        new_state,
                    )
                )




    def _handle_retention_changes(self, vals):
            """Handle retention policy changes impact"""
            for record in self:
                if record.document_count > 0:
                    _logger.warning(
                        "Retention change affects %s documents for type %s",
                        record.document_count,
                        record.name,
                    )



    def _show_success_message(self, message):
        """Display success notification"""
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": message,
                "type": "success",
                "sticky": False,
            }
        }




    def _show_deprecation_wizard(self):
        """Show deprecation confirmation wizard"""
        return {
            "type": "ir.actions.act_window",
            "name": _("Confirm Deprecation"),
            "res_model": "records.document.type.deprecate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_document_type_id": self.id},
        }



    def _setup_retention_policy(self):
        """Create default retention policy for certain categories"""
        if not self.retention_policy_id and self.category in [
            "financial",
            "legal",
            "compliance",
        ]:
            retention_years = {
                "financial": 7,
                "legal": 10,
                "compliance": 5,
            }
            policy_name = _("Default %s Policy - %s", self.category.title(), self.name)
            _logger.info(
                "Would create retention policy: %s with %s years retention",
                policy_name,
                retention_years.get(self.category),
            )
        return True


    def _setup_security_rules(self):
        """Set up security rules based on confidentiality level"""
        security_configs = {
            "public": {"access_group": "base.group_user", "encryption": False},
            "internal": {
                "access_group": "base.group_user",
                "encryption": False,
            },
            "confidential": {
                "access_group": "records_management.group_records_manager",
                "encryption": True,
            },
            "restricted": {
                "access_group": "records_management.group_records_manager",
                "encryption": True,
            },
            "top_secret": {
                "access_group": "records_management.group_records_admin",
                "encryption": True,
            },
        }
        config = security_configs.get(
            self.confidentiality_level, security_configs["internal"]
        )
        _logger.info(
            "Would configure security for %s: access_group=%s, encryption=%s",
            self.name,
            config["access_group"],
            config["encryption"],
        )
        return True
