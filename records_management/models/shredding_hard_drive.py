from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class ShreddingHardDrive(models.Model):
    _name = 'shredding.hard_drive'
    _description = 'Hard Drive Destruction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    partner_id = fields.Many2one()
    active = fields.Boolean()
    state = fields.Selection()
    serial_number = fields.Char()
    asset_tag = fields.Char()
    make_model = fields.Char()
    capacity_gb = fields.Float()
    hashed_serial = fields.Char()
    customer_id = fields.Many2one()
    customer_location_notes = fields.Text()
    scanned_at_customer = fields.Boolean()
    scanned_at_customer_by_id = fields.Many2one()
    scanned_at_customer_date = fields.Datetime()
    physical_condition = fields.Selection()
    facility_verification_notes = fields.Text()
    data_classification = fields.Selection()
    encryption_level = fields.Selection()
    destruction_method = fields.Selection()
    destruction_date = fields.Date()
    destruction_witness_required = fields.Boolean()
    destruction_method_verified = fields.Boolean()
    destroyed = fields.Boolean()
    sanitization_standard = fields.Selection()
    physical_destruction_level = fields.Selection()
    nist_compliance_verified = fields.Boolean()
    degaussing_required = fields.Boolean()
    chain_of_custody_verified = fields.Boolean()
    forensic_analysis_completed = fields.Boolean()
    forensic_analysis_notes = fields.Text()
    certificate_number = fields.Char()
    certificate_line_text = fields.Text()
    included_in_certificate = fields.Boolean()
    service_request_id = fields.Many2one()
    approved_by_id = fields.Many2one()
    completed = fields.Boolean()
    weight = fields.Float()
    sequence = fields.Integer()
    created_date = fields.Date()
    updated_date = fields.Date()
    description = fields.Text()
    notes = fields.Text()
    scan_count = fields.Integer(string='Scan Count')
    scan_location = fields.Char(string='Scan Location')
    scan_notes = fields.Text(string='Scan Notes')
    scanned_at_customer_by_id = fields.Many2one()
    scanned_serials = fields.Text(string='Scanned Serials')
    verified_at_facility_by_id = fields.Many2one()
    verified_at_facility_date = fields.Datetime(string='Verified At Facility Date')
    verified_before_destruction = fields.Boolean()
    bulk_serial_input = fields.Text()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    today = fields.Date()
    today = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def name_get(self):
            """Custom name display with serial number and customer"""
            result = []
            for record in self:
                name = record.name
                if record.serial_number:
                    name = _("%s - %s", name, record.serial_number)
                if record.customer_id:
                    name = _("%s (%s)", name, record.customer_id.name)
                result.append((record.id, name))
            return result


    def create(self, vals_list):
            """Override create to generate reference numbers"""
            for vals in vals_list:
                if not vals.get("name"):
                    # Generate reference number
                    sequence = self.env["ir.sequence"].next_by_code("shredding.hard_drive")
                    if not sequence:
                        # Fallback sequence generation

    def write(self, vals):
            """Override write to update timestamp"""

    def action_scan_at_customer(self):
            """Mark as scanned at customer location"""
            self.ensure_one()
            if self.state != "draft":
                raise UserError(_("Can only scan items in draft state"))

            self.write({
                "state": "scanned",
                "scanned_at_customer": True,
                "scanned_at_customer_by_id": self.env.user.id,
                "scanned_at_customer_date": fields.Datetime.now(),
            })
            self.message_post(body=_("Hard drive scanned at customer location"))


    def action_mark_transported(self):
            """Mark as in transit"""
            self.ensure_one()
            if self.state not in ["scanned"]:
                raise UserError(_("Can only transport scanned items"))

            self.write({"state": "transported"})
            self.message_post(body=_("Hard drive marked as in transit"))


    def action_receive_at_facility(self):
            """Mark as received at facility"""
            self.ensure_one()
            if self.state not in ["transported"]:
                raise UserError(_("Can only receive transported items"))

            self.write({
                "state": "received",
                "chain_of_custody_verified": True,
            })
            self.message_post(body=_("Hard drive received at facility"))


    def action_complete_destruction(self):
            """Complete the destruction process"""
            self.ensure_one()
            if self.state not in ["received"]:
                raise UserError(_("Can only destroy items received at facility"))

            if not self.destruction_method:
                raise UserError(_("Destruction method must be specified"))

            self.write({
                "state": "destroyed",
                "destroyed": True,
                "destruction_date": fields.Date.today(),
                "destruction_method_verified": True,
            })

            method_display = dict(self._fields["destruction_method"].selection).get(
                self.destruction_method
            )
            self.message_post(
                body=_("Hard drive destruction completed using %s", method_display)
            )


    def action_generate_certificate(self):
            """Generate destruction certificate"""
            self.ensure_one()
            if self.state not in ["destroyed"]:
                raise UserError(_("Can only generate certificates for destroyed items")):
            # Generate certificate number if not exists:
            if not self.certificate_number:
                sequence = self.env["ir.sequence"].next_by_code("destruction.certificate")
                if not sequence:

    def action_verify_chain_of_custody(self):
            """Verify chain of custody"""
            self.ensure_one()
            self.write({"chain_of_custody_verified": True})
            self.message_post(body=_("Chain of custody verified"))


    def action_complete_forensic_analysis(self):
            """Complete forensic analysis"""
            self.ensure_one()
            self.write({"forensic_analysis_completed": True})
            self.message_post(body=_("Forensic analysis completed"))


    def action_verify_nist_compliance(self):
            """Verify NIST compliance"""
            self.ensure_one()
            self.write({"nist_compliance_verified": True})
            self.message_post(body=_("NIST compliance verified"))


    def action_verify_destruction_method(self):
            """Verify destruction method"""
            self.ensure_one()
            if not self.destruction_method:
                raise UserError(_("Destruction method must be specified first"))

            self.write({"destruction_method_verified": True})
            method_display = dict(self._fields["destruction_method"].selection).get(
                self.destruction_method
            )
            self.message_post(body=_("Destruction method verified: %s", method_display))

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_serial_number_unique(self):
            """Ensure serial numbers are unique per customer"""
            for record in self:
                if record.serial_number and record.customer_id:
                    existing = self.search([
                        ("id", "!=", record.id),
                        ("serial_number", "=", record.serial_number),
                        ("customer_id", "=", record.customer_id.id)
                    ])
                    if existing:
                        raise ValidationError(_(
                            "Serial number %s already exists for customer %s",:
                            record.serial_number,
                            record.customer_id.name
                        ))


    def _check_positive_values(self):
            """Ensure capacity and weight are positive"""
            for record in self:
                if record.capacity_gb and record.capacity_gb < 0:
                    raise ValidationError(_("Capacity cannot be negative"))
                if record.weight and record.weight < 0:
                    raise ValidationError(_("Weight cannot be negative"))


    def _check_destruction_date(self):
            """Validate destruction date"""
            for record in self:
                if record.destruction_date and record.destruction_date > fields.Date.today():
                    raise ValidationError(_("Destruction date cannot be in the future"))

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def get_destruction_summary(self):
            """Get destruction summary for reporting""":
            self.ensure_one()
            return {
                "reference": self.name,
                "serial_number": self.serial_number,
                "customer": self.customer_id.name,
                "destruction_method": dict(
                    self._fields["destruction_method"].selection
                ).get(self.destruction_method),
                "destruction_date": self.destruction_date,
                "certificate_number": self.certificate_number,
                "data_classification": dict(
                    self._fields["data_classification"].selection
                ).get(self.data_classification),
                "compliance_verified": self.nist_compliance_verified,
                "status": dict(self._fields["state"].selection).get(self.state),
            }


    def get_destruction_statistics(self):
            """Get destruction statistics for dashboard""":
            total_count = self.search_count([])
            destroyed_count = self.search_count([("destroyed", "=", True)])
            certified_count = self.search_count([("state", "=", "certified")])

            return {
                "total_drives": total_count,
                "destroyed_drives": destroyed_count,
                "certified_drives": certified_count,
                "pending_destruction": total_count - destroyed_count,
                "completion_rate": (
                    (destroyed_count / total_count * 100) if total_count > 0 else 0:
                ),
            }


    def create_from_service_request(self, service_id, drive_details):
            """Create hard drive records from service request"""
            service = self.env["shredding.service"].browse(service_id)
            if not service.exists():
                raise UserError(_("Service request not found"))

            drive_data = {
                "customer_id": service.customer_id.id,
                "service_request_id": service.id,
                "serial_number": drive_details.get("serial_number"),
                "asset_tag": drive_details.get("asset_tag"),
                "make_model": drive_details.get("make_model"),
                "capacity_gb": drive_details.get("capacity_gb"),
                "data_classification": drive_details.get("data_classification", "internal"),
                "encryption_level": drive_details.get("encryption_level", "none"),
            }
            return self.create(drive_data)

